# Copyright 2017 - Nokia
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

from vitrage.evaluator.actions.base import ActionType
from vitrage.evaluator.actions.recipes.execute_mistral import WORKFLOW
from vitrage.evaluator.template_fields import TemplateFields
from vitrage.evaluator.template_validation.content.execute_mistral_validator \
    import ExecuteMistralValidator
from vitrage.tests.unit.evaluator.template_validation.content.base import \
    ActionValidatorTest
from vitrage.tests.unit.evaluator.template_validation.content.base import \
    DEFINITIONS_INDEX_MOCK


class ExecuteMistralValidatorTest(ActionValidatorTest):

    def test_validate_execute_mistral_action(self):

        self._validate_action(
            self._create_execute_mistral_action('wf_1', 'host_2', 'down'),
            ExecuteMistralValidator.validate
        )

    def test_validate_execute_mistral_action_without_workflow(self):

        # Test setup
        idx = DEFINITIONS_INDEX_MOCK.copy()
        action = self._create_execute_mistral_action('wf_1', 'host_2', 'down')
        action[TemplateFields.PROPERTIES].pop(WORKFLOW)

        # Test action
        result = ExecuteMistralValidator.validate(action, idx)

        # Test assertions
        self._assert_fault_result(result, 133)

    def test_validate_execute_mistral_action_with_empty_workflow(self):

        # Test setup
        idx = DEFINITIONS_INDEX_MOCK.copy()
        action = self._create_execute_mistral_action('', 'host_2', 'down')

        # Test action
        result = ExecuteMistralValidator.validate(action, idx)

        # Test assertions
        self._assert_fault_result(result, 133)

    def test_validate_execute_mistral_action_with_none_workflow(self):

        # Test setup
        idx = DEFINITIONS_INDEX_MOCK.copy()
        action = self._create_execute_mistral_action(None, 'host_2', 'down')

        # Test action
        result = ExecuteMistralValidator.validate(action, idx)

        # Test assertions
        self._assert_fault_result(result, 133)

    def test_validate_execute_mistral_action_without_additional_params(self):

        # Test setup - having only the 'workflow' param is a legal config
        idx = DEFINITIONS_INDEX_MOCK.copy()
        action = self._create_execute_mistral_action('wf_1', 'host_2', 'down')
        action[TemplateFields.PROPERTIES].pop('host')
        action[TemplateFields.PROPERTIES].pop('host_state')

        # Test action
        result = ExecuteMistralValidator.validate(action, idx)

        # Test assertions
        self._assert_correct_result(result)

    @staticmethod
    def _create_execute_mistral_action(workflow, host, host_state):

        properties = {
            WORKFLOW: workflow,
            'host': host,
            'host_state': host_state
        }
        action = {
            TemplateFields.ACTION_TYPE: ActionType.EXECUTE_MISTRAL,
            TemplateFields.PROPERTIES: properties
        }

        return action
