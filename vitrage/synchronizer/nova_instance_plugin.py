# Copyright 2015 - Alcatel-Lucent
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

from base_plugin import BasePlugin
from novaclient import client


class NovaInstancePlugin(BasePlugin):
    def __init__(self, version, user, password, proj, auth_url):
        self.client = client.Client(version, user, password, proj, auth_url)

    def make_picklable(self, entities):
        picklable_entities = []
        for entity in entities:
            picklable_entity = entity.__dict__
            picklable_entity.pop('manager')
            picklable_entity['sync_type'] = 'nova.instance'
            picklable_entities.append(picklable_entity)
        return picklable_entities

    def get_all(self):
        return self.make_picklable(self.client.servers.list())
