# Copyright 2016 - Nokia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import copy
from oslo_log import log

from vitrage.common import file_utils
from vitrage.evaluator.actions.base import ActionType
from vitrage.evaluator import template_content_validator as validator
from vitrage.evaluator.template_fields import TemplateFields
from vitrage.tests import base
from vitrage.tests.mocks import utils

LOG = log.getLogger(__name__)


class TemplateContentValidatorTest(base.BaseTest):

    # noinspection PyPep8Naming
    @classmethod
    def setUpClass(cls):

        template_dir_path = '%s/templates/general' % utils.get_resources_dir()
        cls.templates = file_utils.load_yaml_files(template_dir_path)
        cls.first_template = cls.templates[0]

    @property
    def clone_template(self):
        return copy.deepcopy(self.first_template)

    def test_content_validation(self):

        for template in self.templates:
            self.assertTrue(validator.content_validation(template))

    def test_validate_scenario_actions(self):

        # Test setup
        ids = ['1', '2', '3']
        actions = self._create_scenario_actions('1', '2')

        # Test action
        is_valid = validator.validate_scenario_actions(actions, ids)

        # Test assertions
        self.assertTrue(is_valid)

    def test_validate_invalid_scenario_actions(self):

        ids = ['1', '2', '3']
        actions = self._create_scenario_actions('1', '2')

        # Validate actions with invalid type
        actions_with_invalid_type = copy.deepcopy(actions)
        first = actions_with_invalid_type[0]
        first[TemplateFields.ACTION][TemplateFields.ACTION_TYPE] = 'unknown'

        is_valid = validator.validate_scenario_actions(
            actions_with_invalid_type,
            ids)
        self.assertFalse(is_valid)

        # Validate actions with invalid target
        actions_with_invalid_target = self._create_scenario_actions('4', '2')
        is_valid = validator.validate_scenario_actions(
            actions_with_invalid_target,
            ids)
        self.assertFalse(is_valid)

        # Validate actions with invalid source
        actions_with_invalid_source = self._create_scenario_actions('1', '4')
        is_valid = validator.validate_scenario_actions(
            actions_with_invalid_source,
            ids)
        self.assertFalse(is_valid)

    def test_validate_scenario_action(self):
        ids = ['1', '2', '3']

        raise_alarm_action = self._create_raise_alarm_action('1')
        is_valid = validator.validate_scenario_action(raise_alarm_action, ids)
        self.assertTrue(is_valid)

        set_state_action = self._create_set_state_action('2')
        is_valid = validator.validate_scenario_action(set_state_action, ids)
        self.assertTrue(is_valid)

        causal_action = self._create_add_causal_relationship_action('1', '3')
        is_valid = validator.validate_scenario_action(causal_action, ids)
        self.assertTrue(is_valid)

        causal_action[TemplateFields.ACTION_TYPE] = 'unknown type'
        is_valid = validator.validate_scenario_action(causal_action, ids)
        self.assertFalse(is_valid)

    def test_validate_raise_alarm_action(self):
        # Test setup
        ids = ['123', '456', '789']
        action = self._create_set_state_action('123')

        # Test action and assertions
        self.assertTrue(validator.validate_set_state_action(action, ids))

    def test_validate_set_state_action(self):
        # Test setup
        ids = ['123', '456', '789']
        action = self._create_set_state_action('123')

        # Test action and assertions
        self.assertTrue(validator.validate_set_state_action(action, ids))

    def test_validate_invalid_raise_alarm_action(self):

        # Test setup
        ids = ['123', '456', '789']

        # Invalid target id
        action = self._create_set_state_action('000')
        self.assertFalse(
            validator.validate_raise_alarm_action(action, ids))

        # Action with no target
        action[TemplateFields.ACTION_TARGET].pop(TemplateFields.TARGET)
        self.assertFalse(
            validator.validate_raise_alarm_action(action, ids))

        # Action with no severity property
        action = self._create_set_state_action('123')
        action[TemplateFields.PROPERTIES].pop(TemplateFields.SEVERITY, None)
        self.assertFalse(
            validator.validate_raise_alarm_action(action, ids))

        # Action with no alarm name property
        action = self._create_set_state_action('123')
        action[TemplateFields.PROPERTIES].pop(TemplateFields.ALARM_NAME, None)
        self.assertFalse(
            validator.validate_raise_alarm_action(action, ids))

    def test_validate_invalid_set_state_action(self):

        # Test setup
        ids = ['123', '456', '789']

        # Invalid target id
        action = self._create_set_state_action('000')
        self.assertFalse(
            validator.validate_set_state_action(action, ids))

        # Action with no target
        action[TemplateFields.ACTION_TARGET].pop(TemplateFields.TARGET)
        self.assertFalse(
            validator.validate_set_state_action(action, ids))

        # Action with no state property
        action = self._create_set_state_action('123')
        action[TemplateFields.PROPERTIES].pop(TemplateFields.STATE, None)
        self.assertFalse(
            validator.validate_set_state_action(action, ids))

    def test_validate_add_causal_relationship_action(self):
        # Test setup
        ids = ['123', '456', '789']
        action = self._create_add_causal_relationship_action('456', '123')

        # Test action and assertions
        self.assertTrue(
            validator.validate_add_causal_relationship_action(action, ids))

    def test_validate_invalid_add_causal_relationship_action(self):

        # Test setup
        ids = ['123', '456', '789']

        # Invalid target id
        action1 = self._create_add_causal_relationship_action('000', '123')
        self.assertFalse(
            validator.validate_add_causal_relationship_action(action1, ids))

        # Action with no target
        action1[TemplateFields.ACTION_TARGET].pop(TemplateFields.TARGET)
        self.assertFalse(
            validator.validate_add_causal_relationship_action(action1, ids))

        # Invalid source id
        action2 = self._create_add_causal_relationship_action('456', '000')
        self.assertFalse(
            validator.validate_add_causal_relationship_action(action2, ids))

        # Action with no source
        action2[TemplateFields.ACTION_TARGET].pop(TemplateFields.SOURCE)
        self.assertFalse(
            validator.validate_add_causal_relationship_action(action2, ids))

    def test_validate_template_id(self):

        ids = ['123', '456', '789']

        self.assertTrue(validator.validate_template_id(ids, '123'))
        self.assertFalse(validator.validate_template_id(ids, '000'))

    def _create_scenario_actions(self, target, source):

        actions = []
        raise_alarm_action = self._create_raise_alarm_action(target)
        actions.append({TemplateFields.ACTION: raise_alarm_action})

        set_state_action = self._create_set_state_action(target)
        actions.append({TemplateFields.ACTION: set_state_action})

        causal_action = self._create_add_causal_relationship_action(target,
                                                                    source)
        actions.append({TemplateFields.ACTION: causal_action})

        return actions

    # Static methods:
    @staticmethod
    def _create_add_causal_relationship_action(target, source):

        action_target = {
            TemplateFields.TARGET: target,
            TemplateFields.SOURCE: source
        }
        action = {
            TemplateFields.ACTION_TYPE: ActionType.ADD_CAUSAL_RELATIONSHIP,
            TemplateFields.ACTION_TARGET: action_target}

        return action

    @staticmethod
    def _create_set_state_action(target):

        action_target = {
            TemplateFields.TARGET: target
        }
        properties = {
            TemplateFields.STATE: 'SUBOPTIMAL'
        }
        action = {
            TemplateFields.ACTION_TYPE: ActionType.SET_STATE,
            TemplateFields.ACTION_TARGET: action_target,
            TemplateFields.PROPERTIES: properties
        }
        return action

    @staticmethod
    def _create_raise_alarm_action(target):

        action_target = {
            TemplateFields.TARGET: target
        }
        properties = {
            TemplateFields.ALARM_NAME: 'VM_CPU_SUBOPTIMAL_PERFORMANCE',
            TemplateFields.SEVERITY: 'critical'
        }
        action = {
            TemplateFields.ACTION_TYPE: ActionType.RAISE_ALARM,
            TemplateFields.ACTION_TARGET: action_target,
            TemplateFields.PROPERTIES: properties
        }
        return action
