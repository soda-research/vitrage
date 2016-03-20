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

from oslo_log import log as logging

from vitrage.common import file_utils
from vitrage.evaluator.template_fields import TemplateFields
from vitrage.evaluator import template_syntax_validator
from vitrage.tests import base
from vitrage.tests.mocks import utils


LOG = logging.getLogger(__name__)


# noinspection PyAttributeOutsideInit
class TemplateValidatorTest(base.BaseTest):

    # noinspection PyPep8Naming
    @classmethod
    def setUpClass(cls):

        template_dir_path = '%s/templates/general' % utils.get_resources_dir()
        template_yamls = file_utils.load_yaml_files(template_dir_path)
        cls.first_template = template_yamls[0]

    @property
    def clone_template(self):
        return copy.deepcopy(self.first_template)

    def test_template_validator(self):
        self.assertTrue(template_syntax_validator.syntax_valid(
            self.first_template))

    def test_validate_template_without_metadata_section(self):

        template = self.clone_template
        template.pop(TemplateFields.METADATA)
        self.assertFalse(template_syntax_validator.syntax_valid(template))

    def test_validate_template_without_id_in_metadata_section(self):

        template = self.clone_template
        template[TemplateFields.METADATA].pop(TemplateFields.ID)
        self.assertFalse(template_syntax_validator.syntax_valid(template))

    def test_validate_template_without_definitions_section(self):

        template = self.clone_template
        template.pop(TemplateFields.DEFINITIONS)
        self.assertFalse(template_syntax_validator.syntax_valid(template))

    def test_validate_template_without_entities(self):

        template = self.clone_template
        template[TemplateFields.DEFINITIONS].pop(TemplateFields.ENTITIES)
        self.assertFalse(template_syntax_validator.syntax_valid(template))

    def test_validate_template_with_empty_entities(self):

        template = self.clone_template
        template[TemplateFields.DEFINITIONS][TemplateFields.ENTITIES] = []
        self.assertFalse(template_syntax_validator.syntax_valid(template))

    def test_validate_entity_without_required_fields(self):

        template = self.clone_template
        definitions = template[TemplateFields.DEFINITIONS]
        entity = definitions[TemplateFields.ENTITIES][0]
        entity[TemplateFields.ENTITY].pop(TemplateFields.CATEGORY)
        self.assertFalse(template_syntax_validator.syntax_valid(template))

        template = self.clone_template
        definitions = template[TemplateFields.DEFINITIONS]
        entity = definitions[TemplateFields.ENTITIES][0]
        entity[TemplateFields.ENTITY].pop(TemplateFields.TEMPLATE_ID)
        self.assertFalse(template_syntax_validator.syntax_valid(template))

    def test_validate_relationships_without_required_fields(self):

        template = self.clone_template
        definitions = template[TemplateFields.DEFINITIONS]
        relationship = definitions[TemplateFields.RELATIONSHIPS][0]
        relationship[TemplateFields.RELATIONSHIP].pop(TemplateFields.SOURCE)
        self.assertFalse(template_syntax_validator.syntax_valid(template))

        template = self.clone_template
        definitions = template[TemplateFields.DEFINITIONS]
        relationship = definitions[TemplateFields.RELATIONSHIPS][0]
        relationship[TemplateFields.RELATIONSHIP].pop(TemplateFields.TARGET)
        self.assertFalse(template_syntax_validator.syntax_valid(template))

        template = self.clone_template
        definitions = template[TemplateFields.DEFINITIONS]
        relationship = definitions[TemplateFields.RELATIONSHIPS][0]
        relationship[TemplateFields.RELATIONSHIP].pop(
            TemplateFields.TEMPLATE_ID
        )
        self.assertFalse(template_syntax_validator.syntax_valid(template))

    def test_validate_template_without_scenarios(self):

        template = self.clone_template
        template.pop(TemplateFields.SCENARIOS)
        self.assertFalse(template_syntax_validator.syntax_valid(template))

    def test_validate_template_with_empty_scenarios(self):
        template = self.clone_template
        template[TemplateFields.SCENARIOS] = []
        self.assertFalse(template_syntax_validator.syntax_valid(template))

    def test_validate_scenario_without_required_fields(self):

        template = self.clone_template
        scenario = template[TemplateFields.SCENARIOS][0]
        scenario[TemplateFields.SCENARIO].pop(TemplateFields.CONDITION)
        self.assertFalse(template_syntax_validator.syntax_valid(template))

        template = self.clone_template
        scenario = template[TemplateFields.SCENARIOS][0]
        scenario[TemplateFields.SCENARIO].pop(TemplateFields.ACTIONS)
        self.assertFalse(template_syntax_validator.syntax_valid(template))

    def test_validate_template_with_empty_actions(self):

        template = self.clone_template
        scenario = template[TemplateFields.SCENARIOS][0]
        scenario[TemplateFields.SCENARIO][TemplateFields.ACTIONS] = []
        self.assertFalse(template_syntax_validator.syntax_valid(template))

    def test_validate_action_without_required_fields(self):

        template = self.clone_template
        scenario = template[TemplateFields.SCENARIOS][0]
        action = scenario[TemplateFields.SCENARIO][TemplateFields.ACTIONS][0]
        action[TemplateFields.ACTION].pop(TemplateFields.ACTION_TYPE)
        self.assertFalse(template_syntax_validator.syntax_valid(template))

        template = self.clone_template
        scenario = template[TemplateFields.SCENARIOS][0]
        action = scenario[TemplateFields.SCENARIO][TemplateFields.ACTIONS][0]
        action[TemplateFields.ACTION].pop(TemplateFields.ACTION_TARGET)
        self.assertFalse(template_syntax_validator.syntax_valid(template))
