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
    VALUES = 'values'
    PRIORITIES = 'priorities'

    def __init__(self, conf):
        self.conf = conf
        self.category_normalizator = self._init_category_normalizator()
        self.datasources_state_confs = self._load_state_configurations()

    def normalize_state(self, category, datasource_name, state):
        upper_state = state if not state else state.upper()
        important_states = \
            self.category_normalizator[category].important_states()

        if datasource_name in self.datasources_state_confs:

            states_conf = self.datasources_state_confs[datasource_name]

            return states_conf[self.VALUES][upper_state] \
                if upper_state in states_conf[self.VALUES] \
                else states_conf[important_states.unknown]
        else:
            return important_states.undefined

    def state_priority(self, datasource_name, normalized_state):
        # no need to check if normalized_state exists, cause it exists for sure
        upper_state = normalized_state if not normalized_state else \
            normalized_state.upper()

        if datasource_name in self.datasources_state_confs:
            states_conf = self.datasources_state_confs[datasource_name]
            return states_conf[self.PRIORITIES][upper_state]
        else:
            # default UNDEFINED priority
            return 0

    def aggregated_state(self, new_vertex, graph_vertex, is_normalized=False):
        datasource_name = new_vertex[VProps.TYPE] if \
            VProps.TYPE in new_vertex.properties else \
            graph_vertex[VProps.TYPE]

        category = new_vertex[VProps.CATEGORY] if \
            VProps.CATEGORY in new_vertex.properties else \
            graph_vertex[VProps.CATEGORY]

        if datasource_name in self.datasources_state_confs:
            state_properties = \
                self.category_normalizator[category].state_properties()
            normalized_state, state_priority = \
                self._find_normalized_state_and_priority(new_vertex,
                                                         graph_vertex,
                                                         state_properties[0],
                                                         category,
                                                         datasource_name,
                                                         is_normalized)
            state_properties.pop(0)

            for property_ in state_properties:
                tmp_normalized_state, tmp_state_priority = \
                    self._find_normalized_state_and_priority(new_vertex,
                                                             graph_vertex,
                                                             property_,
                                                             category,
                                                             datasource_name,
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
        ok_datasources = {}
        erroneous_datasources = []

        files = file_utils.load_files(
            self.conf.entity_graph.datasources_values_dir, '.yaml')

        for file_name in files:
            try:
                full_path = self.conf.entity_graph.datasources_values_dir \
                    + '/' + file_name
                states, priorities = \
                    self._retrieve_states_and_priorities_from_file(full_path)
                ok_datasources[os.path.splitext(file_name)[0]] = {
                    self.VALUES: states,
                    self.PRIORITIES: priorities
                }
            except Exception as e:
                LOG.exception("Exception: %s", e)
                datasource = os.path.splitext(file_name)[0]
                LOG.error('erroneous data sources is %s',
                          erroneous_datasources.append(datasource))

        self._check_state_confs_exists(
            [key for key in ok_datasources.keys()],
            erroneous_datasources)

        return ok_datasources

    def _retrieve_states_and_priorities_from_file(self, full_path):
        states = {}
        priorities = {}
        config = file_utils.load_yaml_file(full_path, with_exception=True)
        category = config['category']

        for item in config[self.VALUES]:
            normalized_state = item['normalized value']

            # original to normalized value
            normalized_state_name = normalized_state['name']
            for original_state in normalized_state['original values']:
                states[original_state['name'].upper()] = normalized_state_name

            self._add_default_states(states, priorities, category)

            # normalized value priority
            priorities[normalized_state_name] = \
                int(normalized_state['priority'])

        self.check_validity(category, priorities, full_path)

        return states, priorities

    def _add_default_states(self, states, priorities, category):
        default_values = self.category_normalizator[category].default_states()
        for state, priority in default_values:
            states[None] = state
            priorities[NormalizedResourceState.UNDEFINED] = priority

    def check_validity(self, category, priorities, full_path):
        important_states = \
            self.category_normalizator[category].important_states()
        if important_states.unknown not in priorities:
            raise ValueError('%s state is not defined in %s',
                             important_states.unknown, full_path)

        # check that all the normalized values exists
        state_class_instance = \
            self.category_normalizator[category].get_state_class_instance()
        normalized_values = StateManager._get_all_local_variables_of_class(
            state_class_instance)
        for key in priorities.keys():
            if key not in normalized_values:
                raise ValueError('normalized value %s for %s is not in %s',
                                 key, full_path,
                                 state_class_instance.__class__.__name__)

    def _find_normalized_state_and_priority(self,
                                            new_vertex,
                                            graph_vertex,
                                            property_,
                                            category,
                                            datasource_name,
                                            is_normalized=False):
        state = self._get_updated_property(new_vertex,
                                           graph_vertex,
                                           property_)

        upper_state1 = state if not state else state.upper()

        normalized_state = upper_state1 if is_normalized else \
            self.normalize_state(category, datasource_name, upper_state1)

        state_priority = self.state_priority(datasource_name,
                                             normalized_state)

        return normalized_state, state_priority

    @staticmethod
    def _get_all_local_variables_of_class(class_instance):
        return [attr for attr in dir(class_instance) if not callable(attr) and
                not attr.startswith("__")]

    def _check_state_confs_exists(self,
                                  ok_datasources,
                                  error_datasources):

        datasource_types = self.conf.datasources.types
        datasources_with_state_conf = ok_datasources + error_datasources

        for datasource_type in datasource_types:
            if datasource_type not in datasources_with_state_conf:
                LOG.info("No state configuration file for: %s",
                         datasource_type)

    @staticmethod
    def _get_updated_property(new_vertex, graph_vertex, prop):
        if new_vertex and prop in new_vertex.properties:
            return new_vertex[prop]
        elif graph_vertex and prop in graph_vertex.properties:
            return graph_vertex[prop]

        return None
