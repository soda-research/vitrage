# Copyright 2016 - Alcatel-Lucent
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,  software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND,  either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from vitrage.synchronizer.plugins.neutron.base import NeutronBase
from vitrage.synchronizer.plugins.neutron.network import NEUTRON_NETWORK_PLUGIN


class NetworkSynchronizer(NeutronBase):

    @staticmethod
    def get_skipped_event_types():
        pass

    @staticmethod
    def get_topic(conf):
        pass

    @staticmethod
    def get_event_types(conf):
        pass

    @staticmethod
    def enrich_event(event, event_type):
        pass

    @staticmethod
    def extract(networks):
        return [network.__dict__ for network in networks]

    def get_all(self, sync_mode):
        return self.make_pickleable(
            self.extract(self.client.list_networks()),
            NEUTRON_NETWORK_PLUGIN,
            sync_mode)
