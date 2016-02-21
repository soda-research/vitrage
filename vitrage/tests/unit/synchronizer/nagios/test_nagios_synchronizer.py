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

from vitrage.synchronizer.plugins.nagios.properties import NagiosProperties \
    as NagiosProps
from vitrage.tests.unit.synchronizer.nagios.nagios_base_test \
    import NagiosBaseTest
from vitrage.tests.unit.synchronizer.nagios.synchronizer_with_mock_data \
    import NagiosSynchronizerWithMockData

LOG = logging.getLogger(__name__)


class NagiosSynchronizerTest(NagiosBaseTest):

    def setUp(self):
        super(NagiosSynchronizerTest, self).setUp()
        self.conf = cfg.ConfigOpts()

    def test_get_all(self):
        """Check get_all functionality.

        Check the logic of which tests are returned: tests that are not OK,
        or tests that were changed from not-OK to OK
        """

        # Setup
        nagios_synchronizer = NagiosSynchronizerWithMockData(self.conf)

        # Action
        service_data1 = {NagiosProps.RESOURCE_NAME: 'compute-0',
                         NagiosProps.SERVICE: 'CPU utilization',
                         NagiosProps.STATUS: 'OK'}
        service_data2 = {NagiosProps.RESOURCE_NAME: 'compute-1',
                         NagiosProps.SERVICE: 'CPU utilization',
                         NagiosProps.STATUS: 'OK'}
        service_data3 = {NagiosProps.RESOURCE_NAME: 'compute-1',
                         NagiosProps.SERVICE: 'Uptime',
                         NagiosProps.STATUS: 'OK'}

        nagios_synchronizer.set_service_datas([service_data1,
                                               service_data2,
                                               service_data3])

        services = nagios_synchronizer._get_services()

        # Test assertions
        # Services with status OK should not be returned
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(0, len(services))

    # Action
        service_data1 = {NagiosProps.RESOURCE_NAME: 'compute-0',
                         NagiosProps.SERVICE: 'CPU utilization',
                         NagiosProps.STATUS: 'WARNING'}
        service_data2 = {NagiosProps.RESOURCE_NAME: 'compute-1',
                         NagiosProps.SERVICE: 'CPU utilization',
                         NagiosProps.STATUS: 'OK'}
        service_data3 = {NagiosProps.RESOURCE_NAME: 'compute-1',
                         NagiosProps.SERVICE: 'Uptime',
                         NagiosProps.STATUS: 'OK'}

        nagios_synchronizer.set_service_datas([service_data1,
                                               service_data2,
                                               service_data3])

        services = nagios_synchronizer._get_services()

        # Test assertions
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(1, len(services))
        self._assert_contains(service_data1, services)

        # Action
        service_data1 = {NagiosProps.RESOURCE_NAME: 'compute-0',
                         NagiosProps.SERVICE: 'CPU utilization',
                         NagiosProps.STATUS: 'CRITICAL'}
        service_data2 = {NagiosProps.RESOURCE_NAME: 'compute-1',
                         NagiosProps.SERVICE: 'CPU utilization',
                         NagiosProps.STATUS: 'WARNING'}
        service_data3 = {NagiosProps.RESOURCE_NAME: 'compute-1',
                         NagiosProps.SERVICE: 'Uptime',
                         NagiosProps.STATUS: 'OK'}

        nagios_synchronizer.set_service_datas([service_data1,
                                               service_data2,
                                               service_data3])

        services = nagios_synchronizer._get_services()

        # Test assertions
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(2, len(services))
        self._assert_contains(service_data1, services)
        self._assert_contains(service_data2, services)

        # Action
        service_data1 = {NagiosProps.RESOURCE_NAME: 'compute-0',
                         NagiosProps.SERVICE: 'CPU utilization',
                         NagiosProps.STATUS: 'OK'}
        service_data2 = {NagiosProps.RESOURCE_NAME: 'compute-1',
                         NagiosProps.SERVICE: 'CPU utilization',
                         NagiosProps.STATUS: 'OK'}
        service_data3 = {NagiosProps.RESOURCE_NAME: 'compute-1',
                         NagiosProps.SERVICE: 'Uptime',
                         NagiosProps.STATUS: 'OK'}

        nagios_synchronizer.set_service_datas([service_data1,
                                               service_data2,
                                               service_data3])

        services = nagios_synchronizer._get_services()

        # Test assertions
        # The services of service_data1/2 should be returned although their
        # status is OK, because they were not OK earlier
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(2, len(services))
        self._assert_contains(service_data1, services)
        self._assert_contains(service_data2, services)

        # Action
        services = nagios_synchronizer._get_services()

        # Test assertions
        # Calling get_services again should not return anything, since all
        # services are still OK
        self.assertIsNotNone(services, 'services is None')
        self.assertEqual(0, len(services))
