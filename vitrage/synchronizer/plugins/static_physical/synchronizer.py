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
# WARRANTIES OR  CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os

from vitrage.common.constants import EntityType
from vitrage.common.constants import EventAction
from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common.constants import VertexProperties as VProps
from vitrage.common import file_utils
from vitrage.synchronizer.plugins.synchronizer_base import SynchronizerBase


class StaticPhysicalSynchronizer(SynchronizerBase):
    ENTITIES_SECTION = 'entities'

    def __init__(self, conf):
        super(StaticPhysicalSynchronizer, self).__init__()
        self.cfg = conf
        self.cache = {}

    def get_all(self, sync_mode):
        return self.make_pickleable(self._get_all_entities(),
                                    EntityType.SWITCH,
                                    sync_mode)

    def get_changes(self, sync_mode):
        return self.make_pickleable(self._get_changes_entities(),
                                    EntityType.SWITCH,
                                    sync_mode)

    def _get_all_entities(self):
        static_entities = []

        if os.path.isdir(self.cfg.synchronizer_plugins.static_plugins_dir):
            files = file_utils.load_files(
                self.cfg.synchronizer_plugins.static_plugins_dir, '.yaml')

            for file in files:
                full_path = self.cfg.synchronizer_plugins.static_plugins_dir \
                    + '/' + file
                static_entities += self._get_entities_from_file(file,
                                                                full_path)

        return static_entities

    def _get_entities_from_file(self, file, path):
        static_entities = []
        config = file_utils.load_yaml_file(path)

        for entity in config[self.ENTITIES_SECTION]:
            static_entities.append(entity.copy())

        self.cache[file] = config

        return static_entities

    def _get_changes_entities(self):
        entities_updates = []

        entities_updates = []
        files = file_utils.load_files(
            self.cfg.synchronizer_plugins.static_plugins_dir, '.yaml')

        for file in files:
            full_path = self.cfg.synchronizer_plugins.static_plugins_dir +\
                '/' + file
            config = file_utils.load_yaml_file(full_path)
            if config:
                if file in self.cache:
                    if str(config) != str(self.cache[file]):
                        # TODO(alexey_weyl): need also to remove deleted
                        #                   files from cache

                        self._update_on_existing_entities(
                            self.cache[file][self.ENTITIES_SECTION],
                            config[self.ENTITIES_SECTION],
                            entities_updates)

                        self._update_on_new_entities(
                            config[self.ENTITIES_SECTION],
                            self.cache[file][self.ENTITIES_SECTION],
                            entities_updates)

                        self.cache[file] = config
                else:
                    self.cache[file] = config
                    entities_updates += \
                        self._get_entities_from_file(file, full_path)

        return entities_updates

    def _update_on_existing_entities(self, old_entities,
                                     new_entities, updates):
        for old_entity in old_entities:
            if old_entity not in new_entities:
                new_entity = self._find_entity(old_entity, new_entities)
                if not new_entity:
                    self._delete_event(old_entity)
                    updates.append(old_entity.copy())
                else:
                    updates.append(new_entity.copy())

    @staticmethod
    def _find_entity(new_entity, entities):
        for entity in entities:
            if entity[VProps.TYPE] == new_entity[VProps.TYPE] \
                    and entity[VProps.ID] == new_entity[VProps.ID]:
                return entity
        return None

    @staticmethod
    def _update_on_new_entities(new_entities, old_entities, updates):
        for entity in new_entities:
            if entity not in updates and entity not in old_entities:
                updates.append(entity.copy())

    @staticmethod
    def _delete_event(entity):
        entity[SyncProps.EVENT_TYPE] = EventAction.DELETE
