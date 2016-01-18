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


class VertexProperties(object):
    CATEGORY = 'category'
    TYPE = 'type'
    ID = 'id'
    IS_DELETED = 'is_deleted'
    STATE = 'state'
    PROJECT_ID = 'project_id'
    UPDATE_TIMESTAMP = 'update_timestamp'
    NAME = 'name'
    IS_PLACEHOLDER = 'is_placeholder'


class EdgeProperties(object):
    RELATIONSHIP_NAME = 'relationship_name'
    IS_DELETED = 'is_deleted'
    UPDATE_TIMESTAMP = 'update_timestamp'


class EdgeLabels(object):
    ON = 'on'
    CONTAINS = 'contains'


class SyncMode(object):
    SNAPSHOT = 'snapshot'
    INIT_SNAPSHOT = 'init_snapshot'
    UPDATE = 'update'


class EntityTypes(object):
    RESOURCE = 'RESOURCE'


class EventAction(object):
    CREATE = 'create'
    DELETE = 'delete'
    UPDATE = 'update'
