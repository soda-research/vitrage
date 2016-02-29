# Copyright 2015 - Alcatel-Lucent
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


class VertexProperties(object):
    CATEGORY = 'category'
    TYPE = 'type'
    ID = 'id'
    IS_DELETED = 'is_deleted'
    STATE = 'state'
    VITRAGE_STATE = 'vitrage_state'
    AGGREGATED_STATE = 'aggregated_state'
    PROJECT_ID = 'project_id'
    UPDATE_TIMESTAMP = 'update_timestamp'
    NAME = 'name'
    IS_PLACEHOLDER = 'is_placeholder'
    SEVERITY = 'severity'
    VITRAGE_ID = 'vitrage_id'
    INFO = 'info'


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


class EntityCategory(object):
    RESOURCE = 'RESOURCE'
    ALARM = 'ALARM'


class SynchronizerProperties(object):
    SYNC_TYPE = 'sync_type'
    SYNC_MODE = 'sync_mode'
    SAMPLE_DATE = 'sample_date'
    EVENT_TYPE = 'event_type'


class EntityType(object):
    OPENSTACK_NODE = 'openstack.node'
    NOVA_INSTANCE = 'nova.instance'
    NOVA_HOST = 'nova.host'
    NOVA_ZONE = 'nova.zone'
    SWITCH = 'switch'
    NAGIOS = 'nagios'
    VITRAGE = 'vitrage'


class EventAction(object):
    CREATE = 'create'
    DELETE = 'delete'
    UPDATE = 'update'
    END_MESSAGE = 'end_message'
