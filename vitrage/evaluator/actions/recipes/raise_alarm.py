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

from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources.alarm_properties import AlarmProperties as AlarmProps
from vitrage.evaluator.actions.recipes.action_steps import ADD_VERTEX
from vitrage.evaluator.actions.recipes.action_steps import REMOVE_VERTEX
from vitrage.evaluator.actions.recipes import base
from vitrage.evaluator.actions.recipes.base import ActionStepWrapper


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

        return [add_vertex_step]

    @staticmethod
    def get_undo_recipe(action_spec):

        params = RaiseAlarm._get_vertex_params(action_spec)
        params[VProps.STATE] = AlarmProps.ALARM_INACTIVE_STATE
        remove_vertex_step = ActionStepWrapper(REMOVE_VERTEX, params)

        return [remove_vertex_step]

    @staticmethod
    def _get_vertex_params(action_spec):

        add_vertex_params = action_spec.targets.copy()
        add_vertex_params.update(action_spec.properties)

        return add_vertex_params
