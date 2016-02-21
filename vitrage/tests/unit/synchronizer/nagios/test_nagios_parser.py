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
from oslo_log import log as logging

from vitrage.synchronizer.plugins.nagios.parser import NagiosParser
from vitrage.synchronizer.plugins.nagios.properties import NagiosProperties
from vitrage.tests import base
from vitrage.tests.mocks import utils

LOG = logging.getLogger(__name__)


class NagiosParserTest(base.BaseTest):

    expected_service1 = {NagiosProperties.RESOURCE_NAME: 'compute-0-0.local',
                         NagiosProperties.SERVICE: 'CPU load',
                         NagiosProperties.STATUS: 'WARNING',
                         NagiosProperties.LAST_CHECK: '2016-02-09 13:05:32',
                         NagiosProperties.DURATION: ' 8d  2h 16m 33s',
                         NagiosProperties.ATTEMPT: '1/1',
                         NagiosProperties.STATUS_INFO:
                             u'high CPU load\xa0'}

    expected_service2 = {NagiosProperties.RESOURCE_NAME: 'compute-0-1.local',
                         NagiosProperties.SERVICE: 'check_load',
                         NagiosProperties.STATUS: 'CRITICAL',
                         NagiosProperties.LAST_CHECK: '2016-02-16 14:27:06',
                         NagiosProperties.DURATION: ' 1d  0h 54m 59s',
                         NagiosProperties.ATTEMPT: '1/1',
                         NagiosProperties.STATUS_INFO:
                             u'Critical Error\xa0'}

    expected_service3 = {NagiosProperties.RESOURCE_NAME: 'compute-0-0.local',
                         NagiosProperties.SERVICE: 'Disk IO SUMMARY',
                         NagiosProperties.STATUS: 'OK',
                         NagiosProperties.LAST_CHECK: '2016-02-17 15:21:22',
                         NagiosProperties.DURATION: '14d  1h 28m 34s',
                         NagiosProperties.ATTEMPT: '1/1',
                         NagiosProperties.STATUS_INFO:
                             u'OK - 0.00 B/sec read, 1.84 MB/sec write, '
                             u'IOs: 89.00/sec\xa0'}

    def setUp(self):
        super(NagiosParserTest, self).setUp()

    def test_template_loader(self):
        # Setup
        fp = open(utils.get_resources_dir() + '/nagios/nagios-mock.html')
        nagios_html = fp.read()

        # Action
        nagios_services = NagiosParser().parse(nagios_html)

        # Test assertions
        self.assertTrue(nagios_services)
        self._assert_contains(nagios_services, self.expected_service1)
        self._assert_contains(nagios_services, self.expected_service2)
        self._assert_contains(nagios_services, self.expected_service3)

    def _assert_contains(self, services, expected_service):
        for service in services:
            if service[NagiosProperties.RESOURCE_NAME] == \
                    expected_service[NagiosProperties.RESOURCE_NAME] and \
                    service[NagiosProperties.SERVICE] == \
                    expected_service[NagiosProperties.SERVICE]:
                self._assert_expected_service(expected_service, service)
                return

        self.fail("service not found: %(resource_name)s %(service_name)s" %
                  {'resource_name':
                   expected_service[NagiosProperties.RESOURCE_NAME],
                   'service_name':
                   expected_service[NagiosProperties.SERVICE]})

    def _assert_expected_service(self, expected_service, service):
        for key, value in expected_service.items():
            self.assertEqual(value, service[key], 'wrong value for ' + key)
