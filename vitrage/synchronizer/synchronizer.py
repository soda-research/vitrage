# Copyright 2015 - Alcatel-Lucent
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
from nova_instance_plugin import NovaInstancePlugin
from snapshot_collector import SnapshotCollector


class Synchronizer(object):
    def __init__(self, queue):
        self.callback_function = self.create_send_to_queue_callback(queue)
        self.registered_plugins = self._init_registered_plugins()

    def create_send_to_queue_callback(self, queue):
        def send_to_queue_callback(output):
            for entity in output:
                queue.put(entity)

        return send_to_queue_callback

    def _init_registered_plugins(self):
        version = 2.0
        user = 'admin'
        password = 'password'
        proj = 'admin'
        auth_url = "http://localhost:5000/v2.0/"
        registered_plugins = \
            [NovaInstancePlugin(version, user, password, proj, auth_url)]
        return registered_plugins

    def get_all(self, entity_type_filter=None, sync_mode=None):
        self.sc = \
            SnapshotCollector(self.callback_function,
                              self.registered_plugins, sync_mode)
        self.sc.start()
        return
