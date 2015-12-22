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
from vitrage.common.constants import VertexProperties as vertex_cons
from vitrage.common.exception import VitrageTransformerError
import vitrage.entity_graph.transformer.base as base_transformer
from vitrage.entity_graph.transformer import transformer_manager
import vitrage.graph.utils as graph_utils
from vitrage.tests.unit import base

LOG = logging.getLogger(__name__)


def create_vertex(entity_id, entity_type, entity_subtype=None):

    """returns vertex with partial data"""

    vertex_id = base_transformer.Transformer.KEY_SEPARATOR.join(
        [entity_type, entity_subtype, entity_id])

    return graph_utils.create_vertex(
        vertex_id,
        entity_id=entity_id,
        entity_type=entity_type,
        entity_subtype=entity_subtype
    )


class TransformerManagerTest(base.BaseTest):

    def test_key_fields(self):

        LOG.debug('Test get key fields from by given entity_event')
        manager = transformer_manager.TransformerManager()

        expected_instance_key_fields = [vertex_cons.TYPE,
                                        vertex_cons.SUB_TYPE,
                                        vertex_cons.ID]

        instance_vertex = create_vertex('123', 'RESOURCE', 'nova.instance')
        observed_instance_key_fields = manager.key_fields(instance_vertex)
        self.assert_list_equal(
            expected_instance_key_fields,
            observed_instance_key_fields
        )

        no_entity_vertex = create_vertex('123', 'RESOURCE', 'no.transformer')

        self.assertRaises(
            VitrageTransformerError, manager.key_fields, no_entity_vertex)
