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

from vitrage.common.constants import VertexProperties as VProps
from vitrage.evaluator.actions.base import ActionType
from vitrage.evaluator.actions.recipes.action_steps import UPDATE_VERTEX
from vitrage.evaluator.actions.recipes.set_state import SetState
from vitrage.evaluator.template import ActionSpecs
from vitrage.evaluator.template_fields import TemplateFields as TFields
from vitrage.tests import base

LOG = logging.getLogger(__name__)


class SetStateRecipeTest(base.BaseTest):

    def test_get_do_recipe(self):

        # Test Setup
        target_vertex_id = 'RESOURCE:nova.host:test1'

        targets = {TFields.TARGET: target_vertex_id}
        props = {TFields.STATE: 'SUBOPTIMAL'}

        action_spec = ActionSpecs(ActionType.SET_STATE, targets, props)

        # Test Action
        action_steps = SetState.get_do_recipe(action_spec)

        # Test Assertions
        self.assertEqual(1, len(action_steps))

        self.assertEqual(UPDATE_VERTEX, action_steps[0].type)
        update_vertex_step_params = action_steps[0].params
        self.assertEqual(2, len(update_vertex_step_params))

        vitrage_state = update_vertex_step_params[VProps.VITRAGE_STATE]
        self.assertEqual(props[TFields.STATE], vitrage_state)

        vitrage_id = update_vertex_step_params[VProps.VITRAGE_ID]
        self.assertEqual(target_vertex_id, vitrage_id)
