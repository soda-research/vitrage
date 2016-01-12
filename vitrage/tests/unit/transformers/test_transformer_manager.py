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

from oslo_log import log as logging
from vitrage.entity_graph.transformer.base import TransformerBase
import vitrage.graph.utils as graph_utils
from vitrage.tests.unit import base

LOG = logging.getLogger(__name__)


def create_vertex(entity_id, entity_type, entity_subtype=None):

    """returns placeholder vertex"""

    vertex_id = TransformerBase.KEY_SEPARATOR.join(
        [entity_type, entity_subtype, entity_id])

    return graph_utils.create_vertex(
        vertex_id,
        entity_id=entity_id,
        entity_type=entity_type,
        entity_subtype=entity_subtype
    )


class TransformerManagerTest(base.BaseTest):
    pass
