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
from oslo_log import log

from vitrage.common import file_utils
from vitrage.evaluator.template import Template
from vitrage.evaluator.template_syntax_validator import syntax_validate


LOG = log.getLogger(__name__)


action_types = {
    'RAISE_ALARM': 'raise_alarm',
    'ADD_CAUSAL_RELATIONSHIP': 'add_causal_relationship',
    'SET_STATE': 'set_state'
}


class ScenarioRepository(object):

    def __init__(self, conf):
        self._load_templates_files(conf)
        self.scenarios = {}

    def add_template(self, template_definition):

        if syntax_validate(template_definition):
            template = Template(template_definition)
            print(template)

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

        # trigger_id_before = 'template_id of trigger for before scenario'
        # trigger_id_now = 'template_id of trigger for now scenario'

        # return {'before': [(scenario., trigger_id_before)],
        #         'now': [(scenario.Scenario, trigger_id_now)]}

        pass

    def _load_templates_files(self, conf):

        templates_dir_path = conf.evaluator.templates_dir
        template_definitions = file_utils.load_yaml_files(templates_dir_path)

        for template_definition in template_definitions:
            self.add_template(template_definition)
