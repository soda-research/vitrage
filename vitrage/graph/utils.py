# Copyright 2016 - Alcatel-Lucent
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

from vitrage.common.constants import EdgeProperties as EConst
from vitrage.common.constants import VertexProperties as VConst
from vitrage.graph import Edge
from vitrage.graph import Vertex


def create_vertex(vertex_id,
                  entity_id=None,
                  entity_type=None,
                  entity_subtype=None,
                  entity_project=None,
                  entity_state=None,
                  is_deleted=False,
                  update_timestamp=None,
                  is_placeholder=False,
                  metadata=None):
    """A builder to create a vertex

    :param vertex_id:
    :type vertex_id: str
    :param entity_id:
    :type entity_id: str
    :param entity_type:
    :type entity_type: str
    :param entity_subtype:
    :type entity_subtype: str
    :param entity_project:
    :type entity_project: str
    :param entity_state:
    :type entity_state: str
    :param is_deleted:
    :type is_deleted: boolean
    :param update_timestamp:
    :type update_timestamp: str
    :param metadata:
    :type metadata: dict
    :param is_placeholder:
    :type is_placeholder: boolean
    :return:
    :rtype: Vertex
    """

    properties = {
        VConst.ID: entity_id,
        VConst.PROJECT: entity_project,
        VConst.STATE: entity_state,
        VConst.SUB_TYPE: entity_subtype,
        VConst.TYPE: entity_type,
        VConst.IS_DELETED: is_deleted,
        VConst.UPDATE_TIMESTAMP: update_timestamp,
        VConst.IS_PLACEHOLDER: is_placeholder
    }
    if metadata:
        properties.update(metadata)
    properties = dict(
        (k, v) for k, v in properties.iteritems() if v is not None)
    vertex = Vertex(vertex_id=vertex_id, properties=properties)
    return vertex


def create_edge(source_id,
                target_id,
                relation_type,
                is_deleted=False,
                update_timestamp=None,
                metadata=None):
    """A builder to create an edge

    :param source_id:
    :type source_id: str
    :param target_id:
    :type target_id: str
    :param relation_type:
    :type relation_type: str
    :param is_deleted:
    :type is_deleted: str
    :param metadata:
    :type metadata: dict
    :return:
    :rtype: Edge
    """
    properties = {
        EConst.UPDATE_TIMESTAMP: update_timestamp,
        EConst.IS_DELETED: is_deleted,
        EConst.RELATION_NAME: relation_type,
    }
    if metadata:
        properties.update(metadata)
    properties = dict(
        (k, v) for k, v in properties.iteritems() if v is not None)
    edge = Edge(source_id=source_id,
                target_id=target_id,
                label=relation_type,
                properties=properties)
    return edge


def check_filter(data, attr_filter):
    """Check attr_filter against data

    :param data: a dictionary of field_name: value
    :param attr_filter: a dictionary of either
    field_name : value (mandatory)
    field_name : list of values - data[field_name] must match ANY of the values
    :rtype: bool
    """
    if not attr_filter:
        return True
    for key, content in attr_filter.items():
        if not isinstance(content, list):
            content = [content]
        if not data[key] in content:
            return False
    return True
