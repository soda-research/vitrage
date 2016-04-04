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
from vitrage.common.constants import VertexProperties as VProps
from vitrage.entity_graph.states.normalized_resource_state import \
    NormalizedResourceState
from vitrage.entity_graph.states.state_manager import StateManager
from vitrage.graph.utils import create_vertex
from vitrage.service import load_plugin
from vitrage.synchronizer.plugins.nagios import NAGIOS_PLUGIN
from vitrage.synchronizer.plugins.nova.host import NOVA_HOST_PLUGIN
from vitrage.synchronizer.plugins.nova.instance import NOVA_INSTANCE_PLUGIN
from vitrage.synchronizer.plugins.nova.zone import NOVA_ZONE_PLUGIN
from vitrage.tests import base
from vitrage.tests.mocks import utils


class TestStateManager(base.BaseTest):

    ENTITY_GRAPH_OPTS = [
        cfg.StrOpt('states_plugins_dir',
                   default=utils.get_resources_dir() + '/states_plugins'),
    ]

    PLUGINS_OPTS = [
        cfg.ListOpt('plugin_type',
                    default=[NAGIOS_PLUGIN,
                             NOVA_HOST_PLUGIN,
                             NOVA_INSTANCE_PLUGIN,
                             NOVA_ZONE_PLUGIN],
                    help='Names of supported synchronizer plugins'),

        cfg.ListOpt('plugin_path',
                    default=['vitrage.synchronizer.plugins'],
                    help='base path for plugins')
    ]

    @staticmethod
    def _load_plugins(conf):
        for plugin_name in conf.plugins.plugin_type:
            load_plugin(conf, plugin_name, conf.plugins.plugin_path)

    # noinspection PyAttributeOutsideInit,PyPep8Naming
    @classmethod
    def setUpClass(cls):
        super(TestStateManager, cls).setUpClass()
        cls.conf = cfg.ConfigOpts()
        cls.conf.register_opts(cls.ENTITY_GRAPH_OPTS, group='entity_graph')
        cls.conf.register_opts(cls.PLUGINS_OPTS, group='plugins')
        cls._load_plugins(cls.conf)

    def test_load_state_plugins_without_errors(self):
        # action
        state_manager = StateManager(self.conf)

        # test assertions

        # Total plugins plus the evaluator which is not definable
        total_plugins = len(self.conf.plugins.plugin_type) + 1
        self.assertEqual(total_plugins, len(state_manager.states_plugins))

    def test_load_state_plugins_with_errors(self):
        # setup
        entity_graph_opts = [
            cfg.StrOpt('states_plugins_dir',
                       default=utils.get_resources_dir() +
                       '/states_plugins/erroneous_states_plugins'),
        ]
        conf = cfg.ConfigOpts()
        conf.register_opts(entity_graph_opts, group='entity_graph')
        conf.register_opts(self.PLUGINS_OPTS, group='plugins')
        self._load_plugins(conf)

        # action
        state_manager = StateManager(conf)

        # test assertions
        missing_states_plugins = 1
        erroneous_states_plugins = 2
        num_valid_plugins = len(state_manager.states_plugins) + \
            missing_states_plugins + erroneous_states_plugins
        self.assertEqual(len(conf.plugins.plugin_type), num_valid_plugins)

    def test_normalize_state(self):
        # setup
        state_manager = StateManager(self.conf)

        # action
        normalized_state = \
            state_manager.normalize_state(EntityCategory.RESOURCE,
                                          NOVA_INSTANCE_PLUGIN,
                                          'BUILDING')

        # test assertions
        self.assertEqual(NormalizedResourceState.TRANSIENT, normalized_state)

    def test_state_priority(self):
        # setup
        state_manager = StateManager(self.conf)

        # action
        state_priority = \
            state_manager.state_priority(NOVA_INSTANCE_PLUGIN,
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
                                    entity_type=NOVA_INSTANCE_PLUGIN,
                                    metadata=metadata1)
        metadata2 = {VProps.VITRAGE_STATE: 'ACTIVE'}
        new_vertex2 = create_vertex('23456',
                                    entity_state='SUSPENDED',
                                    entity_category=EntityCategory.RESOURCE,
                                    entity_type=NOVA_INSTANCE_PLUGIN,
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
                                    entity_type=NOVA_INSTANCE_PLUGIN)
        metadata2 = {VProps.VITRAGE_STATE: 'SUBOPTIMAL'}
        new_vertex2 = create_vertex('23456',
                                    entity_category=EntityCategory.RESOURCE,
                                    entity_type=NOVA_INSTANCE_PLUGIN,
                                    metadata=metadata2)
        new_vertex3 = create_vertex('34567',
                                    entity_category=EntityCategory.RESOURCE,
                                    entity_type=NOVA_INSTANCE_PLUGIN)
        graph_vertex3 = create_vertex('45678',
                                      entity_category=EntityCategory.RESOURCE,
                                      entity_type=NOVA_INSTANCE_PLUGIN)

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
