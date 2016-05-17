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
from vitrage.evaluator.template_syntax_validator import ELEMENTS_MIN_NUM_ERROR
from vitrage.evaluator.template_syntax_validator import \
    MANDATORY_SECTIONS_ERROR
from vitrage.evaluator.template_syntax_validator import RESULT_COMMENT
from vitrage.evaluator.template_syntax_validator import RESULT_STATUS
from vitrage.evaluator.template_syntax_validator import SCHEMA_CONTENT_ERROR
from vitrage.tests import base
from vitrage.tests.mocks import utils


LOG = logging.getLogger(__name__)


# noinspection PyAttributeOutsideInit
class TemplateSyntaxValidatorTest(base.BaseTest):

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
        self.assertTrue(template_syntax_validator.syntax_validation(
            self.first_template))

    def test_validate_template_without_metadata_section(self):

        template = self.clone_template
        template.pop(TemplateFields.METADATA)
        self._test_execution(template, MANDATORY_SECTIONS_ERROR)

    def test_validate_template_without_id_in_metadata_section(self):

        template = self.clone_template
        template[TemplateFields.METADATA].pop(TemplateFields.ID)

        expected_comment = SCHEMA_CONTENT_ERROR % (
            TemplateFields.METADATA, TemplateFields.ID)

        self._test_execution(template, expected_comment)

    def test_validate_template_without_definitions_section(self):

        template = self.clone_template
        template.pop(TemplateFields.DEFINITIONS)
        self._test_execution(template, MANDATORY_SECTIONS_ERROR)

    def test_validate_template_without_entities(self):

        template = self.clone_template
        template[TemplateFields.DEFINITIONS].pop(TemplateFields.ENTITIES)
        expected_comment = SCHEMA_CONTENT_ERROR % (
            TemplateFields.DEFINITIONS,
            '"%s"' % TemplateFields.ENTITIES
        )

        self._test_execution(template, expected_comment)

    def test_validate_template_with_empty_entities(self):

        # Test setup
        template = self.clone_template
        template[TemplateFields.DEFINITIONS][TemplateFields.ENTITIES] = []
        expected_comment = ELEMENTS_MIN_NUM_ERROR % TemplateFields.ENTITY

        self._test_execution(template, expected_comment)

    def test_validate_entity_without_required_fields(self):

        self._validate_entity_without_missing_required_field(
            TemplateFields.CATEGORY)

        self._validate_entity_without_missing_required_field(
            TemplateFields.TEMPLATE_ID)

    def _validate_entity_without_missing_required_field(self, field_name):

        # Test setup
        template = self.clone_template
        definitions = template[TemplateFields.DEFINITIONS]
        entity = definitions[TemplateFields.ENTITIES][0]
        entity[TemplateFields.ENTITY].pop(field_name)

        expected_comment = SCHEMA_CONTENT_ERROR % (
            TemplateFields.ENTITY,
            '"%s" and "%s"' % (TemplateFields.CATEGORY,
                               TemplateFields.TEMPLATE_ID)
        )

        self._test_execution(template, expected_comment)

    def test_validate_relationships_without_required_fields(self):

        self._validate_relationships_with_missing_required_field(
            TemplateFields.SOURCE)

        self._validate_relationships_with_missing_required_field(
            TemplateFields.TARGET)

        self._validate_relationships_with_missing_required_field(
            TemplateFields.TEMPLATE_ID)

    def _validate_relationships_with_missing_required_field(self, field_name):

        # Test setup
        template = self.clone_template
        definitions = template[TemplateFields.DEFINITIONS]
        relationship = definitions[TemplateFields.RELATIONSHIPS][0]
        relationship[TemplateFields.RELATIONSHIP].pop(field_name)

        expected_comment = SCHEMA_CONTENT_ERROR % (
            TemplateFields.RELATIONSHIP, '"%s", "%s" and "%s"' % (
                TemplateFields.SOURCE,
                TemplateFields.TARGET,
                TemplateFields.TEMPLATE_ID
            )
        )

        self._test_execution(template, expected_comment)

    def test_validate_template_without_scenarios_section(self):

        # Test setup
        template = self.clone_template
        template.pop(TemplateFields.SCENARIOS)
        self._test_execution(template, MANDATORY_SECTIONS_ERROR)

    def test_validate_template_with_empty_scenarios(self):

        # Test setup
        template = self.clone_template
        template[TemplateFields.SCENARIOS] = []
        expected_comment = ELEMENTS_MIN_NUM_ERROR % TemplateFields.SCENARIO

        self._test_execution(template, expected_comment)

    def test_validate_scenario_without_required_condition_field(self):

        # Test setup
        template = self.clone_template
        scenario = template[TemplateFields.SCENARIOS][0]
        scenario[TemplateFields.SCENARIO].pop(TemplateFields.CONDITION)

        expected_comment = SCHEMA_CONTENT_ERROR % (
            TemplateFields.SCENARIOS,
            '"%s" and "%s"' % (TemplateFields.CONDITION,
                               TemplateFields.ACTIONS)
        )

        self._test_execution(template, expected_comment)

    def test_validate_scenario_without_required_actions_field(self):

        # Test setup
        template = self.clone_template
        scenario = template[TemplateFields.SCENARIOS][0]
        scenario[TemplateFields.SCENARIO].pop(TemplateFields.ACTIONS)

        expected_comment = SCHEMA_CONTENT_ERROR % (
            TemplateFields.SCENARIOS,
            '"%s" and "%s"' % (TemplateFields.CONDITION,
                               TemplateFields.ACTIONS)
        )

        self._test_execution(template, expected_comment)

    def test_validate_template_with_no_actions(self):

        # Test setup
        template = self.clone_template
        scenario = template[TemplateFields.SCENARIOS][0]
        scenario[TemplateFields.SCENARIO][TemplateFields.ACTIONS] = []
        expected_comment = ELEMENTS_MIN_NUM_ERROR % TemplateFields.ACTION

        self._test_execution(template, expected_comment)

    def test_validate_action_without_required_action_target_field(self):

        # Test setup
        template = self.clone_template
        scenario = template[TemplateFields.SCENARIOS][0]
        action = scenario[TemplateFields.SCENARIO][TemplateFields.ACTIONS][0]
        action[TemplateFields.ACTION].pop(TemplateFields.ACTION_TARGET)

        expected_comment = SCHEMA_CONTENT_ERROR % (
            TemplateFields.ACTION, '"%s" and "%s"' % (
                TemplateFields.ACTION_TYPE, TemplateFields.ACTION_TARGET)
        )

        self._test_execution(template, expected_comment)

    def test_validate_action_without_required_action_type_field(self):

        # Test setup
        template = self.clone_template
        scenario = template[TemplateFields.SCENARIOS][0]
        action = scenario[TemplateFields.SCENARIO][TemplateFields.ACTIONS][0]
        action[TemplateFields.ACTION].pop(TemplateFields.ACTION_TYPE)

        expected_comment = SCHEMA_CONTENT_ERROR % (
            TemplateFields.ACTION, '"%s" and "%s"' % (
                TemplateFields.ACTION_TYPE, TemplateFields.ACTION_TARGET)
        )

        self._test_execution(template, expected_comment)

    def _test_execution(self, template, expected_comment):

        # Test action
        result = template_syntax_validator.syntax_validation(template)

        # Test assertions
        self.assertFalse(result[RESULT_STATUS])
        self.assertEqual(expected_comment, result[RESULT_COMMENT])
