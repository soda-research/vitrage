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

from vitrage.common.constants import VertexProperties as VProps
from vitrage.entity_graph.states.normalizator_base import ImportantStates
from vitrage.entity_graph.states.normalizator_base import NormalizatorBase
from vitrage.entity_graph.states.normalized_resource_state \
    import NormalizedResourceState


class ResourceNormalizator(NormalizatorBase):

    def __init__(self):
        super(ResourceNormalizator, self).__init__()

    def important_states(self):
        return ImportantStates(NormalizedResourceState.UNRECOGNIZED,
                               NormalizedResourceState.UNDEFINED)

    def state_properties(self):
        return [VProps.STATE, VProps.VITRAGE_STATE]

    def set_undefined_state(self, new_vertex):
        new_vertex[VProps.AGGREGATED_STATE] = NormalizedResourceState.UNDEFINED

    def set_aggregated_state(self, new_vertex, normalized_state):
        new_vertex[VProps.AGGREGATED_STATE] = normalized_state

    def default_states(self):
        return [(NormalizedResourceState.UNDEFINED, 0)]

    def get_state_class_instance(self):
        return NormalizedResourceState()
