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
from collections import namedtuple
from oslo_log import log
from sympy.logic.boolalg import And
from sympy.logic.boolalg import Not
from sympy.logic.boolalg import Or
from sympy.logic.boolalg import to_dnf
from sympy import Symbol

from vitrage.evaluator.template_fields import TemplateFields as TFields
from vitrage.graph import Edge
from vitrage.graph import Vertex


LOG = log.getLogger(__name__)


ConditionVar = namedtuple('ConditionVar', ['element', 'type', 'positive'])
ActionSpecs = namedtuple('ActionSpecs', ['type', 'targets', 'properties'])
Scenario = namedtuple('Scenario', ['condition', 'actions'])


TYPE_ENTITY = 'entity'
TYPE_RELATIONSHIP = 'relationship'


class Template(object):

    def __init__(self, template_def):

        super(Template, self).__init__()

        self.template_name = template_def[TFields.METADATA][TFields.ID]

        definitions = template_def[TFields.DEFINITIONS]
        self.entities = self._build_entities(definitions[TFields.ENTITIES])
        self.relationships = self._build_relationships(
            definitions[TFields.RELATIONSHIPS])

        self.scenarios = self._build_scenarios(template_def[TFields.SCENARIOS])

    @property
    def entities(self):
        return self._entities

    @entities.setter
    def entities(self, entities):
        self._entities = entities

    @property
    def relationships(self):
        return self._relationships

    @relationships.setter
    def relationships(self, relationships):
        self._relationships = relationships

    def _build_entities(self, entities_definitions):

        entities = {}
        for entity_definition in entities_definitions:

            entity_dict = entity_definition[TFields.ENTITY]
            template_id = entity_dict[TFields.TEMPLATE_ID]
            entities[template_id] = Vertex(template_id, entity_dict)

        return entities

    def _build_relationships(self, relationships_defs):

        relationships = {}
        for relationship_def in relationships_defs:

            relationship_dict = relationship_def[TFields.RELATIONSHIP]
            relationship = self._create_edge(relationship_dict)
            template_id = relationship_dict[TFields.TEMPLATE_ID]
            relationships[template_id] = relationship

        return relationships

    def _create_edge(self, relationship_dict):

        return Edge(relationship_dict[TFields.SOURCE],
                    relationship_dict[TFields.TARGET],
                    relationship_dict[TFields.RELATIONSHIP_TYPE],
                    relationship_dict)

    def _build_scenarios(self, scenarios_defs):

        scenarios = []
        for scenarios_def in scenarios_defs:

            scenario_dict = scenarios_def[TFields.SCENARIO]
            condition = self._parse_condition(scenario_dict[TFields.CONDITION])
            action_specs = self._build_actions(scenario_dict[TFields.ACTIONS])
            scenarios.append(Scenario(condition, action_specs))

        return scenarios

    def _build_actions(self, actions_def):

        actions = []
        for action_def in actions_def:
            action_dict = action_def[TFields.ACTION]

            action_type = action_dict[TFields.ACTION_TYPE]

            target_def = action_dict[TFields.ACTION_TARGET]
            targets = self._extract_action_target(target_def)

            properties = {}
            if TFields.PROPERTIES in action_dict:
                properties = action_dict[TFields.PROPERTIES]

            actions.append(ActionSpecs(action_type, targets, properties))

        return actions

    def _extract_action_target(self, action_target):

        targets = {}

        for key, value in action_target.iteritems():
            targets[key] = self._extract_variable(value)

        return targets

    def _parse_condition(self, condition_str):
        """Parse condition string into an object

        The condition object is formatted in DNF (Disjunctive Normal Form),
        e.g., (X and Y) or (X and Z) or (X and V and not W)...
        where X, Y, Z, V, W are either entities or relationships
        more details: https://en.wikipedia.org/wiki/Disjunctive_normal_form

        The condition object itself is a list of tuples. each tuple represents
        an AND expression compound ConditionElements. The list presents the
        OR expression e.g. [(condition_element1, condition_element2)]

        :param condition_str: the string as it written in the template itself
        :return: Condition object
        """

        condition_dnf = self.convert_to_dnf_format(condition_str)

        if isinstance(condition_dnf, Or):
            return self._extract_or_condition(condition_dnf)

        if isinstance(condition_dnf, And):
            return [self._extract_and_condition(condition_dnf)]

        if isinstance(condition_dnf, Not):
            return [(self._extract_not_condition(condition_dnf))]

        if isinstance(condition_dnf, Symbol):
            return [(self._extract_condition_variable(condition_dnf, False))]

    def convert_to_dnf_format(self, condition_str):

        condition_str = condition_str.replace('and', '&')
        condition_str = condition_str.replace('or', '|')
        condition_str = condition_str.replace('not ', '~')

        return to_dnf(condition_str)

    def _extract_or_condition(self, or_condition):

        variables = []
        for variable in or_condition.args:

            if isinstance(variable, And):
                variables.append((self._extract_and_condition(variable)),)
            elif isinstance(variable, Not):
                variables.append((self._extract_not_condition(variable),))
            else:
                variables.append((self._extract_condition_variable(variable,
                                                                   False),))
        return variables

    def _extract_and_condition(self, and_condition):

        variables = ()
        for arg in and_condition.args:
            if isinstance(arg, Not):
                condition_var = self._extract_not_condition(arg)
            else:
                condition_var = self._extract_condition_variable(arg, False)
            variables = variables + condition_var

        return variables

    def _extract_not_condition(self, not_condition):
        self._extract_condition_variable(not_condition.args, True)

    def _extract_condition_variable(self, symbol, not_):

        template_id = symbol.__str__()
        variable = self._extract_variable(template_id)

        if variable:
            return ConditionVar(variable[0], variable[1], not_)

        return None

    def _extract_variable(self, template_id):

        if template_id in self.relationships:
            return self.relationships[template_id], TYPE_RELATIONSHIP

        if template_id in self.entities:
            return self.entities[template_id], TYPE_ENTITY

        LOG.error('Cannot find template_id = %s in template named: %s' %
                  (template_id, self.template_name))
        return None
