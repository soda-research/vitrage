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

from datetime import timedelta
import traceback

from oslo_log import log

from vitrage.common.constants import EntityCategory
from vitrage.common.constants import EntityType
from vitrage.common.constants import VertexProperties as VProps
from vitrage.common.datetime_utils import utcnow

LOG = log.getLogger(__name__)


class ConsistencyEnforcer(object):

    def __init__(self, cfg, entity_graph):
        self.cfg = cfg
        self.graph = entity_graph

    def starting_process(self):
        pass

    def periodic_process(self):
        try:
            LOG.debug('Started consistency periodic check')

            # periodic check
            stale_entities = self._find_stale_entities()
            old_deleted_entities = self._find_old_deleted_entities()
            vertices_to_delete = stale_entities.union(old_deleted_entities)

            LOG.debug('Found %s vertices to be deleted by consistency service'
                      ': %s', len(stale_entities), vertices_to_delete)

            self._delete_vertices(vertices_to_delete)
        except Exception:
            LOG.error("Error in deleting vertices from entity_graph: %s",
                      traceback.print_exc())

    def _find_stale_entities(self):
        query = {
            '<': {VProps.UPDATE_TIMESTAMP: str(utcnow() - timedelta(
                seconds=2 * self.cfg.consistency.consistency_interval))},
        }

        vertices = self.graph.get_vertices(query_dict=query)

        return set(self._filter_vertices_to_be_deleted(vertices))

    def _find_old_deleted_entities(self):
        query = {
            'and': [
                {'==': {VProps.IS_DELETED: True}},
                {'<': {VProps.UPDATE_TIMESTAMP: str(utcnow() - timedelta(
                    seconds=self.cfg.consistency.min_time_to_delete))}}
            ]
        }

        vertices = self.graph.get_vertices(query_dict=query)

        return set(self._filter_vertices_to_be_deleted(vertices))

    def _delete_vertices(self, vertices):
        for vertex in vertices:
            self.graph.remove_vertex(vertex)

    @staticmethod
    def _filter_vertices_to_be_deleted(vertices):
        return filter(
            lambda ver:
            not (ver.properties[VProps.CATEGORY] == EntityCategory.RESOURCE
                 and ver.properties[VProps.TYPE] == EntityType.NODE), vertices)
