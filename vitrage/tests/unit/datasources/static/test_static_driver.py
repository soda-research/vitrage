# Copyright 2016 - Nokia, ZTE
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
from oslo_log import log as logging

from vitrage.common.constants import EventAction
from vitrage.common.constants import SyncMode
from vitrage.datasources.static import driver
from vitrage.datasources.static import STATIC_DATASOURCE
from vitrage.tests import base
from vitrage.tests.mocks import utils


LOG = logging.getLogger(__name__)


class TestStaticDriver(base.BaseTest):

    OPTS = [
        cfg.StrOpt('transformer',
                   default='vitrage.datasources.static.transformer.'
                           'StaticTransformer'),
        cfg.StrOpt('driver',
                   default='vitrage.datasources.static.driver.'
                           'StaticDriver'),
        cfg.IntOpt('changes_interval',
                   default=30,
                   min=30,
                   help='interval between checking changes in the '
                        'configuration files of the static datasources'),
        cfg.StrOpt('directory',
                   default=utils.get_resources_dir() + '/static_datasources')
    ]

    CHANGES_OPTS = [
        cfg.StrOpt('transformer',
                   default='vitrage.datasources.static.transformer.'
                           'StaticTransformer'),
        cfg.StrOpt('driver',
                   default='vitrage.datasources.static.driver.'
                           'StaticDriver'),
        cfg.IntOpt('changes_interval',
                   default=30,
                   min=30,
                   help='interval between checking changes in the static '
                        'datasources'),
        cfg.StrOpt('directory',
                   default=utils.get_resources_dir() +
                   '/static_datasources/changes_datasources'),
    ]

    # noinspection PyAttributeOutsideInit,PyPep8Naming
    @classmethod
    def setUpClass(cls):
        cls.conf = cfg.ConfigOpts()
        cls.conf.register_opts(cls.OPTS, group=STATIC_DATASOURCE)
        cls.static_driver = driver.StaticDriver(cls.conf)

    def test_get_all(self):
        # Action
        static_entities = self.static_driver.get_all(SyncMode.UPDATE)

        # Test assertions
        self.assertEqual(0, len(static_entities))

    # noinspection PyAttributeOutsideInit
    def test_get_changes(self):
        # Setup
        entities = self.static_driver.get_all(SyncMode.UPDATE)
        self.assertEqual(0, len(entities))

        self.conf = cfg.ConfigOpts()
        self.conf.register_opts(self.CHANGES_OPTS,
                                group=STATIC_DATASOURCE)
        self.static_driver.cfg = self.conf

        # Action
        changes = self.static_driver.get_changes(
            EventAction.UPDATE_ENTITY)

        # Test Assertions
        self.assertEqual(0, len(changes))
