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

from vitrage.common.constants import EdgeLabels
from vitrage.common.constants import EdgeProperties
from vitrage.evaluator.actions.base import ActionType
from vitrage.evaluator.actions.recipes.action_steps import ADD_EDGE
from vitrage.evaluator.actions.recipes.add_causal_relationship import \
    AddCausalRelationship
from vitrage.evaluator.template import ActionSpecs
from vitrage.evaluator.template_fields import TemplateFields as TField
from vitrage.tests import base


LOG = logging.getLogger(__name__)


class AddCausalRelationshipTest(base.BaseTest):

    def test_get_do_recipe(self):

        # Test Setup
        target_vertex_id = 'RESOURCE:nova.host:test_target'
        source_vertex_id = 'RESOURCE:nova.host:test_source'

        targets = {
            TField.TARGET: target_vertex_id,
            TField.SOURCE: source_vertex_id
        }

        action_spec = ActionSpecs(ActionType.ADD_CAUSAL_RELATIONSHIP,
                                  targets,
                                  {})
        add_causal_relation_action = AddCausalRelationship()

        # Test Action
        action_steps = add_causal_relation_action.get_do_recipe(action_spec)

        # Test Assertions
        self.assertEqual(1, len(action_steps))

        self.assertEqual(ADD_EDGE, action_steps[0].type)
        add_edge_step_params = action_steps[0].params
        self.assertEqual(3, len(add_edge_step_params))

        source = add_edge_step_params.get(TField.SOURCE)
        self.assertEqual(source_vertex_id, source)

        target = add_edge_step_params.get(TField.TARGET)
        self.assertEqual(target_vertex_id, target)

        relation_name = add_edge_step_params[EdgeProperties.RELATIONSHIP_NAME]
        self.assertEqual(EdgeLabels.CAUSES, relation_name)
