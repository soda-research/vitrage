# Copyright 2016 - Alcatel-Lucent
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

from oslo_log import log
from oslo_service import service as os_service

from services import SnapshotsService
from vitrage.synchronizer.plugins.nagios.plugin import Nagios
from vitrage.synchronizer.plugins.nova.host import Host
from vitrage.synchronizer.plugins.nova.instance import Instance
from vitrage.synchronizer.plugins.nova.zone import Zone
from vitrage.synchronizer.plugins.static_physical import StaticPhysical

LOG = log.getLogger(__name__)


def create_send_to_queue_callback(queue):
    def send_to_queue_callback(entity):
        queue.put(entity)

    return send_to_queue_callback


class Launcher(object):

    def __init__(self, conf, callback):

        self.conf = conf
        self.callback = callback
        self.plugins = self._init_registered_plugins()
        self.services = [SnapshotsService(conf, self.plugins)]

    def launch(self):
        launcher = os_service.ProcessLauncher(self.conf)
        for service in self.services:
            service.set_callback(self.callback)
            launcher.launch_service(service, 1)

    def _init_registered_plugins(self):
        version = 2.0
        user = 'admin'
        password = 'password'
        project = 'admin'
        auth_url = "http://localhost:5000/v2.0/"
        registered_plugins = \
            [Zone(version, user, password, project, auth_url),
             Host(version, user, password, project, auth_url),
             Instance(version, user, password, project, auth_url),
             Nagios(self.conf),
             StaticPhysical(self.conf)
             ]
        return registered_plugins
