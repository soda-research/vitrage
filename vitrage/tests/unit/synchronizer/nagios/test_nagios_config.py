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
from oslo_log import log as logging

from vitrage.synchronizer.plugins.nagios.config import NagiosConfig
from vitrage.synchronizer.plugins.nagios.config import NagiosHostMapping
from vitrage.tests import base
from vitrage.tests.mocks import utils

LOG = logging.getLogger(__name__)


class TestNagiosConfig(base.BaseTest):

    OPTS = [
        cfg.StrOpt('nagios_config_file',
                   default=utils.get_resources_dir() +
                   '/nagios/nagios_conf.yaml',
                   help='Nagios configuation file'
                   ),
    ]

    # the rules match the ones in nagios_conf.yaml
    RULE_1 = NagiosHostMapping('compute-1', 'nova.host', 'compute-1')
    RULE_2 = NagiosHostMapping('compute-2', 'nova.host', 'host2')
    RULE_3 = NagiosHostMapping('compute-(.*)', 'nova.host', '${nagios_host}')
    RULE_4 = NagiosHostMapping('instance-(.*)',
                               'nova.instance',
                               '${nagios_host}')
    RULES = [RULE_1, RULE_2, RULE_3, RULE_4]

    NON_EXISTING_RULE_1 = NagiosHostMapping('X', 'nova.host', 'compute-1')
    NON_EXISTING_RULE_2 = NagiosHostMapping('compute-1', 'X', 'compute-1')
    NON_EXISTING_RULE_3 = NagiosHostMapping('compute-1', 'nova.host', 'X')
    NON_EXISTING_RULES = [NON_EXISTING_RULE_1,
                          NON_EXISTING_RULE_2,
                          NON_EXISTING_RULE_3]

    @classmethod
    def setUpClass(cls):
        cls.conf = cfg.ConfigOpts()
        cls.conf.register_opts(cls.OPTS, group='synchronizer_plugins')

    def test_nagios_configuration_loading(self):
        # Action
        nagios_conf = NagiosConfig(self.conf)

        # Test assertions
        rules = nagios_conf.rules
        self.assertIsNotNone(nagios_conf, "no nagios configuration loaded")
        self.assertEqual(len(self.RULES), len(rules))

        for expected_rule in self.RULES:
            self.assertTrue(TestNagiosConfig._check_contains(expected_rule,
                                                             rules))
        for expected_rule in self.NON_EXISTING_RULES:
            self.assertFalse(TestNagiosConfig._check_contains(expected_rule,
                                                              rules))

    @staticmethod
    def _check_contains(expected_rule, rules):
        for rule in rules:
            if TestNagiosConfig._assert_equals(expected_rule, rule):
                return True
        return False

    @staticmethod
    def _assert_equals(rule1, rule2):
        return rule1.nagios_host == rule2.nagios_host and \
            rule1.type == rule2.type and \
            rule1.name == rule2.name
