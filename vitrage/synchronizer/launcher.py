# Copyright 2016 - Alcatel-Lucent
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

from oslo_log import log
from oslo_service import service as os_service

from services import ChangesService
from services import SnapshotsService
from vitrage.synchronizer.plugins.nagios.synchronizer import NagiosSynchronizer
from vitrage.synchronizer.plugins.nova.host.synchronizer import \
    HostSynchronizer
from vitrage.synchronizer.plugins.nova.instance.synchronizer import \
    InstanceSynchronizer
from vitrage.synchronizer.plugins.nova.zone.synchronizer import \
    ZoneSynchronizer
from vitrage.synchronizer.plugins.static_physical.synchronizer import \
    StaticPhysicalSynchronizer

LOG = log.getLogger(__name__)


def create_send_to_queue_callback(queue):
    def send_to_queue_callback(event):
        queue.put(event)

    return send_to_queue_callback


class Launcher(object):

    def __init__(self, conf, callback):
        self.conf = conf
        self.callback = callback
        self.snapshot_plugins = self._register_snapshot_plugins()
        self.services = self._register_services()

    def launch(self):
        launcher = os_service.ProcessLauncher(self.conf)
        for service in self.services:
            service.set_callback(self.callback)
            launcher.launch_service(service, 1)

    def _register_snapshot_plugins(self):
        version = 2.0
        user = 'admin'
        password = 'password'
        project = 'admin'
        auth_url = "http://localhost:5000/v2.0/"
        registered_plugins = \
            [ZoneSynchronizer(version, user, password, project, auth_url),
             HostSynchronizer(version, user, password, project, auth_url),
             InstanceSynchronizer(version, user, password, project, auth_url),
             NagiosSynchronizer(self.conf),
             StaticPhysicalSynchronizer(self.conf)]
        return registered_plugins

    def _register_services(self):
        nagios_changes_interval = self.conf.synchronizer.\
            nagios_changes_interval
        static_physical_changes_interval = self.conf.synchronizer.\
            static_physical_changes_interval

        return [SnapshotsService(self.conf, self.snapshot_plugins),
                ChangesService(self.conf,
                               [NagiosSynchronizer(self.conf)],
                               nagios_changes_interval),
                ChangesService(self.conf,
                               [StaticPhysicalSynchronizer(self.conf)],
                               static_physical_changes_interval)]
