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

from vitrage.common import file_utils
from vitrage.tests import base
from vitrage.tests.mocks import utils


LOG = logging.getLogger(__name__)


class TestStaticPlugin(base.BaseTest):

    OPTS = [
        cfg.StrOpt('static_plugins_dir',
                   default=utils.get_resources_dir() + '/static_plugins',
                   ),
    ]

    def setUp(self):
        super(TestStaticPlugin, self).setUp()
        self.static_dir_path = utils.get_resources_dir() + '/static_plugins'
        self.conf = cfg.ConfigOpts()
        self.conf.register_opts(self.OPTS, group='synchronizer_plugins')

    def test_static_plugins_loader(self):
        # Setup
        total_static_plugins = os.listdir(self.static_dir_path)

        # Action
        static_configs = file_utils.load_yaml_files(
            self.conf.synchronizer_plugins.static_plugins_dir)

        # Test assertions
        self.assertEqual(len(total_static_plugins), len(static_configs))

    def test_number_of_entities(self):
        static_entities = []
        static_plugin_configs = file_utils.load_yaml_files(
            self.conf.synchronizer_plugins.static_plugins_dir)

        for config in static_plugin_configs:
            for entity in config['entities']:
                static_entities.append(entity)

        # Test assertions
        self.assertEqual(4, len(static_entities))
