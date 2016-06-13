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

        alarm_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                       ZabbixProps.DESCRIPTION: 'CPU utilization 1',
                       ZabbixProps.IS_ALARM_DISABLED: '1',
                       ZabbixProps.IS_ALARM_ON: '0',
                       ZabbixProps.SEVERITY: '1'}
        alarm_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                       ZabbixProps.DESCRIPTION: 'CPU utilization 2',
                       ZabbixProps.IS_ALARM_DISABLED: '1',
                       ZabbixProps.IS_ALARM_ON: '1',
                       ZabbixProps.SEVERITY: '1'}
        alarm_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                       ZabbixProps.DESCRIPTION: 'CPU utilization 3',
                       ZabbixProps.IS_ALARM_DISABLED: '0',
                       ZabbixProps.IS_ALARM_ON: '1',
                       ZabbixProps.SEVERITY: '1'}
        alarm_data4 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                       ZabbixProps.DESCRIPTION: 'CPU utilization 4',
                       ZabbixProps.IS_ALARM_DISABLED: '0',
                       ZabbixProps.IS_ALARM_ON: '0',
                       ZabbixProps.SEVERITY: '1'}

        zabbix_driver.set_alarm_datas([alarm_data1,
                                       alarm_data2,
                                       alarm_data3,
                                       alarm_data4])

        expected_alarm1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                           ZabbixProps.DESCRIPTION: 'CPU utilization 3',
                           ZabbixProps.SEVERITY: '1'}

        # Action
        alarms = zabbix_driver._get_all_alarms()

        # Test assertions
        # Services with status OK should not be returned
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(1, len(alarms))
        self._assert_contains(expected_alarm1, alarms)

    def test_get_all(self):
        """Check get_all functionality.

        Checks which tests are returned when performing get_all action:
        tests that their status is not OK, or tests that their status changed
        from not-OK to OK
        """

        # Setup
        zabbix_driver = MockZabbixDriver(self.conf)

        # Action
        alarm_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '-1'}
        alarm_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '-1'}
        alarm_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'Uptime',
                       ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_alarm_datas([alarm_data1,
                                       alarm_data2,
                                       alarm_data3])

        alarms = zabbix_driver._get_all_alarms()

        # Test assertions
        # Services with status OK should not be returned
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(0, len(alarms))

        # Action
        alarm_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '1'}
        alarm_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '-1'}
        alarm_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'Uptime',
                       ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_alarm_datas([alarm_data1,
                                       alarm_data2,
                                       alarm_data3])

        alarms = zabbix_driver._get_all_alarms()

        # Test assertions
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(1, len(alarms))
        self._assert_contains(alarm_data1, alarms)

        # Action
        alarm_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '4'}
        alarm_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '1'}
        alarm_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'Uptime',
                       ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_alarm_datas([alarm_data1,
                                       alarm_data2,
                                       alarm_data3])

        excpected_alarm1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                            ZabbixProps.DESCRIPTION: 'CPU utilization',
                            ZabbixProps.SEVERITY: '4'}
        excpected_alarm2 = {ZabbixProps.RESOURCE_NAME: 'host2',
                            ZabbixProps.DESCRIPTION: 'CPU utilization',
                            ZabbixProps.SEVERITY: '1'}

        alarms = zabbix_driver._get_all_alarms()

        # Test assertions
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(2, len(alarms))
        self._assert_contains(excpected_alarm1, alarms)
        self._assert_contains(excpected_alarm2, alarms)

        # Action
        alarm_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '-1'}
        alarm_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '-1'}
        alarm_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'Uptime',
                       ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_alarm_datas([alarm_data1,
                                       alarm_data2,
                                       alarm_data3])

        excpected_alarm1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                            ZabbixProps.DESCRIPTION: 'CPU utilization',
                            ZabbixProps.SEVERITY: '-1'}
        excpected_alarm2 = {ZabbixProps.RESOURCE_NAME: 'host2',
                            ZabbixProps.DESCRIPTION: 'CPU utilization',
                            ZabbixProps.SEVERITY: '-1'}

        alarms = zabbix_driver._get_all_alarms()

        # Test assertions
        # The alarms of alarm_data1/2 should be returned although their
        # status is OK, because they were not OK earlier
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(2, len(alarms))
        self._assert_contains(excpected_alarm1, alarms)
        self._assert_contains(excpected_alarm2, alarms)

        # Action
        alarms = zabbix_driver._get_all_alarms()

        # Test assertions
        # Calling get_alarms again should not return anything, since all
        # alarms are still OK
        self.assertIsNotNone(alarms, 'alarms is None')
        self.assertEqual(0, len(alarms))

    def test_get_changes(self):
        """Check get_changes functionality.

        Checks which tests are returned when performing get_changes action:
        Tests that their status was changed since the last call
        """

        # Setup
        zabbix_driver = MockZabbixDriver(self.conf)

        # Action
        alarm_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '-1'}
        alarm_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '-1'}
        alarm_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'Uptime',
                       ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_alarm_datas([alarm_data1,
                                       alarm_data2,
                                       alarm_data3])

        alarms = zabbix_driver._get_changed_alarms()

        # Test assertions
        # Services with status OK should not be returned
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(0, len(alarms))

        # Action
        alarm_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '1'}
        alarm_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '-1'}
        alarm_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'Uptime',
                       ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_alarm_datas([alarm_data1,
                                       alarm_data2,
                                       alarm_data3])

        alarms = zabbix_driver._get_changed_alarms()

        # Test assertions
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(1, len(alarms))
        self._assert_contains(alarm_data1, alarms)

        # Action
        alarm_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '4'}
        alarm_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '1'}
        alarm_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'Uptime',
                       ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_alarm_datas([alarm_data1,
                                       alarm_data2,
                                       alarm_data3])

        excpected_alarm1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                            ZabbixProps.DESCRIPTION: 'CPU utilization',
                            ZabbixProps.SEVERITY: '4'}
        excpected_alarm2 = {ZabbixProps.RESOURCE_NAME: 'host2',
                            ZabbixProps.DESCRIPTION: 'CPU utilization',
                            ZabbixProps.SEVERITY: '1'}

        alarms = zabbix_driver._get_changed_alarms()

        # Test assertions
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(2, len(alarms))
        self._assert_contains(excpected_alarm1, alarms)
        self._assert_contains(excpected_alarm2, alarms)

        # Action
        alarm_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '4'}
        alarm_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '4'}
        alarm_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'Uptime',
                       ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_alarm_datas([alarm_data1,
                                       alarm_data2,
                                       alarm_data3])

        excpected_alarm1 = {ZabbixProps.RESOURCE_NAME: 'host2',
                            ZabbixProps.DESCRIPTION: 'CPU utilization',
                            ZabbixProps.SEVERITY: '4'}

        alarms = zabbix_driver._get_changed_alarms()

        # Test assertions
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(1, len(alarms))
        self._assert_contains(excpected_alarm1, alarms)

        # Action
        alarm_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '-1'}
        alarm_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '-1'}
        alarm_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'Uptime',
                       ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_alarm_datas([alarm_data1,
                                       alarm_data2,
                                       alarm_data3])

        excpected_alarm1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                            ZabbixProps.DESCRIPTION: 'CPU utilization',
                            ZabbixProps.SEVERITY: '-1'}
        excpected_alarm2 = {ZabbixProps.RESOURCE_NAME: 'host2',
                            ZabbixProps.DESCRIPTION: 'CPU utilization',
                            ZabbixProps.SEVERITY: '-1'}

        alarms = zabbix_driver._get_changed_alarms()

        # Test assertions
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(2, len(alarms))
        self._assert_contains(excpected_alarm1, alarms)
        self._assert_contains(excpected_alarm2, alarms)

        # Action
        alarms = zabbix_driver._get_changed_alarms()

        # Test assertions
        self.assertIsNotNone(alarms, 'alarms is None')
        self.assertEqual(0, len(alarms))

    def test_get_changes_and_get_all(self):
        """Check get_changes and get_all functionalities """

        # Setup
        zabbix_driver = MockZabbixDriver(self.conf)

        # Action
        alarm_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '1'}
        alarm_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '-1'}
        alarm_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'Uptime',
                       ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_alarm_datas([alarm_data1,
                                       alarm_data2,
                                       alarm_data3])

        alarms = zabbix_driver._get_changed_alarms()

        # Test assertions
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(1, len(alarms))
        self._assert_contains(alarm_data1, alarms)

        # Action
        alarms = zabbix_driver._get_changed_alarms()

        # Test assertions
        # Calling get_changes for the second time should return nothing
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(0, len(alarms))

        # Action
        alarms = zabbix_driver._get_all_alarms()

        # Test assertions
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(1, len(alarms))
        self._assert_contains(alarm_data1, alarms)

        # Action
        alarms = zabbix_driver._get_all_alarms()

        # Test assertions
        # Calling get_all for the second time should return the same results
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(1, len(alarms))
        self._assert_contains(alarm_data1, alarms)

        # Action
        alarm_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '4'}
        alarm_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '1'}
        alarm_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'Uptime',
                       ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_alarm_datas([alarm_data1,
                                       alarm_data2,
                                       alarm_data3])

        excpected_alarm1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                            ZabbixProps.DESCRIPTION: 'CPU utilization',
                            ZabbixProps.SEVERITY: '4'}
        excpected_alarm2 = {ZabbixProps.RESOURCE_NAME: 'host2',
                            ZabbixProps.DESCRIPTION: 'CPU utilization',
                            ZabbixProps.SEVERITY: '1'}

        alarms = zabbix_driver._get_all_alarms()

        # Test assertions
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(2, len(alarms))
        self._assert_contains(excpected_alarm1, alarms)
        self._assert_contains(excpected_alarm2, alarms)

        # Action
        alarms = zabbix_driver._get_changed_alarms()

        # Test assertions
        # Calling get_changes after get_all should return nothing
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(0, len(alarms))

        # Action
        alarms = zabbix_driver._get_all_alarms()

        # Test assertions
        # Calling get_all for the second time should return the same results
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(2, len(alarms))
        self._assert_contains(excpected_alarm1, alarms)
        self._assert_contains(excpected_alarm2, alarms)

        # Action
        alarm_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '4'}
        alarm_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '4'}
        alarm_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'Uptime',
                       ZabbixProps.SEVERITY: '4'}

        zabbix_driver.set_alarm_datas([alarm_data1,
                                       alarm_data2,
                                       alarm_data3])

        excpected_alarm1 = {ZabbixProps.RESOURCE_NAME: 'host2',
                            ZabbixProps.DESCRIPTION: 'CPU utilization',
                            ZabbixProps.SEVERITY: '4'}
        excpected_alarm2 = {ZabbixProps.RESOURCE_NAME: 'host2',
                            ZabbixProps.DESCRIPTION: 'Uptime',
                            ZabbixProps.SEVERITY: '4'}

        alarms = zabbix_driver._get_changed_alarms()

        # Test assertions
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(2, len(alarms))
        self._assert_contains(excpected_alarm1, alarms)
        self._assert_contains(excpected_alarm2, alarms)

        # Action
        alarm_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '1'}
        alarm_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '4'}
        alarm_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'Uptime',
                       ZabbixProps.SEVERITY: '4'}

        zabbix_driver.set_alarm_datas([alarm_data1,
                                       alarm_data2,
                                       alarm_data3])

        expected_alarm1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                           ZabbixProps.DESCRIPTION: 'CPU utilization',
                           ZabbixProps.SEVERITY: '1'}

        alarms = zabbix_driver._get_changed_alarms()

        # Test assertions
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(1, len(alarms))
        self._assert_contains(expected_alarm1, alarms)

        excpected_alarm1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                            ZabbixProps.DESCRIPTION: 'CPU utilization',
                            ZabbixProps.SEVERITY: '1'}
        excpected_alarm2 = {ZabbixProps.RESOURCE_NAME: 'host2',
                            ZabbixProps.DESCRIPTION: 'CPU utilization',
                            ZabbixProps.SEVERITY: '4'}
        excpected_alarm3 = {ZabbixProps.RESOURCE_NAME: 'host2',
                            ZabbixProps.DESCRIPTION: 'Uptime',
                            ZabbixProps.SEVERITY: '4'}

        # Action
        alarms = zabbix_driver._get_changed_alarms()

        # Test assertions
        self.assertIsNotNone(alarms, 'alarms is None')
        self.assertEqual(0, len(alarms))

        # Action
        alarms = zabbix_driver._get_all_alarms()

        # Test assertions
        # Calling get_all for the second time should return the same results
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(3, len(alarms))
        self._assert_contains(excpected_alarm1, alarms)
        self._assert_contains(excpected_alarm2, alarms)
        self._assert_contains(excpected_alarm3, alarms)

    def test_delete_alarm(self):
        """Check get_all and get_changes with a deleted alarm"""

        # Setup
        zabbix_driver = MockZabbixDriver(self.conf)

        # Action
        alarm_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '1'}
        alarm_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '-1'}
        alarm_data3 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'Uptime',
                       ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_alarm_datas([alarm_data1,
                                       alarm_data2,
                                       alarm_data3])

        alarms = zabbix_driver._get_all_alarms()

        # Test assertions
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(1, len(alarms))
        self._assert_contains(alarm_data1, alarms)

        # Action - delete a alarm that was OK
        alarm_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '1'}
        alarm_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_alarm_datas([alarm_data1, alarm_data2])

        alarms = zabbix_driver._get_all_alarms()

        # Test assertions
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(1, len(alarms))
        self._assert_contains(alarm_data1, alarms)

        # Action - delete a alarm that was not OK
        alarm_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_alarm_datas([alarm_data2])

        alarms = zabbix_driver._get_all_alarms()

        # Test assertions
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(1, len(alarms))
        self._assert_contains(alarm_data1, alarms)
        self.assertEqual(EventAction.DELETE_ENTITY,
                         alarms[0][DSProps.EVENT_TYPE])

        # Action - get changes, should not return the deleted alarm again
        alarms = zabbix_driver._get_changed_alarms()

        # Test assertions
        self.assertIsNotNone(alarms, 'alarms is None')
        self.assertEqual(0, len(alarms))

        # Action - "undelete" the alarm that was OK
        alarm_data1 = {ZabbixProps.RESOURCE_NAME: 'compute-1',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '1'}
        alarm_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_alarm_datas([alarm_data1, alarm_data2])

        alarms = zabbix_driver._get_all_alarms()

        # Test assertions
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(1, len(alarms))
        self._assert_contains(alarm_data1, alarms)
        self.assertFalse(DSProps.EVENT_TYPE in alarms[0])

        # Action - delete a alarm that was not OK and call get_changes
        alarm_data2 = {ZabbixProps.RESOURCE_NAME: 'compute-2',
                       ZabbixProps.DESCRIPTION: 'CPU utilization',
                       ZabbixProps.SEVERITY: '-1'}

        zabbix_driver.set_alarm_datas([alarm_data2])

        alarms = zabbix_driver._get_changed_alarms()

        # Test assertions
        self.assertIsNotNone(alarms, 'No alarms returned')
        self.assertEqual(1, len(alarms))
        self._assert_contains(alarm_data1, alarms)
        self.assertEqual(EventAction.DELETE_ENTITY,
                         alarms[0][DSProps.EVENT_TYPE])
