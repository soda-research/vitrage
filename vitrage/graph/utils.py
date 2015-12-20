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

from vitrage.common.constants import EdgeConstants as EConst
from vitrage.common.constants import VertexConstants as VConst
from vitrage.graph import Edge
from vitrage.graph import Vertex


def create_vertex(vertex_id,
                  entity_id=None,
                  entity_type=None,
                  entity_subtype=None,
                  entity_project=None,
                  entity_state=None,
                  is_deleted=False,
                  deletion_timestamp=None,
                  update_timestamp=None,
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
    :type is_deleted: str
    :param deletion_timestamp:
    :type deletion_timestamp: str
    :param update_timestamp:
    :type update_timestamp: str
    :param metadata:
    :type metadata: dict
    :return:
    :rtype: Vertex
    """

    properties = {
        VConst.VERTEX_DELETION_TIMESTAMP: deletion_timestamp,
        VConst.ID: entity_id,
        VConst.PROJECT: entity_project,
        VConst.STATE: entity_state,
        VConst.SUB_TYPE: entity_subtype,
        VConst.TYPE: entity_type,
        VConst.IS_VERTEX_DELETED: is_deleted,
        VConst.UPDATE_TIMESTAMP: update_timestamp
    }
    if metadata:
        properties.update(metadata)
    properties = dict((k, v) for k, v in properties.iteritems() if v)
    vertex = Vertex(vertex_id=vertex_id, properties=properties)
    return vertex


def create_edge(source_id,
                target_id,
                relation_type,
                is_deleted=False,
                deletion_timestamp=None,
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
    :param deletion_timestamp:
    :type deletion_timestamp: str
    :param metadata:
    :type metadata: dict
    :return:
    :rtype: Edge
    """
    properties = {
        EConst.EDGE_DELETION_TIMESTAMP: deletion_timestamp,
        EConst.IS_EDGE_DELETED: is_deleted,
        EConst.RELATION_NAME: relation_type,
    }
    if metadata:
        properties.update(metadata)
    properties = dict((k, v) for k, v in properties.iteritems() if v)
    edge = Edge(source_id=source_id,
                target_id=target_id,
                label=relation_type,
                properties=properties)
    return edge
