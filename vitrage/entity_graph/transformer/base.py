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

LOG = logging.getLogger(__name__)


EntityWrapper = \
    namedtuple('EntityWrapper', ['vertex', 'neighbors', 'action'])

Neighbor = namedtuple('Neighbor', ['vertex', 'edge'])


def extract_field_value(entity_event, key_names):

    value = entity_event
    for key in key_names:
        value = value[key]

    return value


@six.add_metaclass(abc.ABCMeta)
class Transformer(object):

    KEY_SEPARATOR = ':'

    @abc.abstractmethod
    def transform(self, entity_event):
        """Transforms an entity event into entity wrapper.

        :return: An EntityWrapper. EntityWrapper - a namedTuple that contains
        three fields:
            1. Vertex - Entity vertex
            2. Neighbors - vertex and an edge pairs
            3. Action - CREATE/UPDATE/DELETE
        :rtype: EntityWrapper
        """
        pass

    @staticmethod
    def key_fields():
        """Returns a field list that are must to create the entity key.

        The field order is important to.
        :return: field list
        """
        return [cons.VertexProperties.TYPE,
                cons.VertexProperties.SUB_TYPE,
                cons.VertexProperties.ID]

    @abc.abstractmethod
    def extract_key(self, entity_event):
        """Extract entity key from given event

        By given an entity event, return a entity key which
        consisting key fields

        :param entity_event: event that returns from the synchronizer
        :return: key
        """
        pass
