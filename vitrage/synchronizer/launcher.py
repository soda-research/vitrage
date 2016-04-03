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

from oslo_log import log
from oslo_service import service as os_service
from oslo_utils import importutils as utils
from vitrage.synchronizer.plugins.listener_service import ListenerService

from services import ChangesService
from services import SnapshotsService
from vitrage.common.utils import opt_exists

LOG = log.getLogger(__name__)
CHANGES_INTERVAL = 'changes_interval'


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
            launcher.launch_service(service, 1)

    def _register_snapshot_plugins(self):
        return {plugin: utils.import_object(self.conf[plugin].synchronizer,
                                            self.conf)
                for plugin in self.conf.plugins.plugin_type}

    def _register_services(self):
        return itertools.chain(
            (ChangesService(self.conf,
                            [self.snapshot_plugins[plugin]],
                            self.conf[plugin].changes_interval,
                            self.callback)

                for plugin in self.conf.plugins.plugin_type
                if opt_exists(self.conf[plugin], CHANGES_INTERVAL)),

            (SnapshotsService(self.conf,
                              self.snapshot_plugins,
                              self.callback),),

            (ListenerService(self.conf,
                             self.snapshot_plugins,
                             self.callback),),)
