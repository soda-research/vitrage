# Copyright 2015 - Alcatel-Lucent
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

import abc
from collections import namedtuple

from oslo_log import log as logging
import six
from vitrage.common import datetime_utils

import vitrage.common.constants as cons
from vitrage.common.constants import EventAction
from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common.constants import SyncMode
from vitrage.common.exception import VitrageTransformerError
import vitrage.graph.utils as graph_utils
from vitrage.synchronizer.plugins import OPENSTACK_NODE

LOG = logging.getLogger(__name__)

EntityWrapper = \
    namedtuple('EntityWrapper', ['vertex', 'neighbors', 'action'])

Neighbor = namedtuple('Neighbor', ['vertex', 'edge'])


TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


AVAILABLE = 'available'


def extract_field_value(entity_event, *args):

    value = entity_event
    for key in args:
        value = value[key]

    return value


def build_key(key_values):
    return TransformerBase.KEY_SEPARATOR.join(map(str, key_values))


def create_node_placeholder_vertex():
    key = build_key([cons.EntityCategory.RESOURCE,
                     OPENSTACK_NODE])

    metadata = {
        cons.VertexProperties.NAME: OPENSTACK_NODE
    }

    return graph_utils.create_vertex(
        key,
        entity_id=OPENSTACK_NODE,
        entity_category=cons.EntityCategory.RESOURCE,
        entity_type=OPENSTACK_NODE,
        entity_state=AVAILABLE,
        metadata=metadata
    )


def convert_timestamp_format(current_timestamp_format, timestamp):

    return datetime_utils.change_time_str_format(
        timestamp,
        current_timestamp_format,
        TIMESTAMP_FORMAT
    )


def is_update_event(event):
    return event[SyncProps.SYNC_MODE] == SyncMode.UPDATE


@six.add_metaclass(abc.ABCMeta)
class TransformerBase(object):

    KEY_SEPARATOR = ':'
    QUERY_RESULT = 'graph_query_result'

    UPDATE_EVENT_TYPES = {}

    def transform(self, entity_event):
        """Transform an entity event into entity wrapper.

        Entity event is received from synchronizer it need to be
        transformed into entity wrapper. The wrapper contains:
            1. Entity Vertex - The vertex itself with all fields
            2. Neighbor list - neighbor placeholder vertex and an edge
            3. Action type - CREATE/UPDATE/DELETE

        :param entity_event: a general event from the synchronizer
        :return: entity wrapper
        :rtype:EntityWrapper
        """

        if not self._is_end_message(entity_event):
            entity_vertex = self._create_entity_vertex(entity_event)
            neighbors = self._create_neighbors(entity_event)
            action = self._extract_action_type(entity_event)

            return EntityWrapper(entity_vertex, neighbors, action)
        else:
            return EntityWrapper(self._create_end_vertex(entity_event),
                                 None,
                                 EventAction.END_MESSAGE)

    def _create_entity_vertex(self, entity_event):

        if is_update_event(entity_event):
            return self._create_update_entity_vertex(entity_event)
        else:
            return self._create_snapshot_entity_vertex(entity_event)

    @abc.abstractmethod
    def _create_snapshot_entity_vertex(self, entity_event):
        pass

    @abc.abstractmethod
    def _create_update_entity_vertex(self, entity_event):
        pass

    @abc.abstractmethod
    def _create_neighbors(self, entity_event):
        """Extracts entity neighbors received from a given entity event.

         Extracting entity neighbors from a given event provided
         by synchronizer

         :param entity_event: an event provided by synchronizer
         :return: neighbors - a list of neighbors where each item in the list
                              is a tuple of (vertex, edge)
         :rtype: list
         """

    @abc.abstractmethod
    def _create_entity_key(self, entity_event):
        """Create entity key from given event

        By given an entity event, return a entity key which
        consisting key fields

        :param entity_event: event that returns from the synchronizer
        :return: key
        """
        pass

    @abc.abstractmethod
    def create_placeholder_vertex(self, **kwargs):
        """Creates placeholder vertex.

        Placeholder vertex contains only mandatory fields of this entity.
        This way other plugins can create placeholder vertices of those
        entities

        :param kwargs: the properties for the placeholder vertex
        :return: Placeholder vertex
        :rtype: Vertex
        """
        pass

    def _extract_action_type(self, entity_event):
        """Extract action type.

        Decides what action (from constants.EventAction) the processor need
        to perform according to the data received from the event.

        :param entity_event: event that returns from the synchronizer
        :return: the action that the processor needs to perform
        :rtype: str
        """

        sync_mode = entity_event[SyncProps.SYNC_MODE]

        if SyncMode.UPDATE == sync_mode:
            return self.UPDATE_EVENT_TYPES.get(
                entity_event.get(SyncProps.EVENT_TYPE, None),
                EventAction.UPDATE_ENTITY)

        if SyncMode.SNAPSHOT == sync_mode:
            return EventAction.UPDATE_ENTITY

        if SyncMode.INIT_SNAPSHOT == sync_mode:
            return EventAction.CREATE_ENTITY

        raise VitrageTransformerError(
            'Invalid sync mode: (%s)' % sync_mode)

    def _key_values(self, *args):
        """A list of key fields

        The fields which consist the entity key

        :param args: a tuple of mutable key fields
        :return: ()
        """
        pass

    @staticmethod
    def _create_end_vertex(entity_event):
        sync_type = entity_event[SyncProps.SYNC_TYPE]
        return graph_utils.create_vertex(
            'END_MESSAGE:' + sync_type,
            entity_type=sync_type)

    @staticmethod
    def _is_end_message(entity_event):
        return entity_event[SyncProps.SYNC_MODE] == SyncMode.INIT_SNAPSHOT and\
            SyncProps.EVENT_TYPE in entity_event and \
            entity_event[SyncProps.EVENT_TYPE] == EventAction.END_MESSAGE

    @staticmethod
    def _format_update_timestamp(update_timestamp, sample_timestamp):
        return update_timestamp if update_timestamp else sample_timestamp

    @staticmethod
    def get_enrich_query(event):
        """Allow running a query on the graph vertices

        The result of the query specified here will be added to the event in
        the 'QUERY_RESULT' field.

         Example:
         -------
          query = {'type': 'nova.instance'}
          Before transform is called the result of running the query against
          the topology graph will be updated to event[QUERY_RESULT]
          To contain the list of all the vertices with type=nova.instance
        """
        return None
