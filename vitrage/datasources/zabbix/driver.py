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

from collections import namedtuple

from oslo_log import log
from pyzabbix import ZabbixAPI

from vitrage.common import file_utils
from vitrage.datasources.alarm_driver_base import AlarmDriverBase
from vitrage.datasources.zabbix.properties import ZabbixProperties \
    as ZabbixProps
from vitrage.datasources.zabbix.properties import ZabbixTriggerStatus
from vitrage.datasources.zabbix import ZABBIX_DATASOURCE

LOG = log.getLogger(__name__)


class ZabbixDriver(AlarmDriverBase):
    ServiceKey = namedtuple('ServiceKey', ['host_name', 'service'])

    def __init__(self, conf):
        super(ZabbixDriver, self).__init__()
        self.conf = conf
        self.configuration_mapping = self._configuration_mapping(conf)
        self.status_mapping = self._status_mapping()
        self.client = None

    def _sync_type(self):
        return ZABBIX_DATASOURCE

    def _alarm_key(self, alarm):
        return self.ServiceKey(host_name=alarm[ZabbixProps.RESOURCE_NAME],
                               service=alarm[ZabbixProps.DESCRIPTION])

    def _get_alarms(self):
        zabbix_user = self.conf.zabbix.user
        zabbix_password = self.conf.zabbix.password
        zabbix_url = self.conf.zabbix.url

        if not zabbix_user:
            LOG.warning('Zabbix user is not defined')
            return []

        if not zabbix_password:
            LOG.warning('Zabbix password is not defined')
            return []

        if not zabbix_url:
            LOG.warning('Zabbix url is not defined')
            return []

        if not self.client:
            self.client = ZabbixAPI(zabbix_url)
            self.client.login(zabbix_user, zabbix_password)

        alarms = []
        hosts = self.client.host.get()
        for host in hosts:
            if host[ZabbixProps.HOST] in self.configuration_mapping:
                self._get_triggers_per_host(host, alarms)

        return alarms

    def _enrich_alarms(self, alarms):
        for alarm in alarms:
            # based on zabbix configuration file, convert zabbix host name
            # to vitrage resource type and name
            zabbix_host = alarm[ZabbixProps.RESOURCE_NAME]
            vitrage_resource = self.configuration_mapping[zabbix_host]

            alarm[ZabbixProps.STATUS] = \
                self._get_status(alarm)
            alarm[ZabbixProps.RESOURCE_TYPE] = \
                vitrage_resource[ZabbixProps.RESOURCE_TYPE]
            alarm[ZabbixProps.RESOURCE_NAME] = \
                vitrage_resource[ZabbixProps.RESOURCE_NAME]

    def _is_erroneous(self, alarm):
        return alarm and alarm[ZabbixProps.STATUS] != ZabbixTriggerStatus.OK

    def _status_changed(self, alarm1, alarm2):
        return alarm1 and alarm2 and \
            not alarm1[ZabbixProps.STATUS] == alarm2[ZabbixProps.STATUS]

    def _is_valid(self, alarm):
        return alarm[ZabbixProps.RESOURCE_TYPE] is not None and \
            alarm[ZabbixProps.RESOURCE_NAME] is not None

    def _get_status(self, alarm):
        if alarm[ZabbixProps.IS_ALARM_DISABLED] == '1' or \
                alarm[ZabbixProps.IS_ALARM_ON] == '0':
            return ZabbixTriggerStatus.OK

        return self.status_mapping[alarm[ZabbixProps.SEVERITY]]

    @staticmethod
    def _status_mapping():
        return {
            '-1': ZabbixTriggerStatus.OK,
            '0': ZabbixTriggerStatus.NOT_CLASSIFIED,
            '1': ZabbixTriggerStatus.INFORMATION,
            '2': ZabbixTriggerStatus.WARNING,
            '3': ZabbixTriggerStatus.AVERAGE,
            '4': ZabbixTriggerStatus.HIGH,
            '5': ZabbixTriggerStatus.DISASTER
        }

    @staticmethod
    def _configuration_mapping(conf):
        try:
            zabbix_config_file = conf.zabbix['config_file']
            zabbix_config = file_utils.load_yaml_file(zabbix_config_file)
            zabbix_config_elements = zabbix_config['zabbix']

            mappings = {}
            for element_config in zabbix_config_elements:
                mappings[element_config['zabbix_host']] = {
                    ZabbixProps.RESOURCE_TYPE: element_config['type'],
                    ZabbixProps.RESOURCE_NAME: element_config['name']
                }

            return mappings
        except Exception as e:
            LOG.exception('failed in init %s ', e)
            return {}

    def _get_triggers_per_host(self, host, alarms):
        host_ids = host[ZabbixProps.HOST_ID]
        triggers = self.client.trigger.get(hostids=host_ids)
        for trigger in triggers:
            trigger[ZabbixProps.RESOURCE_NAME] = host[ZabbixProps.HOST]
            alarms.append(trigger)
