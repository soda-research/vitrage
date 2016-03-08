# Copyright 2015 - Alcatel-Lucent
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

from vitrage.common.constants import EntityType
from vitrage.entity_graph.transformer_manager import TransformerManager
from vitrage.service import load_plugin
from vitrage.synchronizer.plugins.nagios.transformer import \
    NagiosTransformer
from vitrage.synchronizer.plugins.nova.host.transformer import \
    HostTransformer
from vitrage.synchronizer.plugins.nova.instance.transformer import \
    InstanceTransformer
from vitrage.synchronizer.plugins.nova.zone.transformer import \
    ZoneTransformer
from vitrage.tests import base

LOG = logging.getLogger(__name__)


class TransformerManagerTest(base.BaseTest):

    OPTS = [
        cfg.ListOpt('plugin_type',
                    default=['nagios',
                             'nova.host',
                             'nova.instance',
                             'nova.zone'],
                    help='Names of supported synchronizer plugins'),
    ]

    @classmethod
    def setUpClass(cls):
        cls.conf = cfg.ConfigOpts()
        cls.conf.register_opts(cls.OPTS, group='synchronizer_plugins')
        for plugin_name in cls.conf.synchronizer_plugins.plugin_type:
            load_plugin(cls.conf, plugin_name)
        cls.manager = TransformerManager(cls.conf)

    def test_transformer_registration_nagios(self):
            self.assertIsInstance(self.manager.get_transformer
                                  (EntityType.NAGIOS), NagiosTransformer)

    def test_transformer_registration_nova_host(self):
        self.assertIsInstance(self.manager.get_transformer
                              (EntityType.NOVA_HOST), HostTransformer)

    def test_transformer_registration_nova_instance(self):
        self.assertIsInstance(self.manager.get_transformer
                              (EntityType.NOVA_INSTANCE), InstanceTransformer)

    def test_transformer_registration_nova_zone(self):
        self.assertIsInstance(self.manager.get_transformer
                              (EntityType.NOVA_ZONE), ZoneTransformer)
