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

import os

from oslo_log import log

from vitrage.common.constants import EntityCategory
from vitrage.common import file_utils
from vitrage.entity_graph.states.alarm_state import AlarmState
from vitrage.entity_graph.states.resource_state import ResourceState

LOG = log.getLogger(__name__)


class StateManager(object):

    STATES = 'states'
    PRIORITIES = 'priorities'
    UNKNOWN_TYPE = 'unknown_type'

    def __init__(self, cfg):
        self.cfg = cfg
        self.category_unknown_type = self._init_category_unknown_type()
        self.category_additional_data = self._init_category_additional_data()
        self.states_plugins = self._load_state_configurations()

    def normalize_state(self, plugin_name, state):
        upper_state = state if not state else state.upper()
        return self.states_plugins[plugin_name][self.STATES][upper_state] \
            if upper_state in self.states_plugins[plugin_name][self.STATES] else \
            self.states_plugins[plugin_name][self.UNKNOWN_TYPE]

    def state_priority(self, plugin_name, normalized_state):
        # no need to check if normalized_state exists, cause it exists for sure
        upper_state = normalized_state if not normalized_state else \
            normalized_state.upper()
        return self.states_plugins[plugin_name][self.PRIORITIES][upper_state]

    def aggregated_state(self, state1, state2, plugin_name,
                         is_normalized=False):
        upper_state1 = state1 if not state1 else state1.upper()
        upper_state2 = state2 if not state2 else state2.upper()

        normalized_state1 = upper_state1.upper() if is_normalized else \
            self.normalize_state(plugin_name, upper_state1)
        normalized_state2 = upper_state2.upper() if is_normalized else \
            self.normalize_state(plugin_name, upper_state2)

        priority_state1 = self.state_priority(plugin_name,
                                              normalized_state1)
        priority_state2 = self.state_priority(plugin_name,
                                              normalized_state2)

        return normalized_state1 if priority_state1 > priority_state2 \
            else normalized_state2

    def _load_state_configurations(self):
        states_plugins = {}

        files = file_utils.load_files(
            self.cfg.entity_graph.states_plugins_dir, '.yaml')

        for file_name in files:
            full_path = self.cfg.entity_graph.states_plugins_dir + '/' \
                + file_name
            states, priorities, unknown_type = \
                self._retrieve_states_and_priorities_from_file(full_path)
            states_plugins[os.path.splitext(file_name)[0]] = {
                self.STATES: states,
                self.PRIORITIES: priorities,
                self.UNKNOWN_TYPE: unknown_type
            }

        # TODO(Alexey): implement this after finishing implement load
        #               specific plugins from configuration
        # self._is_all_plugins_states_exists()

        return states_plugins

    def _retrieve_states_and_priorities_from_file(self, full_path):
        states = {}
        priorities = {}
        config = file_utils.load_yaml_file(full_path, with_exception=True)

        for item in config['states']:
            normalized_state = item['normalized state']

            # original to normalized state
            normalized_state_name = normalized_state['name']
            for original_state in normalized_state['original states']:
                states[original_state['name'].upper()] = normalized_state_name

            self._add_default_states(states, priorities)

            # normalized state priority
            priorities[normalized_state_name] = \
                int(normalized_state['priority'])

        self.category_additional_data[config['category']](states,
                                                          priorities,
                                                          full_path)

        category_unknown_type = self.category_unknown_type[config['category']]
        return states, priorities, category_unknown_type

    @staticmethod
    def _add_default_states(states, priorities):
        states[None] = ResourceState.UNDEFINED
        priorities[ResourceState.UNDEFINED] = 0

    @staticmethod
    def _init_category_unknown_type():
        return {
            EntityCategory.RESOURCE: ResourceState.UNRECOGNIZED,
            EntityCategory.ALARM: AlarmState.UNKNOWN
        }

    def _init_category_additional_data(self):
        return {
            EntityCategory.RESOURCE: self._resource_additional_states,
            EntityCategory.ALARM: self._alarm_additional_states
        }

    @staticmethod
    def _resource_additional_states(states, priorities, full_path):
        if ResourceState.UNRECOGNIZED not in priorities:
            raise ValueError('%s state is not defined in %s',
                             ResourceState.UNRECOGNIZED, full_path)

    @staticmethod
    def _alarm_additional_states(states, priorities, full_path):
        if AlarmState.UNKNOWN not in priorities:
            raise ValueError('%s state is not defined in %s',
                             AlarmState.UNKNOWN, full_path)
