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
from oslo_log import log as logging

from vitrage.common.constants import EdgeLabels
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common.constants import VertexProperties as VProps
from vitrage.common import datetime_utils
import vitrage.graph.utils as graph_utils
from vitrage.synchronizer.plugins.aodh.properties import AodhProperties \
    as AodhProps
from vitrage.synchronizer.plugins.aodh.properties import EventProps
from vitrage.synchronizer.plugins.base.alarm.properties \
    import AlarmProperties as AlarmProps
from vitrage.synchronizer.plugins.base.alarm.transformer \
    import BaseAlarmTransformer
from vitrage.synchronizer.plugins import transformer_base as tbase
from vitrage.synchronizer.plugins.transformer_base import Neighbor

LOG = logging.getLogger(__name__)


class AodhTransformer(BaseAlarmTransformer):

    STATUS_OK = 'ok'

    def __init__(self, transformers):
        super(AodhTransformer, self).__init__(transformers)

    def _create_entity_vertex(self, entity_event):
        metadata = {
            VProps.NAME: entity_event[AodhProps.NAME],
            VProps.SEVERITY: entity_event[AodhProps.SEVERITY],
            AodhProps.DESCRIPTION: entity_event[AodhProps.DESCRIPTION],
            AodhProps.ENABLED: entity_event[AodhProps.ENABLED],
            VProps.PROJECT_ID: entity_event[AodhProps.PROJECT_ID],
            AodhProps.REPEAT_ACTIONS: entity_event[AodhProps.REPEAT_ACTIONS],
            'alarm_type': entity_event[AodhProps.TYPE]
        }

        if entity_event[AodhProps.TYPE] == AodhProps.EVENT:
            metadata[AodhProps.EVENT_TYPE] = entity_event[AodhProps.EVENT_TYPE]

        elif entity_event[AodhProps.TYPE] == AodhProps.THRESHOLD:
            metadata[AodhProps.STATE_TIMESTAMP] = \
                entity_event[AodhProps.STATE_TIMESTAMP]

        sample_timestamp = entity_event[SyncProps.SAMPLE_DATE]

        update_timestamp = self._format_update_timestamp(
            AodhTransformer._timestamp(entity_event), sample_timestamp)

        return graph_utils.create_vertex(
            self._create_entity_key(entity_event),
            entity_id=entity_event[AodhProps.ALARM_ID],
            entity_category=EntityCategory.ALARM,
            entity_type=entity_event[SyncProps.SYNC_TYPE],
            entity_state=AlarmProps.ALARM_ACTIVE_STATE,
            sample_timestamp=sample_timestamp,
            update_timestamp=update_timestamp,
            metadata=metadata)

    # noinspection PyMethodMayBeStatic
    def _create_neighbors(self, entity_event):
        resource_id = entity_event[AodhProps.RESOURCE_ID]
        resource_type = entity_event['affected_resource_type']
        resource_category = entity_event['affected_resource_category']
        resource_vertex_id = entity_event['resource_vertex_id']
        vertex = graph_utils.create_vertex(
            resource_vertex_id,
            entity_id=resource_id,
            entity_category=resource_category,
            entity_type=resource_type,
            sample_timestamp=entity_event[SyncProps.SAMPLE_DATE],
            is_placeholder=True)

        edge = graph_utils.create_edge(
            source_id=self.extract_key(entity_event),
            target_id=resource_vertex_id,
            relationship_type=EdgeLabels.ON)
        return [Neighbor(vertex, edge)]

    def _ok_status(self, entity_event):
        return entity_event[AodhProps.STATE] == self.STATUS_OK

    def _create_entity_key(self, entity_event):
        sync_type = entity_event[SyncProps.SYNC_TYPE]
        alarm_name = entity_event[AodhProps.NAME]
        resource_id = entity_event[AodhProps.RESOURCE_ID]
        return (tbase.build_key(self._key_values(sync_type,
                                                 resource_id,
                                                 alarm_name)) if resource_id
                else tbase.build_key(self._key_values(sync_type, alarm_name)))

    @staticmethod
    def _timestamp(entity_event):
        return datetime_utils.change_time_str_format(
            entity_event[AodhProps.TIMESTAMP],
            '%Y-%m-%dT%H:%M:%S.%f',
            tbase.TIMESTAMP_FORMAT)

    @staticmethod
    def enrich_event(event, graph):
        affected_resource_id = event.get(AodhProps.RESOURCE_ID, None)
        if not affected_resource_id:
            return

        vertices = graph.get_vertices({VProps.ID: affected_resource_id})
        LOG.debug('affected resource id %s found %s items',
                  affected_resource_id, str(len(vertices)))
        if len(vertices) != 1:
            LOG.error('Unknown affected resource id %s', affected_resource_id)
            return
        event[EventProps.AFFECTED_TYPE] = vertices[0][VProps.TYPE]
        event[EventProps.AFFECTED_CATEGORY] = vertices[0][VProps.CATEGORY]
        event[EventProps.RESOURCE_VERTEX_ID] = vertices[0].vertex_id
