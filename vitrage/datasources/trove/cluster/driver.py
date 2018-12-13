# Copyright 2018 Samsung Electronics
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_log import log

from vitrage.datasources.transformer_base import extract_field_value
from vitrage.datasources.trove.cluster import TROVE_CLUSTER_DATASOURCE
from vitrage.datasources.trove.properties import \
    TroveClusterProperties as TProps
from vitrage.datasources.trove.trove_driver_base import TroveDriverBase


LOG = log.getLogger(__name__)


class TroveClusterDriver(TroveDriverBase):

    def __init__(self, conf):
        super(TroveClusterDriver, self).__init__(conf)
        self._cached_entities = []

    def _get_vitrage_type(self):
        return TROVE_CLUSTER_DATASOURCE

    def _get_all_entities(self):
        # TODO(bzurkowski): Add all_tenants option to Trove client
        return self.extract_entities(self.client.clusters.list())

    def _find_entity(self, search_entity, entities):
        for entity in entities:
            if entity[TProps.ID] == search_entity[TProps.ID]:
                return entity

    def _equal_entities(self, old_entity, new_entity):
        old_state = extract_field_value(old_entity, *TProps.STATE)
        new_state = extract_field_value(old_entity, *TProps.STATE)
        return old_entity[TProps.ID] == new_entity[TProps.ID] and \
            old_entity[TProps.NAME] == new_entity[TProps.NAME] and \
            old_state == new_state
