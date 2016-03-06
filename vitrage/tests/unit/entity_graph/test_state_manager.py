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

from vitrage.common.constants import EntityType

from vitrage.entity_graph.states.resource_state import NormalizedResourceState
from vitrage.entity_graph.states.state_manager import StateManager
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

        cfg.DictOpt('nagios',
                    default={
                        'synchronizer':
                            'vitrage.synchronizer.plugins.nagios.synchronizer',
                        'transformer': 'vitrage.synchronizer.plugins'
                                       '.nagios.transformer.NagiosTransformer',
                        'user': '',
                        'password': '',
                        'url': '',
                        'config_file': '/etc/vitrage/nagios_conf.yaml'},),

        cfg.DictOpt('nova.host',
                    default={
                        'synchronizer':
                            'vitrage.synchronizer.plugins.nova.host'
                            '.synchronizer',
                        'transformer': 'vitrage.synchronizer.plugins.nova'
                                       '.host.transformer.HostTransformer',
                        'user': '',
                        'password': '',
                        'url': '',
                        'version': '2.0',
                        'project': 'admin'},),

        cfg.DictOpt('nova.instance',
                    default={
                        'synchronizer':
                            'vitrage.synchronizer.plugins.nova.instance'
                            '.synchronizer',
                        'transformer':
                            'vitrage.synchronizer.plugins'
                            '.nova.instance.transformer.InstanceTransformer',
                        'user': '',
                        'password': '',
                        'url': '',
                        'version': '2.0',
                        'project': 'admin'},),

        cfg.DictOpt('nova.zone',
                    default={
                        'synchronizer':
                            'vitrage.synchronizer.plugins.nova.zone'
                            '.synchronizer',
                        'transformer': 'vitrage.synchronizer.plugins.nova'
                                       '.zone.transformer.ZoneTransformer',
                        'user': '',
                        'password': '',
                        'url': '',
                        'version': '2.0',
                        'project': 'admin'},),
    ]

    def setUp(self):
        super(TestStateManager, self).setUp()
        self.conf = cfg.ConfigOpts()
        self.conf.register_opts(self.ENTITY_GRAPH_OPTS, group='entity_graph')
        self.conf.register_opts(self.PLUGINS_OPTS,
                                group='synchronizer_plugins')

    def test_load_state_plugins_without_errors(self):
        # action
        state_manager = StateManager(self.conf)

        # test assertions
        self.assertEqual(len(self.conf.synchronizer_plugins.plugin_type),
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
            state_manager.normalize_state(EntityType.NOVA_INSTANCE, 'BUILDING')

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

    def test_aggregated_state_normalized(self):
        # setup
        state_manager = StateManager(self.conf)

        # action
        aggregated_state_nova_instance_1 = state_manager.aggregated_state(
            NormalizedResourceState.SUSPENDED,
            NormalizedResourceState.SUBOPTIMAL,
            EntityType.NOVA_INSTANCE, True)
        aggregated_state_nova_instance_2 = state_manager.aggregated_state(
            NormalizedResourceState.SUBOPTIMAL,
            NormalizedResourceState.SUSPENDED,
            EntityType.NOVA_INSTANCE, True)

        # test assertions
        self.assertEqual(NormalizedResourceState.SUSPENDED,
                         aggregated_state_nova_instance_1)
        self.assertEqual(NormalizedResourceState.SUSPENDED,
                         aggregated_state_nova_instance_2)

    def test_aggregated_state_not_normalized(self):
        # setup
        state_manager = StateManager(self.conf)

        # action
        aggregated_state_nova_instance_1 = state_manager.aggregated_state(
            'ACTIVE', 'SUSPENDED', EntityType.NOVA_INSTANCE)
        aggregated_state_nova_instance_2 = state_manager.aggregated_state(
            'SUSPENDED', 'ACTIVE', EntityType.NOVA_INSTANCE)

        # test assertions
        self.assertEqual(NormalizedResourceState.SUSPENDED,
                         aggregated_state_nova_instance_1)
        self.assertEqual(NormalizedResourceState.SUSPENDED,
                         aggregated_state_nova_instance_2)

    def test_aggregated_state_functionalities(self):
        # setup
        state_manager = StateManager(self.conf)

        # action
        aggregated_state_nova_instance_1 = state_manager.aggregated_state(
            'ACTIVE', None, EntityType.NOVA_INSTANCE)
        aggregated_state_nova_instance_2 = state_manager.aggregated_state(
            None, 'ACTIVE', EntityType.NOVA_INSTANCE)
        aggregated_state_nova_instance_3 = state_manager.aggregated_state(
            None, None, EntityType.NOVA_INSTANCE)

        # test assertions
        self.assertEqual(NormalizedResourceState.RUNNING,
                         aggregated_state_nova_instance_1)
        self.assertEqual(NormalizedResourceState.RUNNING,
                         aggregated_state_nova_instance_2)
        self.assertEqual(NormalizedResourceState.UNDEFINED,
                         aggregated_state_nova_instance_3)
