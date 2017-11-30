# Copyright 2016 - Nokia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from sympy.logic.boolalg import Not
from sympy import Symbol

from oslo_log import log
from six.moves import reduce

from vitrage.common.constants import EdgeProperties as EProps
from vitrage.evaluator.actions.base import ActionType
from vitrage.evaluator.condition import convert_to_dnf_format
from vitrage.evaluator.condition import get_condition_common_targets
from vitrage.evaluator.condition import is_condition_include_positive_clause
from vitrage.evaluator.condition import parse_condition
from vitrage.evaluator.condition import SymbolResolver
from vitrage.evaluator.template_fields import TemplateFields
from vitrage.evaluator.template_validation.content. \
    add_causal_relationship_validator import AddCausalRelationshipValidator
from vitrage.evaluator.template_validation.content.base import \
    get_content_correct_result
from vitrage.evaluator.template_validation.content.base import \
    get_content_fault_result
from vitrage.evaluator.template_validation.content.base import \
    validate_template_id
from vitrage.evaluator.template_validation.content.execute_mistral_validator \
    import ExecuteMistralValidator
from vitrage.evaluator.template_validation.content.mark_down_validator \
    import MarkDownValidator
from vitrage.evaluator.template_validation.content.raise_alarm_validator \
    import RaiseAlarmValidator
from vitrage.evaluator.template_validation.content.set_state_validator \
    import SetStateValidator
from vitrage.evaluator.template_validation.status_messages import status_msgs

LOG = log.getLogger(__name__)


class ScenarioValidator(object):

    class TemplateSymbolResolver(SymbolResolver):
        def is_relationship(self, symbol):
            return TemplateFields.RELATIONSHIP_TYPE in symbol

        def get_relationship_source_id(self, relationship):
            return relationship[TemplateFields.SOURCE]

        def get_relationship_target_id(self, relationship):
            return relationship[TemplateFields.TARGET]

        def get_entity_id(self, entity):
            return entity[TemplateFields.TEMPLATE_ID]

    def __init__(self, definitions_index):
        self.definitions_index = definitions_index

    def validate(self, scenarios):
        for scenario in scenarios:
            scenario_values = scenario[TemplateFields.SCENARIO]

            condition = scenario_values[TemplateFields.CONDITION]
            result = self._validate_scenario_condition(condition)

            if not result.is_valid_config:
                return result

            actions = scenario_values[TemplateFields.ACTIONS]
            result = self._validate_scenario_actions(actions)

            if not result.is_valid_config:
                return result

        return get_content_correct_result()

    def _validate_scenario_condition(self, condition):
        try:
            dnf_result = convert_to_dnf_format(condition)
        except Exception:
            LOG.error('%s status code: %s' % (status_msgs[85], 85))
            return get_content_fault_result(85)

        # not condition validation
        not_condition_result = self._validate_not_condition(dnf_result)
        if not not_condition_result.is_valid_config:
            return not_condition_result

        # template id validation
        values_to_replace = ' and ', ' or ', ' not ', 'not ', '(', ')'
        condition_vars = reduce(lambda cond, v: cond.replace(v, ' '),
                                values_to_replace,
                                condition)

        for condition_var in condition_vars.split(' '):

            if len(condition_var.strip()) == 0:
                continue

            result = \
                validate_template_id(self.definitions_index, condition_var)
            if not result.is_valid_config:
                return result

        # condition structure validation
        condition_structure_result = \
            self._validate_condition_structure(parse_condition(condition))
        if not condition_structure_result.is_valid_config:
            return condition_structure_result

        return get_content_correct_result()

    def _validate_condition_structure(self, condition_dnf):
        result = \
            self._validate_condition_includes_positive_clause(condition_dnf)
        if not result.is_valid_config:
            return result

        common_targets = \
            get_condition_common_targets(condition_dnf,
                                         self.definitions_index,
                                         self.TemplateSymbolResolver())

        return get_content_correct_result() if common_targets \
            else get_content_fault_result(135)

    @staticmethod
    def _validate_condition_includes_positive_clause(condition):
        return get_content_correct_result() if \
            is_condition_include_positive_clause(condition) \
            else get_content_fault_result(134)

    def _validate_not_condition(self, dnf_result):
        """Not operator validation

        Not operator can appear only on edges.

        :param dnf_result:
        :param definitions_index:
        :return:
        """

        if isinstance(dnf_result, Not):
            for arg in dnf_result.args:
                if isinstance(arg, Symbol):
                    definition = self.definitions_index.get(str(arg), None)
                    if not (definition and
                            definition.get(EProps.RELATIONSHIP_TYPE)):
                        msg = status_msgs[86] + ' template id: %s' % arg
                        LOG.error('%s status code: %s' % (msg, 86))
                        return get_content_fault_result(86, msg)
                else:
                    res = self._validate_not_condition(arg)
                    if not res.is_valid_config:
                        return res
            return get_content_correct_result()

        for arg in dnf_result.args:
            if not isinstance(arg, Symbol):
                res = self._validate_not_condition(arg)
                if not res.is_valid_config:
                    return res

        return get_content_correct_result()

    def _validate_scenario_actions(self, actions):

        for action in actions:
            result = \
                self._validate_scenario_action(action[TemplateFields.ACTION])
            if not result.is_valid_config:
                return result

        return get_content_correct_result()

    def _validate_scenario_action(self, action):

        action_type = action[TemplateFields.ACTION_TYPE]

        action_validators = {
            ActionType.RAISE_ALARM: RaiseAlarmValidator(),
            ActionType.SET_STATE: SetStateValidator(),
            ActionType.ADD_CAUSAL_RELATIONSHIP:
                AddCausalRelationshipValidator(),
            ActionType.MARK_DOWN: MarkDownValidator(),
            ActionType.EXECUTE_MISTRAL: ExecuteMistralValidator(),
        }

        if action_type not in action_validators:
            LOG.error('%s status code: %s' % (status_msgs[120], 120))
            return get_content_fault_result(120)

        return action_validators[action_type].validate(action,
                                                       self.definitions_index)
