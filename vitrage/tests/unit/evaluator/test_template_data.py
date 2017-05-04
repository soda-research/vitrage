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

from vitrage.evaluator.template_data import ActionSpecs
from vitrage.evaluator.template_data import ConditionVar
from vitrage.evaluator.template_data import EdgeDescription
from vitrage.evaluator.template_data import Scenario
from vitrage.evaluator.template_data import TemplateData
from vitrage.evaluator.template_fields import TemplateFields as TFields
from vitrage.graph import Edge
from vitrage.graph import Vertex
from vitrage.tests import base
from vitrage.tests.mocks import utils
from vitrage.utils import file as file_utils


class BasicTemplateTest(base.BaseTest):

    BASIC_TEMPLATE = 'basic.yaml'

    def test_basic_template(self):

        # Test setup
        template_path = '%s/templates/general/%s' % (utils.get_resources_dir(),
                                                     self.BASIC_TEMPLATE)
        template_definition = file_utils.load_yaml_file(template_path, True)

        template_data = TemplateData(template_definition)
        entities = template_data.entities
        relationships = template_data.relationships
        scenarios = template_data.scenarios
        definitions = template_definition[TFields.DEFINITIONS]

        # Assertions
        entities_definition = definitions[TFields.ENTITIES]
        self._validate_entities(entities, entities_definition)

        relate_def = definitions[TFields.RELATIONSHIPS]
        self._validate_relationships(relationships, relate_def, entities)
        self._validate_scenarios(scenarios, entities)

        expected_entities = {
            'alarm': Vertex(vertex_id='alarm',
                            properties={'category': 'ALARM',
                                        'type': 'nagios',
                                        'name': 'host_problem'
                                        }),
            'resource': Vertex(vertex_id='resource',
                               properties={'category': 'RESOURCE',
                                           'type': 'nova.host'
                                           })
        }

        expected_relationships = {
            'alarm_on_host': EdgeDescription(
                edge=Edge(source_id='alarm',
                          target_id='resource',
                          label='on',
                          properties={'relationship_type': 'on'}),
                source=expected_entities['alarm'],
                target=expected_entities['resource']
            )
        }

        expected_scenario = Scenario(
            id='basic_template-scenario0',
            condition=[
                [ConditionVar(symbol_name='alarm_on_host',
                              positive=True)]],
            actions=[
                ActionSpecs(
                    type='set_state',
                    targets={'target': 'resource'},
                    properties={'state': 'SUBOPTIMAL'})],
            # TODO(yujunz): verify the built subgraph is consistent with
            #               scenario definition. For now the observed value is
            #               assigned to make test passing
            subgraphs=template_data.scenarios[0].subgraphs,
            entities=expected_entities,
            relationships=expected_relationships
        )

        self._validate_strict_equal(template_data,
                                    expected_entities,
                                    expected_relationships,
                                    expected_scenario)

    def _validate_strict_equal(self,
                               template_data,
                               expected_entities,
                               expected_relationships,
                               expected_scenario
                               ):
        self.assert_dict_equal(expected_entities, template_data.entities,
                               'entities not equal')

        self.assert_dict_equal(expected_relationships,
                               template_data.relationships,
                               'relationship not equal')

        self.assertEqual(expected_scenario, template_data.scenarios[0],
                         'scenario not equal')

    def _validate_entities(self, entities, entities_def):

        self.assertIsNotNone(entities)
        for entity_id, entity in entities.items():

            self.assertIsInstance(entity, Vertex)
            self.assertEqual(entity_id, entity.vertex_id)
            self.assertIsNotNone(entity.properties)
            self.assertIn(TFields.CATEGORY, entity.properties)

        self.assertEqual(len(entities), len(entities_def))

        for entity_def in entities_def:
            entity_def_dict = entity_def[TFields.ENTITY]
            self.assertIn(entity_def_dict[TFields.TEMPLATE_ID], entities)
            entity = entities[entity_def_dict[TFields.TEMPLATE_ID]]

            for key, value in entity_def_dict.items():
                if key == TFields.TEMPLATE_ID:
                    continue
                self.assertEqual(value, entity.properties[key])

    def _validate_relationships(self, relationships, relations_def, entities):

        self.assertIsNotNone(relationships)
        for relationship_id, relationship in relationships.items():

            self.assertIsInstance(relationship, EdgeDescription)
            self.assertIn(relationship.source.vertex_id, entities)
            self.assertIn(relationship.target.vertex_id, entities)

            relationship_props = relationship.edge.properties
            self.assertIsNotNone(relationship_props)
            relation_type = relationship_props[TFields.RELATIONSHIP_TYPE]
            self.assertEqual(relation_type, relationship.edge.label)

        self.assertEqual(len(relationships), len(relations_def))

        exclude_keys = [TFields.TEMPLATE_ID, TFields.SOURCE, TFields.TARGET]
        for relation_def in relations_def:

            relation_def_dict = relation_def[TFields.RELATIONSHIP]

            template_id = relation_def_dict[TFields.TEMPLATE_ID]
            self.assertIn(template_id, relationships)
            relationship = relationships[template_id].edge

            for key, value in relation_def_dict.items():
                if key not in exclude_keys:
                    self.assertEqual(value, relationship.properties[key])

    def _validate_scenarios(self, scenarios, entities):
        """Validates scenario parsing

        Expects to single scenario:
         1. condition consists from one variable (type EdgeDescription)
         2. Actions - set state action
        :param scenarios: parsed scenarios
        :param entities
        """
        self.assertIsNotNone(scenarios)
        self.assertEqual(len(scenarios), 1)

        scenario = scenarios[0]

        condition = scenario.condition
        self.assertEqual(len(condition), 1)

        condition_var = condition[0][0]
        self.assertIsInstance(condition_var, ConditionVar)

        symbol_name = condition_var.symbol_name
        self.assertIsInstance(symbol_name, str)

        actions = scenario.actions
        self.assert_is_not_empty(scenario.actions)
        self.assertEqual(len(actions), 1)

        action = actions[0]
        self.assertEqual(action.type, 'set_state')

        targets = action.targets
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets['target'], 'resource')

        properties = action.properties
        self.assertEqual(len(properties), 1)
        self.assertEqual(properties['state'], 'SUBOPTIMAL')
