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
# WARRANTIES OR CONDITIONS OF ANY KIND,  either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import multiprocessing


class SnapshotCollector(multiprocessing.Process):
    def __init__(self, callback_function, registered_plugins, sync_mode=None):
        multiprocessing.Process.__init__(self)
        self.callback_function = callback_function
        self.registered_plugins = registered_plugins
        self.sync_mode = sync_mode
        return

    def mark_snapshot_entities(self, entities_dictionaries):
        for entity_dict in entities_dictionaries:
            if self.sync_mode is None:
                entity_dict['sync_mode'] = 'update'
            else:
                entity_dict['sync_mode'] = self.sync_mode
        return entities_dictionaries

    def run(self):
        snapshot_entities_dictionaries = []
        for plugin in self.registered_plugins:
            entities_dictionaries = \
                self.mark_snapshot_entities(plugin.get_all())
            for entity_dict in entities_dictionaries:
                snapshot_entities_dictionaries.append(entity_dict)
        self.callback_function(snapshot_entities_dictionaries)
