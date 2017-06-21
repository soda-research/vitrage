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

import itertools

from oslo_service import service as os_service

from vitrage.datasources.services import ChangesService
from vitrage.datasources.services import SnapshotsService
from vitrage.entity_graph import utils


def create_send_to_queue_callback(rabbitq):
    def send_to_queue_callback(event):
        rabbitq.notify_when_applicable(event)

    return send_to_queue_callback


class Launcher(object):
    def __init__(self, conf, callback):
        self.conf = conf
        self.callback = callback
        self.drivers = utils.get_drivers(conf)
        self.services = self._register_services()

    def launch(self):
        launcher = os_service.ProcessLauncher(self.conf)
        for service in self.services:
            launcher.launch_service(service, 1)

    def _register_services(self):
        pull_datasources = utils.get_pull_datasources(self.conf)
        changes_services = \
            (ChangesService(self.conf,
                            [self.drivers[datasource]],
                            self.conf[datasource].changes_interval,
                            self.callback)
             for datasource in pull_datasources)

        snapshot_service = (SnapshotsService(self.conf,
                                             self.drivers,
                                             self.callback),)

        return itertools.chain(changes_services,
                               snapshot_service)
