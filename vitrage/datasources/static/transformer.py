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
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# TODO(yujunz) - skeleton only, methods to be implemented

from oslo_log import log as logging

from vitrage.common.constants import DatasourceProperties as DSProps
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources.resource_transformer_base import \
    ResourceTransformerBase
from vitrage.datasources.static import STATIC_DATASOURCE
from vitrage.datasources import transformer_base
import vitrage.graph.utils as graph_utils

LOG = logging.getLogger(__name__)


class StaticTransformer(ResourceTransformerBase):
    def __init__(self, transformers, conf):
        super(StaticTransformer, self).__init__(transformers, conf)

    def _create_snapshot_entity_vertex(self, entity_event):
        return self._create_vertex(entity_event)

    def _create_update_entity_vertex(self, entity_event):
        return self._create_vertex(entity_event)

    def _create_snapshot_neighbors(self, entity_event):
        return self._create_static_neighbors(entity_event)

    def _create_update_neighbors(self, entity_event):
        return self._create_static_neighbors(entity_event)

    def _create_entity_key(self, entity_event):
        entity_id = entity_event[VProps.ID]
        entity_type = entity_event[VProps.TYPE]
        key_fields = self._key_values(entity_type, entity_id)
        return transformer_base.build_key(key_fields)

    def get_type(self):
        return STATIC_DATASOURCE

    def _create_vertex(self, entity_event):
        entity_type = entity_event[VProps.TYPE]
        entity_id = entity_event[VProps.ID]
        sample_timestamp = entity_event[DSProps.SAMPLE_DATE]
        update_timestamp = self._format_update_timestamp(
            update_timestamp=None,
            sample_timestamp=sample_timestamp)
        state = entity_event[VProps.STATE]
        entity_key = self._create_entity_key(entity_event)

        return graph_utils.create_vertex(
            entity_key,
            entity_id=entity_id,
            entity_category=EntityCategory.RESOURCE,
            entity_type=entity_type,
            sample_timestamp=sample_timestamp,
            update_timestamp=update_timestamp,
            entity_state=state)

    def _create_static_neighbors(self, entity_event):
        return []
