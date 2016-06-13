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

from vitrage.common.constants import DatasourceProperties as DSProps
from vitrage.common.constants import EventAction
from vitrage.datasources.zabbix.properties import ZabbixProperties as \
    ZabbixProps
from vitrage.tests.mocks import utils
from vitrage.tests.unit.datasources.zabbix.mock_driver import MockZabbixDriver
from vitrage.tests.unit.datasources.zabbix.zabbix_base_test import \
    ZabbixBaseTest

LOG = logging.getLogger(__name__)


# noinspection PyProtectedMember
class ZabbixDriverTest(ZabbixBaseTest):

    OPTS = [
        cfg.StrOpt('config_file',
                   help='Zabbix configuration file',
                   default=utils.get_resources_dir()
                        + '/zabbix/zabbix_conf.yaml'),
    ]

    # noinspection PyPep8Naming
    @classmethod
    def setUpClass(cls):
        cls.conf = cfg.ConfigOpts()
        cls.conf.register_opts(cls.OPTS, group='zabbix')

    def test_severity_retrieval(self):
        # Setup
        zabbix_driver = MockZabbixDriver(self.conf)

        service_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                         ZabbixProps.DESCRIPTION: 'CPU utilization 1',
                         ZabbixProps.IS_ALARM_DISABLED: '1',
                         ZabbixProps.IS_ALARM_ON: '0',
                         ZabbixProps.SEVERITY: '1'}
        service_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                         ZabbixProps.DESCRIPTION: 'CPU utilization 2',
                         ZabbixProps.IS_ALARM_DISABLED: '1',
                         ZabbixProps.IS_ALARM_ON: '1',
                         ZabbixProps.SEVERITY: '1'}
        service_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                         ZabbixProps.DESCRIPTION: 'CPU utilization 3',
                         ZabbixProps.IS_ALARM_DISABLED: '0',
                         ZabbixProps.IS_ALARM_ON: '1',
                         ZabbixProps.SEVERITY: '1'}
        service_data4 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                         ZabbixProps.DESCRIPTION: 'CPU utilization 4',
                         ZabbixProps.IS_ALARM_DISABLED: '0',
                         ZabbixProps.IS_ALARM_ON: '0',
                         ZabbixProps.SEVERITY: '1'}

        zabbix_driver.set_service_datas([service_data1,
                                         service_data2,
                                         service_data3,
                                         service_data4])

        expected_service1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                             ZabbixProps.DESCRIPTION: 'CPU utilization 3',
                             ZabbixProps.SEVERITY: '1'}

        # Action
        services = zabbix_driver._get_all_alarms()

        # Test assertions
        # Services with status OK should not be returned
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(1, len(services))
        self._assert_contains(expected_service1, services)

    def test_get_all(self):
        """Check get_all functionality.

        Checks which tests are returned when performing get_all action:
        tests that their status is not OK, or tests that their status changed
        from not-OK to OK
        """

        # Setup
        zabbix_driver = MockZabbixDriver(self.conf)

        # Action
        service_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '-1'}
        service_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '-1'}
        service_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'Uptime',
                         ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_service_datas([service_data1,
                                         service_data2,
                                         service_data3])

        services = zabbix_driver._get_all_alarms()

        # Test assertions
        # Services with status OK should not be returned
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(0, len(services))

        # Action
        service_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '1'}
        service_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '-1'}
        service_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'Uptime',
                         ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_service_datas([service_data1,
                                         service_data2,
                                         service_data3])

        services = zabbix_driver._get_all_alarms()

        # Test assertions
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(1, len(services))
        self._assert_contains(service_data1, services)

        # Action
        service_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '4'}
        service_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '1'}
        service_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'Uptime',
                         ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_service_datas([service_data1,
                                         service_data2,
                                         service_data3])

        excpected_service1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                              ZabbixProps.DESCRIPTION: 'CPU utilization',
                              ZabbixProps.SEVERITY: '4'}
        excpected_service2 = {ZabbixProps.RESOURCE_NAME: 'host2',
                              ZabbixProps.DESCRIPTION: 'CPU utilization',
                              ZabbixProps.SEVERITY: '1'}

        services = zabbix_driver._get_all_alarms()

        # Test assertions
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(2, len(services))
        self._assert_contains(excpected_service1, services)
        self._assert_contains(excpected_service2, services)

        # Action
        service_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '-1'}
        service_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '-1'}
        service_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'Uptime',
                         ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_service_datas([service_data1,
                                         service_data2,
                                         service_data3])

        excpected_service1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                              ZabbixProps.DESCRIPTION: 'CPU utilization',
                              ZabbixProps.SEVERITY: '-1'}
        excpected_service2 = {ZabbixProps.RESOURCE_NAME: 'host2',
                              ZabbixProps.DESCRIPTION: 'CPU utilization',
                              ZabbixProps.SEVERITY: '-1'}

        services = zabbix_driver._get_all_alarms()

        # Test assertions
        # The services of service_data1/2 should be returned although their
        # status is OK, because they were not OK earlier
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(2, len(services))
        self._assert_contains(excpected_service1, services)
        self._assert_contains(excpected_service2, services)

        # Action
        services = zabbix_driver._get_all_alarms()

        # Test assertions
        # Calling get_services again should not return anything, since all
        # services are still OK
        self.assertIsNotNone(services, 'services is None')
        self.assertEqual(0, len(services))

    def test_get_changes(self):
        """Check get_changes functionality.

        Checks which tests are returned when performing get_changes action:
        Tests that their status was changed since the last call
        """

        # Setup
        zabbix_driver = MockZabbixDriver(self.conf)

        # Action
        service_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '-1'}
        service_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '-1'}
        service_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'Uptime',
                         ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_service_datas([service_data1,
                                         service_data2,
                                         service_data3])

        services = zabbix_driver._get_changed_alarms()

        # Test assertions
        # Services with status OK should not be returned
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(0, len(services))

        # Action
        service_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '1'}
        service_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '-1'}
        service_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'Uptime',
                         ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_service_datas([service_data1,
                                         service_data2,
                                         service_data3])

        services = zabbix_driver._get_changed_alarms()

        # Test assertions
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(1, len(services))
        self._assert_contains(service_data1, services)

        # Action
        service_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '4'}
        service_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '1'}
        service_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'Uptime',
                         ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_service_datas([service_data1,
                                         service_data2,
                                         service_data3])

        excpected_service1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                              ZabbixProps.DESCRIPTION: 'CPU utilization',
                              ZabbixProps.SEVERITY: '4'}
        excpected_service2 = {ZabbixProps.RESOURCE_NAME: 'host2',
                              ZabbixProps.DESCRIPTION: 'CPU utilization',
                              ZabbixProps.SEVERITY: '1'}

        services = zabbix_driver._get_changed_alarms()

        # Test assertions
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(2, len(services))
        self._assert_contains(excpected_service1, services)
        self._assert_contains(excpected_service2, services)

        # Action
        service_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '4'}
        service_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '4'}
        service_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'Uptime',
                         ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_service_datas([service_data1,
                                         service_data2,
                                         service_data3])

        excpected_service1 = {ZabbixProps.RESOURCE_NAME: 'host2',
                              ZabbixProps.DESCRIPTION: 'CPU utilization',
                              ZabbixProps.SEVERITY: '4'}

        services = zabbix_driver._get_changed_alarms()

        # Test assertions
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(1, len(services))
        self._assert_contains(excpected_service1, services)

        # Action
        service_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '-1'}
        service_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '-1'}
        service_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'Uptime',
                         ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_service_datas([service_data1,
                                         service_data2,
                                         service_data3])

        excpected_service1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                              ZabbixProps.DESCRIPTION: 'CPU utilization',
                              ZabbixProps.SEVERITY: '-1'}
        excpected_service2 = {ZabbixProps.RESOURCE_NAME: 'host2',
                              ZabbixProps.DESCRIPTION: 'CPU utilization',
                              ZabbixProps.SEVERITY: '-1'}

        services = zabbix_driver._get_changed_alarms()

        # Test assertions
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(2, len(services))
        self._assert_contains(excpected_service1, services)
        self._assert_contains(excpected_service2, services)

        # Action
        services = zabbix_driver._get_changed_alarms()

        # Test assertions
        self.assertIsNotNone(services, 'services is None')
        self.assertEqual(0, len(services))

    def test_get_changes_and_get_all(self):
        """Check get_changes and get_all functionalities """

        # Setup
        zabbix_driver = MockZabbixDriver(self.conf)

        # Action
        service_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '1'}
        service_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '-1'}
        service_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'Uptime',
                         ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_service_datas([service_data1,
                                         service_data2,
                                         service_data3])

        services = zabbix_driver._get_changed_alarms()

        # Test assertions
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(1, len(services))
        self._assert_contains(service_data1, services)

        # Action
        services = zabbix_driver._get_changed_alarms()

        # Test assertions
        # Calling get_changes for the second time should return nothing
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(0, len(services))

        # Action
        services = zabbix_driver._get_all_alarms()

        # Test assertions
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(1, len(services))
        self._assert_contains(service_data1, services)

        # Action
        services = zabbix_driver._get_all_alarms()

        # Test assertions
        # Calling get_all for the second time should return the same results
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(1, len(services))
        self._assert_contains(service_data1, services)

        # Action
        service_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '4'}
        service_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '1'}
        service_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'Uptime',
                         ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_service_datas([service_data1,
                                         service_data2,
                                         service_data3])

        excpected_service1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                              ZabbixProps.DESCRIPTION: 'CPU utilization',
                              ZabbixProps.SEVERITY: '4'}
        excpected_service2 = {ZabbixProps.RESOURCE_NAME: 'host2',
                              ZabbixProps.DESCRIPTION: 'CPU utilization',
                              ZabbixProps.SEVERITY: '1'}

        services = zabbix_driver._get_all_alarms()

        # Test assertions
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(2, len(services))
        self._assert_contains(excpected_service1, services)
        self._assert_contains(excpected_service2, services)

        # Action
        services = zabbix_driver._get_changed_alarms()

        # Test assertions
        # Calling get_changes after get_all should return nothing
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(0, len(services))

        # Action
        services = zabbix_driver._get_all_alarms()

        # Test assertions
        # Calling get_all for the second time should return the same results
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(2, len(services))
        self._assert_contains(excpected_service1, services)
        self._assert_contains(excpected_service2, services)

        # Action
        service_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '4'}
        service_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '4'}
        service_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'Uptime',
                         ZabbixProps.SEVERITY: '4'}

        zabbix_driver.set_service_datas([service_data1,
                                         service_data2,
                                         service_data3])

        excpected_service1 = {ZabbixProps.RESOURCE_NAME: 'host2',
                              ZabbixProps.DESCRIPTION: 'CPU utilization',
                              ZabbixProps.SEVERITY: '4'}
        excpected_service2 = {ZabbixProps.RESOURCE_NAME: 'host2',
                              ZabbixProps.DESCRIPTION: 'Uptime',
                              ZabbixProps.SEVERITY: '4'}

        services = zabbix_driver._get_changed_alarms()

        # Test assertions
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(2, len(services))
        self._assert_contains(excpected_service1, services)
        self._assert_contains(excpected_service2, services)

        # Action
        service_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '1'}
        service_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '4'}
        service_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'Uptime',
                         ZabbixProps.SEVERITY: '4'}

        zabbix_driver.set_service_datas([service_data1,
                                         service_data2,
                                         service_data3])

        expected_service1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                             ZabbixProps.DESCRIPTION: 'CPU utilization',
                             ZabbixProps.SEVERITY: '1'}

        services = zabbix_driver._get_changed_alarms()

        # Test assertions
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(1, len(services))
        self._assert_contains(expected_service1, services)

        excpected_service1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                              ZabbixProps.DESCRIPTION: 'CPU utilization',
                              ZabbixProps.SEVERITY: '1'}
        excpected_service2 = {ZabbixProps.RESOURCE_NAME: 'host2',
                              ZabbixProps.DESCRIPTION: 'CPU utilization',
                              ZabbixProps.SEVERITY: '4'}
        excpected_service3 = {ZabbixProps.RESOURCE_NAME: 'host2',
                              ZabbixProps.DESCRIPTION: 'Uptime',
                              ZabbixProps.SEVERITY: '4'}

        # Action
        services = zabbix_driver._get_changed_alarms()

        # Test assertions
        self.assertIsNotNone(services, 'services is None')
        self.assertEqual(0, len(services))

        # Action
        services = zabbix_driver._get_all_alarms()

        # Test assertions
        # Calling get_all for the second time should return the same results
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(3, len(services))
        self._assert_contains(excpected_service1, services)
        self._assert_contains(excpected_service2, services)
        self._assert_contains(excpected_service3, services)

    def test_delete_service(self):
        """Check get_all and get_changes with a deleted service"""

        # Setup
        zabbix_driver = MockZabbixDriver(self.conf)

        # Action
        service_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '1'}
        service_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '-1'}
        service_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'Uptime',
                         ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_service_datas([service_data1,
                                         service_data2,
                                         service_data3])

        services = zabbix_driver._get_all_alarms()

        # Test assertions
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(1, len(services))
        self._assert_contains(service_data1, services)

        # Action - delete a service that was OK
        service_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '1'}
        service_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_service_datas([service_data1, service_data2])

        services = zabbix_driver._get_all_alarms()

        # Test assertions
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(1, len(services))
        self._assert_contains(service_data1, services)

        # Action - delete a service that was not OK
        service_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_service_datas([service_data2])

        services = zabbix_driver._get_all_alarms()

        # Test assertions
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(1, len(services))
        self._assert_contains(service_data1, services)
        self.assertEqual(EventAction.DELETE_ENTITY,
                         services[0][DSProps.EVENT_TYPE])

        # Action - get changes, should not return the deleted alarm again
        services = zabbix_driver._get_changed_alarms()

        # Test assertions
        self.assertIsNotNone(services, 'services is None')
        self.assertEqual(0, len(services))

        # Action - "undelete" the service that was OK
        service_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '1'}
        service_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_service_datas([service_data1, service_data2])

        services = zabbix_driver._get_all_alarms()

        # Test assertions
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(1, len(services))
        self._assert_contains(service_data1, services)
        self.assertFalse(DSProps.EVENT_TYPE in services[0])

        # Action - delete a service that was not OK and call get_changes
        service_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                         ZabbixProps.DESCRIPTION: 'CPU utilization',
                         ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_service_datas([service_data2])

        services = zabbix_driver._get_changed_alarms()

        # Test assertions
        self.assertIsNotNone(services, 'No services returned')
        self.assertEqual(1, len(services))
        self._assert_contains(service_data1, services)
        self.assertEqual(EventAction.DELETE_ENTITY,
                         services[0][DSProps.EVENT_TYPE])
