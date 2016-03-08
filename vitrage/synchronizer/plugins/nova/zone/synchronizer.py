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

from vitrage.common.constants import EntityType
from vitrage.synchronizer.plugins.nova.base import NovaBase


class ZoneSynchronizer(NovaBase):
    def __init__(self, conf):
        version = conf[EntityType.NOVA_ZONE].version
        user = conf[EntityType.NOVA_ZONE].user
        password = conf[EntityType.NOVA_ZONE].password
        project = conf[EntityType.NOVA_ZONE].project
        auth_url = conf[EntityType.NOVA_ZONE].url
        super(ZoneSynchronizer, self).__init__(version,
                                               user,
                                               password,
                                               project,
                                               auth_url)
        self.conf = conf

    @staticmethod
    def filter_internal_zone(zones):
        zones_res = []
        for zone in zones:
            zone_dict = zone.__dict__
            if zone_dict['zoneName'] and zone_dict['zoneName'] != 'internal':
                zones_res.append(zone_dict)
        return zones_res

    def get_all(self, sync_mode):
        return self.make_pickleable(self.filter_internal_zone(
            self.client.availability_zones.list()),
            EntityType.NOVA_ZONE,
            sync_mode,
            ['manager'])

    def get_changes(self, sync_mode):
        pass
