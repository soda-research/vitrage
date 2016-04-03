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
from vitrage.common.constants import VertexProperties as VProps
from vitrage.common import file_utils
from vitrage.entity_graph.states.alarm_normalizator import AlarmNormalizator
from vitrage.entity_graph.states.normalized_resource_state \
    import NormalizedResourceState
from vitrage.entity_graph.states.resource_normalizator import \
    ResourceNormalizator

LOG = log.getLogger(__name__)


class StateManager(object):
    STATES = 'states'
    PRIORITIES = 'priorities'

    def __init__(self, conf):
        self.conf = conf
        self.category_normalizator = self._init_category_normalizator()
        self.states_plugins = self._load_state_configurations()

    def normalize_state(self, category, plugin_name, state):
        upper_state = state if not state else state.upper()
        important_states = \
            self.category_normalizator[category].important_states()

        if plugin_name in self.states_plugins:
            return self.states_plugins[plugin_name][self.STATES][upper_state] \
                if upper_state in \
                self.states_plugins[plugin_name][self.STATES] else \
                self.states_plugins[plugin_name][important_states.unknown]
        else:
            return important_states.undefined

    def state_priority(self, plugin_name, normalized_state):
        # no need to check if normalized_state exists, cause it exists for sure
        upper_state = normalized_state if not normalized_state else \
            normalized_state.upper()

        if plugin_name in self.states_plugins:
            return \
                self.states_plugins[plugin_name][self.PRIORITIES][upper_state]
        else:
            # default UNDEFINED priority
            return 0

    def aggregated_state(self, new_vertex, graph_vertex, is_normalized=False):
        plugin_name = new_vertex[VProps.TYPE] if VProps.TYPE in \
            new_vertex.properties else graph_vertex[VProps.TYPE]
        category = new_vertex[VProps.CATEGORY] if VProps.CATEGORY in \
            new_vertex.properties else graph_vertex[VProps.CATEGORY]

        if plugin_name in self.states_plugins:
            state_properties = \
                self.category_normalizator[category].state_properties()
            normalized_state, state_priority = \
                self._find_normalized_state_and_priority(new_vertex,
                                                         graph_vertex,
                                                         state_properties[0],
                                                         category,
                                                         plugin_name,
                                                         is_normalized)
            state_properties.pop(0)

            for property_ in state_properties:
                tmp_normalized_state, tmp_state_priority = \
                    self._find_normalized_state_and_priority(new_vertex,
                                                             graph_vertex,
                                                             property_,
                                                             category,
                                                             plugin_name,
                                                             is_normalized)
                if tmp_state_priority > state_priority:
                    normalized_state = tmp_normalized_state
                    state_priority = tmp_state_priority

            self.category_normalizator[category].set_aggregated_state(
                new_vertex, normalized_state)
        else:
            self.category_normalizator[category].set_undefined_state(
                new_vertex)

    @staticmethod
    def _init_category_normalizator():
        return {
            EntityCategory.RESOURCE: ResourceNormalizator(),
            EntityCategory.ALARM: AlarmNormalizator()
        }

    def _load_state_configurations(self):
        states_plugins = {}
        erroneous_plugins = []

        files = file_utils.load_files(
            self.conf.entity_graph.states_plugins_dir, '.yaml')

        for file_name in files:
            try:
                full_path = self.conf.entity_graph.states_plugins_dir + '/' \
                    + file_name
                states, priorities = \
                    self._retrieve_states_and_priorities_from_file(full_path)
                states_plugins[os.path.splitext(file_name)[0]] = {
                    self.STATES: states,
                    self.PRIORITIES: priorities
                }
            except Exception as e:
                LOG.exception("Exception: %s", e)
                plugin = os.path.splitext(file_name)[0]
                LOG.error('erroneous plugins is %s',
                          erroneous_plugins.append(plugin))

        self._is_all_plugins_states_exists(
            [key for key in states_plugins.keys()],
            erroneous_plugins)

        return states_plugins

    def _retrieve_states_and_priorities_from_file(self, full_path):
        states = {}
        priorities = {}
        config = file_utils.load_yaml_file(full_path, with_exception=True)
        category = config['category']

        for item in config['states']:
            normalized_state = item['normalized state']

            # original to normalized state
            normalized_state_name = normalized_state['name']
            for original_state in normalized_state['original states']:
                states[original_state['name'].upper()] = normalized_state_name

            self._add_default_states(states, priorities, category)

            # normalized state priority
            priorities[normalized_state_name] = \
                int(normalized_state['priority'])

        self.check_validity(category, states, priorities, full_path)

        return states, priorities

    def _add_default_states(self, states, priorities, category):
        default_states = self.category_normalizator[category].default_states()
        for state, priority in default_states:
            states[None] = state
            priorities[NormalizedResourceState.UNDEFINED] = priority

    def check_validity(self, category, states, priorities, full_path):
        important_states = \
            self.category_normalizator[category].important_states()
        if important_states.unknown not in priorities:
            raise ValueError('%s state is not defined in %s',
                             important_states.unknown, full_path)

        # check that all the normalized states exists
        state_class_instance = \
            self.category_normalizator[category].get_state_class_instance()
        normalized_states = StateManager._get_all_local_variables_of_class(
            state_class_instance)
        for key in priorities.keys():
            if key not in normalized_states:
                raise ValueError('Normalized state %s for %s is not in %s',
                                 key, full_path,
                                 state_class_instance.__class__.__name__)

    def _find_normalized_state_and_priority(self,
                                            new_vertex,
                                            graph_vertex,
                                            property_,
                                            category,
                                            plugin_name,
                                            is_normalized=False):
        state = self._get_updated_property(new_vertex,
                                           graph_vertex,
                                           property_)

        upper_state1 = state if not state else state.upper()

        normalized_state = upper_state1 if is_normalized else \
            self.normalize_state(category, plugin_name, upper_state1)

        state_priority = self.state_priority(plugin_name, normalized_state)

        return normalized_state, state_priority

    @staticmethod
    def _get_all_local_variables_of_class(class_instance):
        return [attr for attr in dir(class_instance) if not callable(attr) and
                not attr.startswith("__")]

    def _is_all_plugins_states_exists(self, states_plugins, error_plugins):
        plugin_types = self.conf.plugins.plugin_type
        all_state_loaded_plugins = states_plugins + error_plugins

        for plugin_type in plugin_types:
            if plugin_type not in all_state_loaded_plugins:
                LOG.error("No state configuration file for: %s", plugin_type)

    @staticmethod
    def _get_updated_property(new_vertex, graph_vertex, prop):
        if new_vertex and prop in new_vertex.properties:
            return new_vertex[prop]
        elif graph_vertex and prop in graph_vertex.properties:
            return graph_vertex[prop]

        return None
