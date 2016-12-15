# Copyright 2016 - Nokia, ZTE
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

from itertools import chain
from six.moves import reduce

from oslo_log import log

from vitrage.common.constants import TopologyFields
from vitrage.datasources.driver_base import DriverBase
from vitrage.datasources.static import STATIC_DATASOURCE
from vitrage.utils import file as file_utils

LOG = log.getLogger(__name__)


class StaticDriver(DriverBase):

    CONFIG_ID = 'config_id'

    def __init__(self, conf):
        super(StaticDriver, self).__init__()
        self.cfg = conf
        self.cache = {}
        self.legacy_driver = {}

    @staticmethod
    def is_valid_config(config):
        """check for validity of configuration"""
        # TODO(yujunz) check with yaml schema or reuse template validation
        return TopologyFields.DEFINITIONS in config

    @staticmethod
    def get_event_types():
        return []

    def enrich_event(self, event, event_type):
        pass

    def get_all(self, datasource_action):
        return self.make_pickleable(self._get_all_entities(),
                                    STATIC_DATASOURCE,
                                    datasource_action)

    def get_changes(self, datasource_action):
        return self.make_pickleable(self._get_changes_entities(),
                                    STATIC_DATASOURCE,
                                    datasource_action)

    def _get_all_entities(self):
        files = file_utils.list_files(self.cfg.static.directory, '.yaml', True)
        return reduce(chain, [self._get_entities_from_file(path)
                              for path in files], [])

    def _get_changes_entities(self):
        """TODO(yujunz): update from file change or CRUD"""
        return []

    @classmethod
    def _get_entities_from_file(cls, path):
        config = file_utils.load_yaml_file(path)

        if not cls.is_valid_config(config):
            LOG.warning("Skipped invalid config (possible obsoleted): {}"
                        .format(path))
            return []

        definitions = config[TopologyFields.DEFINITIONS]

        entities = definitions[TopologyFields.ENTITIES]
        relationships = definitions[TopologyFields.RELATIONSHIPS]

        return cls._pack(entities, relationships)

    @classmethod
    def _pack(cls, entities, relationships):
        entity_index = {}
        for entity in entities:
            cls._pack_entity(entity_index, entity)
        for rel in relationships:
            cls._pack_rel(entity_index, rel)
        return entity_index.values()

    @classmethod
    def _pack_entity(cls, entity_index, entity):
        config_id = entity[cls.CONFIG_ID]
        if config_id not in entity_index:
            entity_index[config_id] = entity
            entity[TopologyFields.RELATIONSHIPS] = []
        else:
            LOG.warning("Skipped duplicated entity: {}".format(entity))

    @staticmethod
    def _pack_rel(entity_index, rel):
        # use set to handle self pointing relationship
        ids = {rel[TopologyFields.SOURCE], rel[TopologyFields.TARGET]}
        for config_id in ids:
            entity_index[config_id][TopologyFields.RELATIONSHIPS].append(rel)
