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

import vitrage.evaluator.scenario as scenario


class ScenarioManager(object):

    def get_relevant_scenarios(self, element_before, element_now):
        """Returns scenarios triggered by an event.

        Returned scenarios are divided into two disjoint lists, based on the
        element state (before/now) that triggered the scenario condition.

        Note that this should intuitively mean that the "before" scenarios will
        activate their "undo" operation, while the "now" will activate the
        "execute" operation.

        :param element_before:
        :param element_now:
        :return:
        :rtype: dict
        """

        trigger_id_before = 'template_id of trigger for before scenario'
        trigger_id_now = 'template_id of trigger for now scenario'

        return {'before': [(scenario.Scenario(), trigger_id_before)],
                'now': [(scenario.Scenario(), trigger_id_now)]}
