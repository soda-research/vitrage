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

from vitrage.entity_graph.states.resource_state import NormalizedResourceState
from vitrage.entity_graph.states.state_manager import StateManager
from vitrage.tests import base
from vitrage.tests.mocks import utils


class TestStateManager(base.BaseTest):

    OPTS = [
        cfg.StrOpt('states_plugins_dir',
                   default=utils.get_resources_dir() + '/states_plugins'),
    ]

    def setUp(self):
        super(TestStateManager, self).setUp()
        self.conf = cfg.ConfigOpts()
        self.conf.register_opts(self.OPTS, group='entity_graph')

    def test_load_state_plugins(self):
        # action
        StateManager(self.conf)

        # test assertions
        # TODO(Alexey): check that UNRECOGNIZED exists
        # TODO(Alexey): check that if UNRECOGNIZED is missing then it throws
        #               exception
        # TODO(Alexey): check that all of the state plugins configured exists
        # TODO(Alexey): check that if one of the state plugins is missing then
        #               it throws an exception

    def test_normalize_state(self):
        # setup
        state_manager = StateManager(self.conf)

        # action
        normalized_state = \
            state_manager.normalize_state('nova.instance', 'BUILDING')

        # test assertions
        self.assertEqual(NormalizedResourceState.TRANSIENT, normalized_state)

    def test_state_priority(self):
        # setup
        state_manager = StateManager(self.conf)

        # action
        state_priority = \
            state_manager.state_priority('nova.instance',
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
            'nova.instance', True)
        aggregated_state_nova_instance_2 = state_manager.aggregated_state(
            NormalizedResourceState.SUBOPTIMAL,
            NormalizedResourceState.SUSPENDED,
            'nova.instance', True)

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
            'ACTIVE', 'SUSPENDED', 'nova.instance')
        aggregated_state_nova_instance_2 = state_manager.aggregated_state(
            'SUSPENDED', 'ACTIVE', 'nova.instance')

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
            'ACTIVE', None, 'nova.instance')
        aggregated_state_nova_instance_2 = state_manager.aggregated_state(
            None, 'ACTIVE', 'nova.instance')
        aggregated_state_nova_instance_3 = state_manager.aggregated_state(
            None, None, 'nova.instance')

        # test assertions
        self.assertEqual(NormalizedResourceState.RUNNING,
                         aggregated_state_nova_instance_1)
        self.assertEqual(NormalizedResourceState.RUNNING,
                         aggregated_state_nova_instance_2)
        self.assertEqual(NormalizedResourceState.UNDEFINED,
                         aggregated_state_nova_instance_3)
