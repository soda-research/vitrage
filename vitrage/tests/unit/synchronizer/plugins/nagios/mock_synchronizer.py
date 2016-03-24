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

from vitrage.synchronizer.plugins.nagios.synchronizer import NagiosSynchronizer
from vitrage.tests.mocks import mock_syncronizer as mock_sync


class MockNagiosSynchronizer(NagiosSynchronizer):
    """A nagios synchronizer for tests.

    Instead of calling Nagios URL to get the data, it returns the data it
    is asked to
    """

    def __init__(self, conf):
        super(MockNagiosSynchronizer, self).__init__(conf)
        self.service_datas = None

    def set_service_datas(self, service_datas):
        self.service_datas = service_datas

    def _get_alarms(self):
        alarms = []
        for service_data in self.service_datas:
            generators = mock_sync.simple_nagios_alarm_generators(
                host_num=1,
                events_num=1,
                snap_vals=service_data)
            alarms.append(
                mock_sync.generate_sequential_events_list(generators)[0])

        return alarms
