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

from vitrage.common.constants import NotifierEventTypes
from vitrage.common.constants import VertexProperties as VProps
from vitrage.evaluator.actions.recipes.action_steps import ADD_VERTEX
from vitrage.evaluator.actions.recipes.action_steps import NOTIFY
from vitrage.evaluator.actions.recipes.action_steps import REMOVE_VERTEX
from vitrage.evaluator.actions.recipes import base
from vitrage.evaluator.actions.recipes.base import ActionStepWrapper
from vitrage.evaluator.template_fields import TemplateFields as TFields
from vitrage.synchronizer.plugins.base.alarm.properties \
    import AlarmProperties as AlarmProps


class RaiseAlarm(base.Recipe):
    """Raise a Vitrage (deduced) alarm.

    The 'get_do_recipe' and 'get_undo_recipe' receive action_spec as input.
    The action_spec contains the following fields: type, targets and
    properties. example input:

    action_spec = ActionSpecs('type'= {'raise_alarm'},
                              'targets'= {target: id},
                              'properties' = {severity : CRITICAL,
                                              alarm_name: instance_cpu_problem}
    """

    @staticmethod
    def get_do_recipe(action_spec):

        params = RaiseAlarm._get_vertex_params(action_spec)
        params[VProps.STATE] = AlarmProps.ALARM_ACTIVE_STATE
        add_vertex_step = ActionStepWrapper(ADD_VERTEX, params)

        notify_step = RaiseAlarm._get_notify_step(
            action_spec,
            NotifierEventTypes.ACTIVATE_DEDUCED_ALARM_EVENT)

        return [add_vertex_step, notify_step]

    @staticmethod
    def get_undo_recipe(action_spec):

        params = RaiseAlarm._get_vertex_params(action_spec)
        params[VProps.STATE] = AlarmProps.ALARM_INACTIVE_STATE
        remove_vertex_step = ActionStepWrapper(REMOVE_VERTEX, params)

        notify_step = RaiseAlarm._get_notify_step(
            action_spec,
            NotifierEventTypes.DEACTIVATE_DEDUCED_ALARM_EVENT)

        return [remove_vertex_step, notify_step]

    @staticmethod
    def _get_notify_step(action_spec, event_type):

        notify_params = {
            'affected_resource_id': action_spec.targets[TFields.TARGET],
            'name': action_spec.properties[TFields.ALARM_NAME],
            'event_type': event_type,
        }
        notify_step = ActionStepWrapper(NOTIFY, notify_params)
        return notify_step

    @staticmethod
    def _get_vertex_params(action_spec):

        add_vertex_params = action_spec.targets.copy()
        add_vertex_params.update(action_spec.properties)

        return add_vertex_params
