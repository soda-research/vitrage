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

from vitrage.common.constants import VertexProperties
from vitrage.entity_graph.transformer import transformer_manager
from vitrage.graph import driver as graph
from vitrage.tests.unit import base


class BaseProcessor(base.BaseTest):

    def setUp(self):
        super(BaseProcessor, self).setUp()
        self.transform = transformer_manager.TransformerManager()

    def _update_vertex_to_graph(self, e_g_manager, type,
                                sub_type, id, additional_prop):
        # create vertex properties
        prop = {key: value for key, value in additional_prop.iteritems()}
        prop[VertexProperties.TYPE] = type
        prop[VertexProperties.SUB_TYPE] = sub_type
        prop[VertexProperties.ID] = id

        # TODO(Alexey): change back to original method
        # vertex_id = self.transform.get_key(prop)
        vertex_id = type + "_" + sub_type + "_" + id
        vertex = graph.Vertex(vertex_id, prop)
        e_g_manager.graph.add_vertex(vertex)

        return vertex

    def _update_edge_to_graph(self, e_g_manager, src_id, trgt_id, label):
        edge = graph.Edge(src_id, trgt_id, label, {})
        e_g_manager.graph.add_edge(edge)
        return edge
