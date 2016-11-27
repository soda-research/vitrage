# Copyright 2016 - Nokia, ZTE
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR  CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from vitrage.datasources.driver_base import DriverBase
from vitrage.datasources.static import STATIC_DATASOURCE


class StaticDriver(DriverBase):

    def __init__(self, conf):
        super(StaticDriver, self).__init__()
        self.cfg = conf
        self.cache = {}

    @staticmethod
    def get_event_types():
        return []

    @staticmethod
    def enrich_event(event, event_type):
        pass

    def get_all(self, sync_mode):
        """Query all entities and send events to the vitrage events queue"""
        return self.make_pickleable(self._get_all_entities(),
                                    STATIC_DATASOURCE,
                                    sync_mode)

    def get_changes(self, sync_mode):
        return self.make_pickleable(self._get_changes_entities(),
                                    STATIC_DATASOURCE,
                                    sync_mode)

    def _get_all_entities(self):
        """Internal method to get all entities"""
        return []

    def _get_changes_entities(self):
        """Internal method to get changed entities"""
        return []
