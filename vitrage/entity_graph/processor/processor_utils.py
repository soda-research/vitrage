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

from dateutil import parser
from vitrage.common.constants import EdgeProperties as EProps
from vitrage.common.constants import VertexProperties as VProps
from vitrage.graph import Edge
from vitrage.graph import Vertex


def is_newer_vertex(prev_vertex, new_vertex):
    prev_timestamp = prev_vertex.get(VProps.SAMPLE_TIMESTAMP)
    if not prev_timestamp:
        return True
    prev_time = parser.parse(prev_timestamp)

    new_timestamp = new_vertex[VProps.SAMPLE_TIMESTAMP]
    if not new_timestamp:
        return False
    new_time = parser.parse(new_timestamp)

    return prev_time <= new_time


def is_deleted(item):
    return item and \
        (isinstance(item, Vertex) and item.get(VProps.IS_DELETED, False)) or\
        (isinstance(item, Edge) and item.get(EProps.IS_DELETED, False))
