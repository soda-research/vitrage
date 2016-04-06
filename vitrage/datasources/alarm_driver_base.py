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

from oslo_log import log

from vitrage.datasources.driver_base import DriverBase

LOG = log.getLogger(__name__)


class AlarmDriverBase(DriverBase):
    def __init__(self):
        super(DriverBase, self).__init__()
        self.cache = dict()

    def _sync_type(self):
        """Return the type of the plugin """
        pass

    def _alarm_key(self, alarm):
        """Return a unique key of the alarm, to identify it in the cache """
        pass

    def _get_alarms(self):
        """Return the list of alarms of this plugin """
        pass

    def _enrich_alarms(self, alarms):
        """Optionally add more data to the alarms

        :param alarms: list of alarms to be enriched
        :return:
        """
        pass

    def _is_erroneous(self, alarm):
        """Check if the state of the alarm is erroneous

        :param alarm:
        :return: True/False based on the alarm state
        """
        pass

    def _status_changed(self, alarm1, alarm2):
        """Check if the status of the two alarms is different

        :param alarm1:
        :param alarm2:
        :return: True/False based on the alarms states
        """
        pass

    def _is_valid(self, alarm):
        """Check if the alarm is valid

        :param alarm: an alarm to check
        :return: True/False
        """
        pass

    def get_all(self, sync_mode):
        return self.make_pickleable(self._get_all_alarms(),
                                    self._sync_type(),
                                    sync_mode)

    def get_changes(self, sync_mode):
        return self.make_pickleable(self._get_changed_alarms(),
                                    self._sync_type(),
                                    sync_mode)

    def _get_all_alarms(self):
        alarms = self._get_alarms()
        self._enrich_alarms(alarms)
        return self._filter_and_cache_alarms(
            alarms,
            AlarmDriverBase._filter_get_all)

    def _get_changed_alarms(self):
        alarms = self._get_alarms()
        self._enrich_alarms(alarms)
        return self._filter_and_cache_alarms(
            alarms,
            AlarmDriverBase._filter_get_changes)

    def _filter_and_cache_alarms(self, alarms, filter_):
        alarms_to_update = []

        for alarm in alarms:
            alarm_key = self._alarm_key(alarm)
            old_alarm = self.cache.get(alarm_key, None)

            if filter_(self, alarm, old_alarm):
                alarms_to_update.append(alarm)

            self.cache[alarm_key] = alarm

        return alarms_to_update

    def _filter_get_all(self, alarm, old_alarm):
        return alarm \
            if self._is_valid(alarm) and \
            (self._is_erroneous(alarm) or self._is_erroneous(old_alarm)) \
            else None

    def _filter_get_changes(self, alarm, old_alarm):
        if not self._is_valid(alarm):
            return None
        if self._status_changed(alarm, old_alarm):
            return alarm
        elif not old_alarm and self._is_erroneous(alarm):
            return alarm
        else:
            return None
