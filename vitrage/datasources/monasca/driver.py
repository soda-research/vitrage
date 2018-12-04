# Copyright 2018 Samsung Electronics
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_log import log

from vitrage.common.constants import DatasourceAction
from vitrage.common.constants import DatasourceProperties as DSProps
from vitrage.datasources.alarm_driver_base import AlarmDriverBase
from vitrage.datasources.monasca import MONASCA_DATASOURCE
from vitrage.datasources.monasca.properties import MonascaProperties as MProps
from vitrage.datasources.monasca.properties import MonascaAlarmStatuses as MAlarmStatuses
from vitrage.datasources.transformer_base import extract_field_value
from vitrage import os_clients
from vitrage.utils import datetime as datetime_utils

LOG = log.getLogger(__name__)


class MonascaDriver(AlarmDriverBase):

    def __init__(self, conf):
        super(MonascaDriver, self).__init__()
        self.conf = conf
        self.__client = None
        self.__cached_entities = []

    @property
    def client(self):
        if not self.__client:
            self.__client = os_clients.monasca_client(self.conf)
        return self.__client

    def _vitrage_type(self):
        return MONASCA_DATASOURCE

    def _alarm_key(self, alarm):
        return alarm[MProps.ID]

    def _get_alarms(self):
        try:
            alarms = self.client.alarms.list()
            LOG.debug('Fetched Monasca alarms: %s' % alarms)
            converted_alarms = [self._convert_alarm(alarm) for alarm in
                                alarms if alarm is not None]
            LOG.debug('Converted Monasca alarms: %s' % converted_alarms)
            return converted_alarms
        except Exception:
            LOG.exception("Failed to fetch Monasca alarms.")
        return []

    def _convert_alarm(self, alarm):
        resource_type, resource_id = self._extract_resource_id(alarm)
        return {
            MProps.ID: alarm[MProps.ID],
            MProps.NAME: extract_field_value(alarm, 'alarm_definition', 'name'),
            MProps.RESOURCE_TYPE: resource_type,
            MProps.RESOURCE_ID: resource_id,
            MProps.STATUS: alarm[MProps.STATUS],
            MProps.UPDATE_TIMESTAMP: alarm[MProps.UPDATE_TIMESTAMP]
        }

    def _enrich_alarms(self, alarms):
        pass

    def _is_erroneous(self, alarm):
        return alarm and alarm[MProps.STATUS] != MAlarmStatuses.OK

    def _status_changed(self, new_alarm, old_alarm):
        return new_alarm and old_alarm and \
            new_alarm[MProps.STATUS] != old_alarm[MProps.STATUS]

    def _is_valid(self, alarm):
        return alarm and alarm[MProps.RESOURCE_TYPE] is not None and \
            alarm[MProps.RESOURCE_ID] is not None

    def _extract_resource_id(self, alarm):
        resource_type = extract_field_value(alarm, 'metrics', 0, 'dimensions', 'resource_type')
        resource_id = extract_field_value(alarm, 'metrics', 0, 'dimensions', 'resource_id')
        return (resource_type, resource_id)

    @staticmethod
    def should_delete_outdated_entities():
        return True
