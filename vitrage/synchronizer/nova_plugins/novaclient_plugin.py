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


from novaclient import client
from vitrage.common import utils
from vitrage.synchronizer.base_plugin import BasePlugin


class NovaClientPlugin(BasePlugin):
    def __init__(self, version, user, password, project, auth_url):
        super(NovaClientPlugin, self).__init__()
        self.client = client.Client(version, user, password, project, auth_url)

    def get_client(self):
        return self.client

    def make_picklable(self, entities, sync_type, fields_to_remove=None):

        picklable_entities = []

        for entity in entities:
            picklable_entity = entity.__dict__

            for field in fields_to_remove:
                picklable_entity.pop(field)

            picklable_entity['sync_type'] = sync_type
            self._add_sampling_time(picklable_entity)
            picklable_entities.append(picklable_entity)

        return picklable_entities

    @staticmethod
    def _add_sampling_time(entity):
        entity['sample_date'] = str(utils.utcnow())
        return entity
