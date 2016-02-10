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
from vitrage.synchronizer.base import SynchronizerBase
from vitrage.synchronizer.plugins.nagios.parser import NagiosParser
from vitrage.synchronizer.plugins.nagios.properties import NagiosProperties \
    as NagiosProps
from vitrage.synchronizer.plugins.nagios.properties import NagiosStatus

LOG = log.getLogger(__name__)


class NagiosSynchronizer(SynchronizerBase):
    ServiceKey = namedtuple('ServiceKey', ['host_name', 'service'])

    def __init__(self, conf):
        super(NagiosSynchronizer, self).__init__()
        self.conf = conf
        self.cache = dict()

    def get_all(self):
        return self.make_pickleable(self._get_services(), EntityType.NAGIOS)

    def _get_services(self):
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
            self._enrich_services(nagios_services)
            return self._cache_and_filter_services(nagios_services)
        else:
            LOG.error(_LE('Failed to get nagios data. Response code: %s') %
                      response.status_code)
            return []

    def _enrich_services(self, nagios_services):
        for service in nagios_services:
            # TODO(ifat_afek) - add a configuration file for resource types
            service[NagiosProps.RESOURCE_TYPE] = EntityType.NOVA_HOST
            service[SyncProps.SYNC_TYPE] = NagiosProps.NAGIOS

    def _cache_and_filter_services(self, nagios_services):
        services_to_update = []

        for service in nagios_services:
            # return all erroneous services, plus services that their status
            # has changed from erroneous to OK
            service_key = self.ServiceKey(
                host_name=service[NagiosProps.RESOURCE_NAME],
                service=service[NagiosProps.SERVICE])

            if service[NagiosProps.STATUS] == NagiosStatus.OK:
                if service_key in self.cache:
                    old_service = self.cache[service_key]
                    if old_service[NagiosProps.STATUS] != NagiosStatus.OK:
                        services_to_update.append(service)
            else:
                services_to_update.append(service)

            self.cache[service_key] = service

        return services_to_update
