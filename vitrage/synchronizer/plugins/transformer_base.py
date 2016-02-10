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

import abc
from collections import namedtuple

from oslo_log import log as logging
import six

import vitrage.common.constants as cons
from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common.exception import VitrageTransformerError
import vitrage.graph.utils as graph_utils

LOG = logging.getLogger(__name__)
NODE_SUBTYPE = 'node'


EntityWrapper = \
    namedtuple('EntityWrapper', ['vertex', 'neighbors', 'action'])

Neighbor = namedtuple('Neighbor', ['vertex', 'edge'])


TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

Neighbor = namedtuple('Neighbor', ['vertex', 'edge'])


def extract_field_value(entity_event, key_names):

    value = entity_event
    for key in key_names:
        value = value[key]

    return value


def build_key(key_values):
    return TransformerBase.KEY_SEPARATOR.join(key_values)


def create_node_placeholder_vertex():
    key = build_key([cons.EntityCategory.RESOURCE, NODE_SUBTYPE])

    metadata = {
        cons.VertexProperties.NAME: NODE_SUBTYPE
    }

    return graph_utils.create_vertex(
        key,
        entity_category=cons.EntityCategory.RESOURCE,
        entity_type=NODE_SUBTYPE,
        metadata=metadata
    )


@six.add_metaclass(abc.ABCMeta)
class TransformerBase(object):

    KEY_SEPARATOR = ':'

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
        entity_vertex = self._create_entity_vertex(entity_event)
        neighbors = self._create_neighbors(entity_event)
        action = self._extract_action_type(entity_event)

        return EntityWrapper(entity_vertex, neighbors, action)

    @abc.abstractmethod
    def _create_entity_vertex(self, entity_event):
        """Creates entity vertex received from given entity event.

         Extracting vertex fields from a given event provided by synchronizer

         :param entity_event: an event provided by synchronizer
         :return: vertex - contains the entity data
         :rtype:Vertex
         """

    @abc.abstractmethod
    def _create_neighbors(self, entity_event):
        """Extracts entity neighbors received from a given entity event.

         Extracting entity neighbors from a given event provided
         by synchronizer

         :param entity_event: an event provided by synchronizer
         :return: neigbors - a list of neighbors
         :rtype:[]
         """

    @abc.abstractmethod
    def key_values(self, mutable_fields=[]):
        """A list of key fields

        The fields which consist the entity key

        :param mutable_fields: a list of mutable key fields
        :return: []
        """
        pass

    @abc.abstractmethod
    def extract_key(self, entity_event):
        """Extract entity key from given event

        By given an entity event, return a entity key which
        consisting key fields

        :param entity_event: event that returns from the synchronizer
        :return: key
        """
        pass

    @abc.abstractmethod
    def create_placeholder_vertex(self, properties={}):
        """Creates placeholder vertex.

        Placeholder vertex contains only mandatory fields

        :param properties: the properties for the placeholder vertex
        :return: Placeholder vertex
        :rtype: Vertex
        """
        pass

    def _extract_action_type(self, entity_event):

        sync_mode = entity_event[SyncProps.SYNC_MODE]

        if cons.SyncMode.UPDATE == sync_mode:
            return cons.EventAction.UPDATE

        if cons.SyncMode.SNAPSHOT == sync_mode:
            return cons.EventAction.UPDATE

        if cons.SyncMode.INIT_SNAPSHOT == sync_mode:
            return cons.EventAction.CREATE

        raise VitrageTransformerError(
            'Invalid sync mode: (%s)' % sync_mode)
