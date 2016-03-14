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

from oslo_log import log

from vitrage.common.constants import EntityCategory
from vitrage.common.constants import EntityType
from vitrage.common.constants import VertexProperties as VProps
from vitrage.common.datetime_utils import utcnow

LOG = log.getLogger(__name__)


class ConsistencyEnforcer(object):

    def __init__(self, cfg, entity_graph, initialization_status):
        self.cfg = cfg
        self.graph = entity_graph
        self.initialization_status = initialization_status
        self.notifier = None

    def initializing_process(self):
        try:
            LOG.debug('Started consistency starting check')
            if self.initialization_status.is_received_all_end_messages():
                LOG.debug('All end messages were received')
                timestamp = utcnow()
                all_vertices = self.graph.get_vertices()

                for vertex in all_vertices:
                    self.run_evaluator(vertex)

                self._notify_deletion_of_deduced_alarms(timestamp)

                self.initialization_status.status = \
                    self.initialization_status.FINISHED
        except Exception as e:
            LOG.exception('Error in deleting vertices from entity_graph: %s',
                          e)

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
        except Exception as e:
            LOG.exception('Error in deleting vertices from entity_graph: %s',
                          e)

    def _find_stale_entities(self):
        query = {
            'and': [
                {'!=': {VProps.TYPE: EntityType.VITRAGE}},
                {'<': {VProps.UPDATE_TIMESTAMP: str(utcnow() - timedelta(
                    seconds=2 * self.cfg.consistency.consistency_interval))}}
            ]
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

    def _find_old_deduced_alarms(self, timestamp):
        query = {
            'and': [
                {'==': {VProps.CATEGORY: EntityCategory.ALARM}},
                {'==': {VProps.TYPE: EntityType.VITRAGE}},
                {'>=': {VProps.UPDATE_TIMESTAMP: timestamp}}
            ]
        }
        return self.graph.get_vertices(query_dict=query)

    def _notify_deletion_of_deduced_alarms(self, timestamp):
        old_deduced_alarms = self._find_old_deduced_alarms(timestamp)
        for vertex in old_deduced_alarms:
            # TODO(Alexey): use notifier to inform aodh
            self.notifier(vertex)

    def _delete_vertices(self, vertices):
        for vertex in vertices:
            self.graph.remove_vertex(vertex)

    @staticmethod
    def _filter_vertices_to_be_deleted(vertices):
        return filter(
            lambda ver:
            not (ver[VProps.CATEGORY] == EntityCategory.RESOURCE and
                 ver[VProps.TYPE] == EntityType.OPENSTACK_NODE), vertices)
