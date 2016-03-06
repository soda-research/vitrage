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
from vitrage.synchronizer.plugins.nagios.transformer import \
    NagiosTransformer
from vitrage.synchronizer.plugins.nova.host.transformer import \
    HostTransformer
from vitrage.synchronizer.plugins.nova.instance.transformer import \
    InstanceTransformer
from vitrage.synchronizer.plugins.nova.zone.transformer import \
    ZoneTransformer
from vitrage.synchronizer.plugins.static_physical.transformer import \
    StaticPhysicalTransformer
from vitrage.tests import base

LOG = logging.getLogger(__name__)


class TransformerManagerTest(base.BaseTest):

    OPTS = [

        cfg.ListOpt('plugin_type',
                    default=['nagios',
                             'nova.host',
                             'nova.instance',
                             'nova.zone',
                             'switch'],
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

        cfg.DictOpt('switch',
                    default={
                        'synchronizer':
                            'vitrage.synchronizer.plugins.static_physical'
                            '.synchronizer',
                        'transformer':
                            'vitrage.synchronizer.plugins.static_physical.'
                            'transformer.StaticPhysicalTransformer',
                        'dir': '/etc/vitrage/static_plugins'},),
    ]

    @classmethod
    def setUpClass(cls):
        cls.conf = cfg.ConfigOpts()
        cls.conf.register_opts(cls.OPTS, group='synchronizer_plugins')
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

    def test_transformer_registration_switch(self):
        self.assertIsInstance(self.manager.get_transformer
                              (EntityType.SWITCH), StaticPhysicalTransformer)
