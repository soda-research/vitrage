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
from vitrage.evaluator.actions.base import ActionType
from vitrage.evaluator.actions.recipes.action_steps import ADD_VERTEX
from vitrage.evaluator.actions.recipes.action_steps import NOTIFY
from vitrage.evaluator.actions.recipes.action_steps import REMOVE_VERTEX
from vitrage.evaluator.actions.recipes.raise_alarm import RaiseAlarm
from vitrage.evaluator.template import ActionSpecs

from vitrage.evaluator.template_fields import TemplateFields as TFields
from vitrage.tests import base


LOG = logging.getLogger(__name__)


class RaiseAlarmRecipeTest(base.BaseTest):

    def test_get_do_recipe(self):

        # Test Setup
        target_vertex_id = 'RESOURCE:nova.host:test1'

        targets = {TFields.TARGET: target_vertex_id}
        props = {TFields.ALARM_NAME: 'VM_CPU_SUBOPTIMAL_PERFORMANCE'}

        action_spec = ActionSpecs(ActionType.SET_STATE, targets, props)

        # Test Action
        action_steps = RaiseAlarm.get_do_recipe(action_spec)

        # Test Assertions
        self.assertEqual(2, len(action_steps))

        self.assertEqual(ADD_VERTEX, action_steps[0].type)
        add_vertex_step_params = action_steps[0].params
        self.assertEqual(3, len(add_vertex_step_params))

        alarm_name = add_vertex_step_params[TFields.ALARM_NAME]
        self.assertEqual(props[TFields.ALARM_NAME], alarm_name)

        target_vitrage_id = add_vertex_step_params[TFields.TARGET]
        self.assertEqual(target_vertex_id, target_vitrage_id)

        self.assertEqual(NOTIFY, action_steps[1].type)

    def test_get_undo_recipe(self):

        # Test Setup
        target_vertex_id = 'RESOURCE:nova.host:test1'

        targets = {TFields.TARGET: target_vertex_id}
        props = {TFields.ALARM_NAME: 'VM_CPU_SUBOPTIMAL_PERFORMANCE'}

        action_spec = ActionSpecs(ActionType.SET_STATE, targets, props)

        # Test Action
        action_steps = RaiseAlarm.get_undo_recipe(action_spec)

        # Test Assertions
        self.assertEqual(2, len(action_steps))

        self.assertEqual(REMOVE_VERTEX, action_steps[0].type)
        remove_vertex_step_params = action_steps[0].params
        self.assertEqual(3, len(remove_vertex_step_params))

        alarm_name = remove_vertex_step_params[TFields.ALARM_NAME]
        self.assertEqual(props[TFields.ALARM_NAME], alarm_name)

        target_vitrage_id = remove_vertex_step_params[TFields.TARGET]
        self.assertEqual(target_vertex_id, target_vitrage_id)

        self.assertEqual(NOTIFY, action_steps[1].type)
