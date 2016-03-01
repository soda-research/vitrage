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

from oslo_config import cfg
from oslo_log import log as logging

from vitrage.common.constants import EntityType
from vitrage.common.constants import EventAction
from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common.constants import SyncMode
from vitrage.common.constants import VertexProperties as VProps
from vitrage.common import file_utils
from vitrage.synchronizer.plugins.static_physical import synchronizer
from vitrage.tests import base
from vitrage.tests.mocks import utils


LOG = logging.getLogger(__name__)


class TestStaticPhysicalSynchronizer(base.BaseTest):

    OPTS = [
        cfg.DictOpt('switch',
                    default={
                        'synchronizer':
                            'vitrage.synchronizer.plugins.static_physical'
                            '.synchronizer.StaticPhysicalSynchronizer',
                        'transformer':
                            'vitrage.synchronizer.plugins.static_physical.'
                            'transformer.StaticPhysicalTransformer',
                        'dir': utils.get_resources_dir() + '/static_plugins'},)
    ]

    CHANGES_OPTS = [
        cfg.DictOpt('switch',
                    default={
                        'synchronizer':
                            'vitrage.synchronizer.plugins.static_physical'
                            '.synchronizer.StaticPhysicalSynchronizer',
                        'transformer':
                            'vitrage.synchronizer.plugins.static_physical.'
                            'transformer.StaticPhysicalTransformer',
                        'dir': utils.get_resources_dir() + '/static_plugins/'
                                                           'changes_plugins'},)
    ]

    def setUp(self):
        super(TestStaticPhysicalSynchronizer, self).setUp()
        self.conf = cfg.ConfigOpts()
        self.conf.register_opts(self.OPTS, group='synchronizer_plugins')
        self.static_physical_synchronizer = \
            synchronizer.StaticPhysicalSynchronizer(self.conf)

    def test_static_plugins_loader(self):
        # Setup
        total_static_plugins = \
            os.listdir(self.conf.synchronizer_plugins.switch['dir'])

        # Action
        static_configs = file_utils.load_yaml_files(
            self.conf.synchronizer_plugins.switch['dir'])

        # Test assertions
        # -1 is because there are 2 files and a folder in static_plugins_dir
        self.assertEqual(len(total_static_plugins) - 1, len(static_configs))

    def test_get_all(self):
        # Action
        static_entities = self.static_physical_synchronizer.get_all(
            SyncMode.UPDATE)

        # Test assertions
        self.assertEqual(5, len(static_entities))

    def test_get_changes(self):
        # Setup
        entities = self.static_physical_synchronizer.get_all(SyncMode.UPDATE)
        self.assertEqual(5, len(entities))

        self.conf = cfg.ConfigOpts()
        self.conf.register_opts(self.CHANGES_OPTS,
                                group='synchronizer_plugins')
        self.static_physical_synchronizer.cfg = self.conf

        # Action
        changes = self.static_physical_synchronizer.get_changes(
            EventAction.UPDATE_ENTITY)

        # Test Assertions
        status = any(change[VProps.TYPE] == EntityType.SWITCH and
                     change[VProps.ID] == '12345' for change in changes)
        self.assertEqual(False, status)

        status = any(change[VProps.TYPE] == EntityType.SWITCH and
                     change[VProps.ID] == '23456' and
                     change[SyncProps.EVENT_TYPE] == EventAction.DELETE_ENTITY
                     for change in changes)
        self.assertEqual(True, status)

        status = any(change[VProps.TYPE] == EntityType.SWITCH and
                     change[VProps.ID] == '34567' for change in changes)
        self.assertEqual(True, status)

        status = any(change[VProps.TYPE] == EntityType.SWITCH and
                     change[VProps.ID] == '45678' for change in changes)
        self.assertEqual(True, status)
        status = any(change[VProps.TYPE] == EntityType.SWITCH and
                     change[VProps.ID] == '56789' for change in changes)
        self.assertEqual(True, status)

        self.assertEqual(4, len(changes))

        # Action
        changes = self.static_physical_synchronizer.get_changes(
            EventAction.UPDATE_ENTITY)

        # Test Assertions
        self.assertEqual(0, len(changes))
