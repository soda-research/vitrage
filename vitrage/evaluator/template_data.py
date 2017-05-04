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
from sympy.logic.boolalg import And
from sympy.logic.boolalg import Not
from sympy.logic.boolalg import Or
from sympy.logic.boolalg import to_dnf as sympy_to_dfn
from sympy import Symbol

from vitrage.common.constants import EdgeProperties as EProps
from vitrage.common.constants import VertexProperties as VProps
from vitrage.common.exception import VitrageError
from vitrage.evaluator.template_fields import TemplateFields as TFields
from vitrage.graph.algo_driver.sub_graph_matching import NEG_CONDITION
from vitrage.graph.driver.networkx_graph import NXGraph
from vitrage.graph import Edge
from vitrage.graph import Vertex

ConditionVar = namedtuple('ConditionVar', ['symbol_name', 'positive'])
ActionSpecs = namedtuple('ActionSpecs', ['type', 'targets', 'properties'])
Scenario = namedtuple('Scenario', ['id',
                                   'condition',
                                   'actions',
                                   'subgraphs',
                                   'entities',
                                   'relationships'
                                   ])
EdgeDescription = namedtuple('EdgeDescription', ['edge', 'source', 'target'])

ENTITY = 'entity'
RELATIONSHIP = 'relationship'


def copy_edge_desc(edge_desc):
    return EdgeDescription(edge=edge_desc.edge.copy(),
                           source=edge_desc.source.copy(),
                           target=edge_desc.target.copy())


# noinspection PyAttributeOutsideInit
class TemplateData(object):

    def __init__(self, template_def):

        self.name = template_def[TFields.METADATA][TFields.NAME]

        defs = template_def[TFields.DEFINITIONS]
        self.entities = self._build_entities(defs[TFields.ENTITIES])

        self.relationships = {}
        if TFields.RELATIONSHIPS in defs:
            self.relationships = self._build_relationships(
                defs[TFields.RELATIONSHIPS])

        self.scenarios = self._build_scenarios(template_def[TFields.SCENARIOS])

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, template_name):
        self._name = template_name

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

    @property
    def scenarios(self):
        return self._scenarios

    @scenarios.setter
    def scenarios(self, scenarios):
        self._scenarios = scenarios

    def _build_entities(self, entities_defs):

        entities = {}
        for entity_def in entities_defs:

            entity_dict = entity_def[TFields.ENTITY]
            template_id = entity_dict[TFields.TEMPLATE_ID]
            properties = self._extract_properties(entity_dict)
            entities[template_id] = Vertex(template_id, properties)

        return entities

    def _build_relationships(self, relationships_defs):

        relationships = {}
        for relationship_def in relationships_defs:

            relationship_dict = relationship_def[TFields.RELATIONSHIP]
            relationship = self._extract_relationship_info(relationship_dict)
            template_id = relationship_dict[TFields.TEMPLATE_ID]
            relationships[template_id] = relationship

        return relationships

    def _extract_relationship_info(self, relationship_dict):

        source_id = relationship_dict[TFields.SOURCE]
        target_id = relationship_dict[TFields.TARGET]

        edge = Edge(source_id,
                    target_id,
                    relationship_dict[TFields.RELATIONSHIP_TYPE],
                    self._extract_properties(relationship_dict))

        source = self.entities[source_id]
        target = self.entities[target_id]
        return EdgeDescription(edge, source, target)

    @staticmethod
    def _extract_properties(var_dict):

        ignore_ids = [TFields.TEMPLATE_ID, TFields.SOURCE, TFields.TARGET]
        return dict((key, var_dict[key]) for key in var_dict
                    if key not in ignore_ids)

    def _build_scenarios(self, scenarios_defs):

        scenarios = []
        for counter, scenario_def in enumerate(scenarios_defs):
            scenario_id = "%s-scenario%s" % (self.name, str(counter))
            scenario_dict = scenario_def[TFields.SCENARIO]
            scenarios.append(TemplateData.ScenarioData(
                scenario_id,
                scenario_dict, self).to_tuple())
        return scenarios

    class ScenarioData(object):
        def __init__(self, scenario_id, scenario_dict, template_data):
            self._template_entities = template_data.entities
            self._template_relationships = template_data.relationships

            self._entities = {}
            self._relationships = {}

            self.scenario_id = scenario_id
            self.condition = self._parse_condition(
                scenario_dict[TFields.CONDITION])
            self.actions = self._build_actions(scenario_dict[TFields.ACTIONS])
            self.subgraphs = TemplateData.SubGraph.from_condition(
                self.condition,
                self._extract_var_and_update_index)

        def __eq__(self, other):
            return self.scenario_id == other.scenario_id \
                and self.condition == other.condition \
                and self.actions == other.actions

        def to_tuple(self):
            return Scenario(id=self.scenario_id,
                            condition=self.condition,
                            actions=self.actions,
                            subgraphs=self.subgraphs,
                            entities=self._entities,
                            relationships=self._relationships)

        @classmethod
        def build_equivalent_scenario(cls,
                                      scenario,
                                      template_id,
                                      entity_props):
            entities = scenario.entities.copy()
            entities[template_id] = Vertex(
                vertex_id=entities[template_id].vertex_id,
                properties={k: v for k, v in entity_props})
            relationships = {
                rel_id: cls.build_equivalent_relationship(rel,
                                                          template_id,
                                                          entity_props)
                for rel_id, rel in scenario.relationships.items()}

            def extract_var(symbol_name):
                if symbol_name in entities:
                    return entities[symbol_name], ENTITY
                elif symbol_name in relationships:
                    return relationships[symbol_name], RELATIONSHIP
                else:
                    raise VitrageError('invalid symbol name: {}'
                                       .format(symbol_name))

            subgraphs = TemplateData.SubGraph.from_condition(
                scenario.condition, extract_var)

            return Scenario(id=scenario.id + '_equivalence',
                            condition=scenario.condition,
                            actions=scenario.actions,
                            subgraphs=subgraphs,
                            entities=entities,
                            relationships=relationships)

        @classmethod
        def build_equivalent_relationship(cls,
                                          relationship,
                                          template_id,
                                          entity_props):
            source = relationship.source
            target = relationship.target
            if relationship.edge.source_id == template_id:
                source = Vertex(vertex_id=source.vertex_id,
                                properties={k: v for k, v in entity_props})
            elif relationship.edge.target_id == template_id:
                target = Vertex(vertex_id=target.vertex_id,
                                properties={k: v for k, v in entity_props})
            return EdgeDescription(source=source,
                                   target=target,
                                   edge=relationship.edge)

        @staticmethod
        def _build_actions(actions_def):

            actions = []
            for action_def in actions_def:

                action_dict = action_def[TFields.ACTION]
                action_type = action_dict[TFields.ACTION_TYPE]
                targets = action_dict[TFields.ACTION_TARGET]
                properties = action_dict.get(TFields.PROPERTIES, {})

                actions.append(ActionSpecs(action_type, targets, properties))

            return actions

        def _parse_condition(self, condition_str):
            """Parse condition string into an object

            The condition string will be converted here into DNF (Disjunctive
            Normal Form), e.g., (X and Y) or (X and Z) or (X and V and not W)
            ... where X, Y, Z, V, W are either entities or relationships
            more details: https://en.wikipedia.org/wiki/Disjunctive_normal_form

            The condition variable lists is then extracted from the DNF object.
            It is a list of lists. Each inner list represents an AND expression
            compound condition variables. The outer list presents the OR
            expression

              [[and_var1, and_var2, ...], or_list_2, ...]

            :param condition_str: the string as it written in the template
            :return: condition_vars_lists
            """

            condition_dnf = self.convert_to_dnf_format(condition_str)

            if isinstance(condition_dnf, Or):
                return self._extract_or_condition(condition_dnf)

            if isinstance(condition_dnf, And):
                return [self._extract_and_condition(condition_dnf)]

            if isinstance(condition_dnf, Not):
                return [(self._extract_not_condition_var(condition_dnf))]

            if isinstance(condition_dnf, Symbol):
                return [[(self._extract_condition_var(condition_dnf, True))]]

        @staticmethod
        def convert_to_dnf_format(condition_str):

            condition_str = condition_str.replace(' and ', '&')
            condition_str = condition_str.replace(' or ', '|')
            condition_str = condition_str.replace(' not ', '~')
            condition_str = condition_str.replace('not ', '~')

            return sympy_to_dfn(condition_str)

        def _extract_or_condition(self, or_condition):

            vars_ = []
            for var in or_condition.args:

                if isinstance(var, And):
                    vars_.append(self._extract_and_condition(var))
                else:
                    is_symbol = isinstance(var, Symbol)
                    vars_.append([self._extract_condition_var(var, is_symbol)])

            return vars_

        def _extract_and_condition(self, and_condition):
            return [self._extract_condition_var(arg, isinstance(arg, Symbol))
                    for arg in and_condition.args]

        def _extract_not_condition_var(self, not_condition):
            return [self._extract_condition_var(arg, False)
                    for arg in not_condition.args]

        def _extract_condition_var(self, symbol, positive):
            if isinstance(symbol, Not):
                return self._extract_not_condition_var(symbol)[0]
            return ConditionVar(symbol.name, positive)

        def _extract_var_and_update_index(self, symbol_name):

            if symbol_name in self._template_relationships:
                relationship = self._template_relationships[symbol_name]
                self._relationships[symbol_name] = relationship
                self._entities.update({
                    relationship.edge.source_id: relationship.source,
                    relationship.edge.target_id: relationship.target
                })
                return relationship, RELATIONSHIP

            entity = self._template_entities[symbol_name]
            self._entities[symbol_name] = entity
            return entity, ENTITY

    class SubGraph(object):
        @classmethod
        def from_condition(cls, condition, extract_var):
            return [cls.from_clause(clause, extract_var)
                    for clause in condition]

        @classmethod
        def from_clause(cls, clause, extract_var):
            condition_g = NXGraph("scenario condition")

            for term in clause:
                variable, var_type = extract_var(term.symbol_name)
                if var_type == ENTITY:
                    vertex = variable.copy()
                    vertex[VProps.IS_DELETED] = False
                    vertex[VProps.IS_PLACEHOLDER] = False
                    condition_g.add_vertex(vertex)

                else:  # type = relationship
                    # prevent overwritten of NEG_CONDITION and IS_DELETED
                    # property when there are both "not A" and "A" in same
                    # template
                    edge_desc = copy_edge_desc(variable)
                    cls._set_edge_relationship_info(edge_desc, term.positive)
                    cls._add_edge_relationship(condition_g, edge_desc)

            return condition_g

        @staticmethod
        def _set_edge_relationship_info(edge_description,
                                        is_positive_condition):
            if not is_positive_condition:
                edge_description.edge[NEG_CONDITION] = True
                edge_description.edge[EProps.IS_DELETED] = True
            else:
                edge_description.edge[EProps.IS_DELETED] = False
                edge_description.edge[NEG_CONDITION] = False

            edge_description.source[VProps.IS_DELETED] = False
            edge_description.source[VProps.IS_PLACEHOLDER] = False
            edge_description.target[VProps.IS_DELETED] = False
            edge_description.target[VProps.IS_PLACEHOLDER] = False

        @staticmethod
        def _add_edge_relationship(condition_graph, edge_description):
            condition_graph.add_vertex(edge_description.source)
            condition_graph.add_vertex(edge_description.target)
            condition_graph.add_edge(edge_description.edge)
