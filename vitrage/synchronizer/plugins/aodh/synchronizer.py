# Copyright 2016 - Alcatel-Lucent
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,  software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND,  either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo_log import log

from vitrage import clients
from vitrage.synchronizer.plugins.aodh.properties import AodhProperties \
    as AodhProps
from vitrage.synchronizer.plugins.aodh.properties import AodhState
from vitrage.synchronizer.plugins.base.alarm.synchronizer \
    import BaseAlarmSynchronizer

LOG = log.getLogger(__name__)
AODH = 'aodh'


class AodhSynchronizer(BaseAlarmSynchronizer):
    def __init__(self, conf):
        super(AodhSynchronizer, self).__init__()
        self.client = clients.ceilometer_client(conf)

    def _sync_type(self):
        return AODH

    def _alarm_key(self, alarm):
        return alarm[AodhProps.NAME]

    def _get_alarms(self):
        return []
        # TODO(iafek): enable the code below

        # try:
        #     aodh_alarms = self.client.alarms.list()
        #     return [_convert_alarm(alarm)
        #             for alarm in aodh_alarms]
        # except Exception:
        #     LOG.error("Exception: %s", traceback.print_exc())
        #     return []

    def _is_erroneous(self, alarm):
        return alarm and alarm[AodhProps.STATE] != AodhState.OK

    def _status_changed(self, alarm1, alarm2):
        return alarm1 and alarm2 and \
            not alarm1[AodhProps.STATE] == alarm2[AodhProps.STATE]

    def _is_valid(self, alarm):
        return True

    @staticmethod
    def _convert_event_alarm(alarm):
        converted_alarm = AodhSynchronizer._convert_base_alarm(alarm)
        event_type, resource_id = \
            AodhSynchronizer._parse_event_rule(alarm.event_rule)
        converted_alarm[AodhProps.EVENT_TYPE] = event_type
        converted_alarm[AodhProps.RESOURCE_ID] = resource_id
        return converted_alarm

    @staticmethod
    def _convert_threshold_alarm(alarm):
        converted_alarm = AodhSynchronizer._convert_base_alarm(alarm)
        converted_alarm[AodhProps.STATE_TIMESTAMP] = alarm.state_timestamp
        converted_alarm[AodhProps.RESOURCE_ID] = \
            AodhSynchronizer._parse_threshold_rule(alarm.threshold_rule)
        return converted_alarm

    @staticmethod
    def _convert_base_alarm(alarm):
        # TODO(iafek): what if the alarm state is 'insufficient data'

        return {
            AodhProps.DESCRIPTION: alarm.description,
            AodhProps.ENABLED: alarm.enabled,
            AodhProps.ALARM_ID: alarm.alarm_id,
            AodhProps.NAME: alarm.name,
            AodhProps.PROJECT_ID: alarm.project_id,
            AodhProps.REPEAT_ACTIONS: alarm.repeat_actions,
            AodhProps.SEVERITY: alarm.severity,
            AodhProps.STATE: alarm.state,
            AodhProps.TIMESTAMP: alarm.timestamp,
            AodhProps.TYPE: alarm.type
        }

    @staticmethod
    def _parse_event_rule(rule):
        event_type = rule[AodhProps.EVENT_TYPE]
        resource_id = \
            AodhSynchronizer._parse_resource_id(rule[AodhProps.QUERY])
        return event_type, resource_id

    @staticmethod
    def _parse_threshold_rule(rule):
        return AodhSynchronizer._parse_resource_id(rule[AodhProps.QUERY])

    @staticmethod
    def _parse_resource_id(query_fields):
        for query in query_fields:
            field = query['field']
            if field == AodhProps.RESOURCE_ID:
                return query['value']
            else:
                return None


def _convert_alarm(alarm):
    alarm_type = alarm.type
    if alarm_type == AodhProps.EVENT:
        return AodhSynchronizer._convert_event_alarm(alarm)
    elif alarm_type == AodhProps.THRESHOLD:
        return AodhSynchronizer._convert_threshold_alarm(alarm)
    else:
        LOG.info('Unsupported Aodh alarm of type %s' % alarm_type)
