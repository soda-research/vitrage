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


class VertexConstants(object):
    TYPE = 'TYPE'
    SUB_TYPE = 'SUB_TYPE'
    ID = 'ID'
    IS_VERTEX_DELETED = 'IS_VERTEX_DELETED'
    VERTEX_DELETION_TIMESTAMP = 'VERTEX_DELETION_TIMESTAMP'
    STATE = 'STATE'
    PROJECT = 'PROJECT'
    UPDATE_TIMESTAMP = 'UPDATE_TIMESTAMP'


class EdgeConstants(object):
    RELATION_NAME = 'RELATION_NAME'
    IS_EDGE_DELETED = 'IS_EDGE_DELETED'
    EDGE_DELETION_TIMESTAMP = 'EDGE_DELETION_TIMESTAMP'


class EdgeLabels(object):
    ON = 'on'
    CONTAINS = 'contains'


class SynchronizerMessageMode(object):
    SNAPSHOT = 'snapshot'
    INIT_SNAPSHOT = 'init_snapshot'
    UPDATE = 'update'
