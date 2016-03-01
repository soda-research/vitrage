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
import requests

from vitrage.common.constants import EntityType
from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.i18n import _LE
from vitrage.i18n import _LW
from vitrage.synchronizer.plugins.nagios.config import NagiosConfig
from vitrage.synchronizer.plugins.nagios.parser import NagiosParser
from vitrage.synchronizer.plugins.nagios.properties import NagiosProperties \
    as NagiosProps
from vitrage.synchronizer.plugins.nagios.properties import NagiosStatus
from vitrage.synchronizer.plugins.synchronizer_base import SynchronizerBase

LOG = log.getLogger(__name__)


class NagiosSynchronizer(SynchronizerBase):
    ServiceKey = namedtuple('ServiceKey', ['host_name', 'service'])

    def __init__(self, conf):
        super(NagiosSynchronizer, self).__init__()
        self.conf = conf
        self.cache = dict()
        self.config = NagiosConfig(conf)

    def get_all(self, sync_mode):
        return self.make_pickleable(self._get_all_services(),
                                    EntityType.NAGIOS,
                                    sync_mode)

    def get_changes(self, sync_mode):
        return self.make_pickleable(self._get_changed_services(),
                                    EntityType.NAGIOS,
                                    sync_mode)

    def _get_all_services(self):
        nagios_services = self._get_services_from_nagios()
        self._enrich_services(nagios_services)
        return self._filter_and_cache_services(
            nagios_services,
            NagiosSynchronizer._filter_get_all)

    def _get_changed_services(self):
        nagios_services = self._get_services_from_nagios()
        self._enrich_services(nagios_services)
        return self._filter_and_cache_services(
            nagios_services,
            NagiosSynchronizer._filter_get_changes)

    def _get_services_from_nagios(self):
        nagios_user = self.conf.synchronizer_plugins.nagios_user
        nagios_password = self.conf.synchronizer_plugins.nagios_password
        nagios_url = self.conf.synchronizer_plugins.nagios_url

        if not nagios_user:
            return []

        if not nagios_password:
            LOG.warn(_LW('Nagios password is not defined'))
            return []

        if not nagios_url:
            LOG.warn(_LW('Nagios url is not defined'))
            return []

        session = requests.Session()
        payload = {'host': 'all', 'limit': '0'}

        response = session.get(nagios_url,
                               params=payload,
                               auth=(nagios_user, nagios_password))

        if response.status_code == requests.codes.ok:
            nagios_services = NagiosParser().parse(response.text)
            return nagios_services
        else:
            LOG.error(_LE('Failed to get nagios data. Response code: %s') %
                      response.status_code)
            return []

    def _enrich_services(self, nagios_services):
        for service in nagios_services:
            # based on nagios configuration file, convert nagios host name
            # to vitrage resource type and name
            service[SyncProps.SYNC_TYPE] = NagiosProps.NAGIOS

            nagios_host = service[NagiosProps.RESOURCE_NAME]
            vitrage_resource = self.config.get_vitrage_resource(nagios_host)

            service[NagiosProps.RESOURCE_TYPE] = \
                vitrage_resource[0] if vitrage_resource else None
            service[NagiosProps.RESOURCE_NAME] = \
                vitrage_resource[1] if vitrage_resource \
                else service[NagiosProps.RESOURCE_NAME]

    def _filter_and_cache_services(self, nagios_services, filter_):
        services_to_update = []

        for service in nagios_services:
            service_key = self.ServiceKey(
                host_name=service[NagiosProps.RESOURCE_NAME],
                service=service[NagiosProps.SERVICE])

            old_service = self.cache.get(service_key, None)

            if filter_(service, old_service):
                services_to_update.append(service)

            self.cache[service_key] = service

        return services_to_update

    @staticmethod
    def _filter_get_all(service, old_service):
        return service \
            if (NagiosSynchronizer._is_erroneous(service) or
                NagiosSynchronizer._is_erroneous(old_service)) \
            else None

    @staticmethod
    def _filter_get_changes(service, old_service):
        if NagiosSynchronizer._status_changed(service, old_service):
            return service
        elif not old_service and NagiosSynchronizer._is_erroneous(service):
            return service
        else:
            return None

    @staticmethod
    def _is_erroneous(service):
        return service and service[NagiosProps.STATUS] != NagiosStatus.OK

    @staticmethod
    def _status_changed(service1, service2):
        return service1 and service2 and \
            not service1[NagiosProps.STATUS] == service2[NagiosProps.STATUS]
