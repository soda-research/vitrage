# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import copy
from driver import Edge
from driver import Vertex


def filter_items(items, attr_filter):
    def is_filter_match(item):
        for key, content in attr_filter.items():
            if not isinstance(content, list):
                content = [content]
            if not item[key] in content:
                return False
        return True

    if attr_filter:
        return filter(is_filter_match, items)
    else:
        return items


def edge_copy(source_id, target_id, label, data):
    return Edge(source_id=source_id, target_id=target_id,
                label=label, properties=copy.copy(data))


def vertex_copy(v_id, data):
    return Vertex(vertex_id=v_id, properties=copy.copy(data))
