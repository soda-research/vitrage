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

from vitrage.common.constants import EntityType
from vitrage.synchronizer.nova_plugins.novaclient_plugin \
    import NovaClientPlugin


class NovaInstancePlugin(NovaClientPlugin):
    def __init__(self, version, user, password, project, auth_url):
        super(NovaInstancePlugin, self).__init__(version,
                                                 user,
                                                 password,
                                                 project,
                                                 auth_url)

    def get_all(self):
        return self.make_pickleable(self.client.servers.list(),
                                    EntityType.NOVA_INSTANCE, ['manager'])
