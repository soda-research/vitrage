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

LOG = logging.getLogger(__name__)


EntityWrapper = \
    namedtuple('EntityWrapper', ['vertex', 'neighbors', 'action'])

Neighbor = namedtuple('Neighbor', ['vertex', 'edge'])


@six.add_metaclass(abc.ABCMeta)
class Transformer(object):

    KEY_SEPARATOR = ':'

    @abc.abstractmethod
    def transform(self, entity_event):
        """Transforms an entity event into entity wrapper

        :return: An EntityWrapper. EntityWrapper is namedTuple that contains
        an entity vertex and a list of vertex and an edge pair that describe
        the entity's neighbors.
        :rtype: EntityWrapper
        """
        pass

    @abc.abstractmethod
    def key_fields(self):
        pass

    @abc.abstractmethod
    def extract_key(self, entity_event):
        pass
