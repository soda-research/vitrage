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
import six

from collections import namedtuple
from oslo_log import log as logging

import vitrage.common.constants as cons
from vitrage.common.exception import VitrageTransformerError
import vitrage.graph.utils as graph_utils


LOG = logging.getLogger(__name__)
NODE_SUBTYPE = 'node'


EntityWrapper = \
    namedtuple('EntityWrapper', ['vertex', 'neighbors', 'action'])

Neighbor = namedtuple('Neighbor', ['vertex', 'edge'])


def extract_field_value(entity_event, key_names):

    value = entity_event
    for key in key_names:
        value = value[key]

    return value


def build_key(key_fields):
    return Transformer.KEY_SEPARATOR.join(key_fields)


def create_node_placeholder_vertex():
    key = build_key([cons.EntityTypes.RESOURCE, NODE_SUBTYPE])

    metadata = {
        cons.VertexProperties.NAME: NODE_SUBTYPE
    }

    return graph_utils.create_vertex(
        key,
        entity_type=cons.EntityTypes.RESOURCE,
        entity_subtype=NODE_SUBTYPE,
        metadata=metadata
    )


@six.add_metaclass(abc.ABCMeta)
class Transformer(object):

    KEY_SEPARATOR = ':'

    @abc.abstractmethod
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
        pass

    def key_fields(self):
        """Returns a field list that are must to create the entity key.

        The field order is important to.
        :return: field list
        """
        return [cons.VertexProperties.TYPE,
                cons.VertexProperties.SUBTYPE,
                cons.VertexProperties.ID]

    @abc.abstractmethod
    def key_values(self, mutable_fields=None):
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
    def create_placeholder_vertex(self, entity_id):
        """Creates placeholder vertex.

        Placeholder vertex contains only mandatory fields

        :param instance_id: The instance ID
        :return: Placeholder vertex
        :rtype: Vertex
        """
        pass

    def extract_action_type(self, entity_event):

        sync_mode = entity_event['sync_mode']

        if cons.SyncMode.UPDATE == sync_mode:
            return cons.EventAction.UPDATE

        if cons.SyncMode.SNAPSHOT == sync_mode:
            return cons.EventAction.UPDATE

        if cons.SyncMode.INIT_SNAPSHOT == sync_mode:
            return cons.EventAction.CREATE

        raise VitrageTransformerError(
            'Invalid sync mode: (%s)' % sync_mode)
