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
from oslo_log import log as logging

from vitrage.common import file_utils
from vitrage.evaluator.template import EdgeDescription
from vitrage.evaluator.template import Template
from vitrage.evaluator.template_fields import TemplateFields as TFields
from vitrage.graph import Vertex
from vitrage.tests import base
from vitrage.tests.mocks import utils

LOG = logging.getLogger(__name__)


class TemplateTest(base.BaseTest):

    VALID_TEMPLATE_NAME = 'host_high_cpu_load_to_instance_cpu_suboptimal.yaml'

    def test_valid_template(self):

        # Test setup
        template_path = '%s/templates/%s' % (utils.get_resources_dir(),
                                             self.VALID_TEMPLATE_NAME)
        template_definition = file_utils.load_yaml_file(template_path, True)

        template = Template(template_definition)
        entities = template.entities
        relationships = template.relationships
        scenarios = template.scenarios
        definitions = template_definition[TFields.DEFINITIONS]

        # Assertions
        entities_definition = definitions[TFields.ENTITIES]
        self._validate_entities(entities, entities_definition)

        relate_def = definitions[TFields.RELATIONSHIPS]
        self._validate_relationships(relationships, relate_def, entities)

        scenarios_definition = template_definition[TFields.SCENARIOS]
        self._validate_scenarios(scenarios, scenarios_definition)

    def _validate_entities(self, entities, entities_def):

        self.assertIsNotNone(entities)
        for entity_id, entity in entities.iteritems():

            self.assertIsInstance(entity, Vertex)
            self.assertEqual(entity_id, entity.vertex_id)
            self.assertIsNotNone(entity.properties)
            self.assertTrue(TFields.CATEGORY in entity.properties)

        self.assertEqual(len(entities), len(entities_def))

        for entity_def in entities_def:
            entity_def_dict = entity_def[TFields.ENTITY]
            self.assertTrue(entity_def_dict[TFields.TEMPLATE_ID] in entities)
            entity = entities[entity_def_dict[TFields.TEMPLATE_ID]]

            for key, value in entity_def_dict.iteritems():
                if key == TFields.TEMPLATE_ID:
                    continue
                self.assertEqual(value, entity.properties[key])

    def _validate_relationships(self, relationships, relations_def, entities):

        self.assertIsNotNone(relationships)
        for relationship_id, relationship in relationships.iteritems():

            self.assertIsInstance(relationship, EdgeDescription)
            self.assertTrue(relationship.source.vertex_id in entities)
            self.assertTrue(relationship.target.vertex_id in entities)

            relationship_props = relationship.edge.properties
            self.assertIsNotNone(relationship_props)
            relation_type = relationship_props[TFields.RELATIONSHIP_TYPE]
            self.assertEqual(relation_type, relationship.edge.label)

        self.assertEqual(len(relationships), len(relations_def))

        for relation_def in relations_def:

            relation_def_dict = relation_def[TFields.RELATIONSHIP]

            template_id = relation_def_dict[TFields.TEMPLATE_ID]
            self.assertTrue(template_id in relationships)
            relationship = relationships[template_id].edge

            for key, value in relation_def_dict.iteritems():
                if key == TFields.TEMPLATE_ID:
                    continue
                self.assertEqual(value, relationship.properties[key])

    def _validate_scenarios(self, scenarios, scenarios_definition):

        self.assertIsNotNone(scenarios)
        self.assertEqual(len(scenarios), len(scenarios_definition))

        for scenario in scenarios:

            self.assert_is_not_empty(scenario.condition)
            self.assert_is_not_empty(scenario.actions)
