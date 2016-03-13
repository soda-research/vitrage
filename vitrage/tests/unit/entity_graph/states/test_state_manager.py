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

from oslo_config import cfg

from vitrage.common.constants import EntityCategory
from vitrage.common.constants import EntityType
from vitrage.common.constants import VertexProperties as VProps
from vitrage.entity_graph.states.normalized_resource_state import \
    NormalizedResourceState
from vitrage.entity_graph.states.state_manager import StateManager
from vitrage.graph.utils import create_vertex
from vitrage.service import load_plugin
from vitrage.tests import base
from vitrage.tests.mocks import utils


class TestStateManager(base.BaseTest):

    ENTITY_GRAPH_OPTS = [
        cfg.StrOpt('states_plugins_dir',
                   default=utils.get_resources_dir() + '/states_plugins'),
    ]

    PLUGINS_OPTS = [
        cfg.ListOpt('plugin_type',
                    default=['nagios',
                             'nova.host',
                             'nova.instance',
                             'nova.zone'],
                    help='Names of supported synchronizer plugins'),
    ]

    @staticmethod
    def _load_plugins(conf):
        for plugin_name in conf.synchronizer_plugins.plugin_type:
            load_plugin(conf, plugin_name)

    def setUp(self):
        super(TestStateManager, self).setUp()
        self.conf = cfg.ConfigOpts()
        self.conf.register_opts(self.ENTITY_GRAPH_OPTS, group='entity_graph')
        self.conf.register_opts(self.PLUGINS_OPTS,
                                group='synchronizer_plugins')
        self._load_plugins(self.conf)

    def test_load_state_plugins_without_errors(self):
        # action
        state_manager = StateManager(self.conf)

        # test assertions
        self.assertEqual(len(self.conf.synchronizer_plugins.plugin_type) + 1,
                         len(state_manager.states_plugins))

    def test_load_state_plugins_with_errors(self):
        # setup
        entity_graph_opts = [
            cfg.StrOpt('states_plugins_dir',
                       default=utils.get_resources_dir() +
                       '/states_plugins/erroneous_states_plugins'),
        ]
        conf = cfg.ConfigOpts()
        conf.register_opts(entity_graph_opts, group='entity_graph')
        conf.register_opts(self.PLUGINS_OPTS, group='synchronizer_plugins')
        self._load_plugins(conf)

        # action
        state_manager = StateManager(conf)

        # test assertions
        missing_states_plugins = 1
        erroneous_states_plugins = 2
        num_valid_plugins = len(state_manager.states_plugins) + \
            missing_states_plugins + erroneous_states_plugins
        self.assertEqual(len(conf.synchronizer_plugins.plugin_type),
                         num_valid_plugins)

    def test_normalize_state(self):
        # setup
        state_manager = StateManager(self.conf)

        # action
        normalized_state = \
            state_manager.normalize_state(EntityCategory.RESOURCE,
                                          EntityType.NOVA_INSTANCE,
                                          'BUILDING')

        # test assertions
        self.assertEqual(NormalizedResourceState.TRANSIENT, normalized_state)

    def test_state_priority(self):
        # setup
        state_manager = StateManager(self.conf)

        # action
        state_priority = \
            state_manager.state_priority(EntityType.NOVA_INSTANCE,
                                         NormalizedResourceState.RUNNING)

        # test assertions
        self.assertEqual(10, state_priority)

    def test_aggregated_state_not_normalized(self):
        # setup
        state_manager = StateManager(self.conf)
        metadata1 = {VProps.VITRAGE_STATE: 'SUSPENDED'}
        new_vertex1 = create_vertex('12345',
                                    entity_state='ACTIVE',
                                    entity_category=EntityCategory.RESOURCE,
                                    entity_type=EntityType.NOVA_INSTANCE,
                                    metadata=metadata1)
        metadata2 = {VProps.VITRAGE_STATE: 'ACTIVE'}
        new_vertex2 = create_vertex('23456',
                                    entity_state='SUSPENDED',
                                    entity_category=EntityCategory.RESOURCE,
                                    entity_type=EntityType.NOVA_INSTANCE,
                                    metadata=metadata2)

        # action
        state_manager.aggregated_state(new_vertex1, None)
        state_manager.aggregated_state(new_vertex2, None)

        # test assertions
        self.assertEqual(NormalizedResourceState.SUSPENDED,
                         new_vertex1[VProps.AGGREGATED_STATE])
        self.assertEqual(NormalizedResourceState.SUSPENDED,
                         new_vertex2[VProps.AGGREGATED_STATE])

    def test_aggregated_state_functionalities(self):
        # setup
        state_manager = StateManager(self.conf)
        new_vertex1 = create_vertex('12345',
                                    entity_state='ACTIVE',
                                    entity_category=EntityCategory.RESOURCE,
                                    entity_type=EntityType.NOVA_INSTANCE)
        metadata2 = {VProps.VITRAGE_STATE: 'SUBOPTIMAL'}
        new_vertex2 = create_vertex('23456',
                                    entity_category=EntityCategory.RESOURCE,
                                    entity_type=EntityType.NOVA_INSTANCE,
                                    metadata=metadata2)
        new_vertex3 = create_vertex('34567',
                                    entity_category=EntityCategory.RESOURCE,
                                    entity_type=EntityType.NOVA_INSTANCE)
        graph_vertex3 = create_vertex('45678',
                                      entity_category=EntityCategory.RESOURCE,
                                      entity_type=EntityType.NOVA_INSTANCE)

        # action
        state_manager.aggregated_state(new_vertex1,
                                       None)
        state_manager.aggregated_state(new_vertex2,
                                       None)
        state_manager.aggregated_state(new_vertex3,
                                       graph_vertex3)

        # test assertions
        self.assertEqual(NormalizedResourceState.RUNNING,
                         new_vertex1[VProps.AGGREGATED_STATE])
        self.assertEqual(NormalizedResourceState.SUBOPTIMAL,
                         new_vertex2[VProps.AGGREGATED_STATE])
        self.assertEqual(NormalizedResourceState.UNDEFINED,
                         new_vertex3[VProps.AGGREGATED_STATE])
