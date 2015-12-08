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
from vitrage.common.constants import VertexConstants as vertex_cons
from vitrage.entity_graph.transformer import base

LOG = logging.getLogger(__name__)

KEY_SEPARATOR = ':'

ENTITY_TYPE = 'RESOURCE'
INSTANCE_SUB_TYPE = 'nova.instance'
HOST_SUB_TYPE = 'nova.host'


class InstanceTransformer(base.Transformer):

    # # Fields returned from Nova Instance snapshot
    ENTITY_ID_DICT = {'snapshot': 'id',
                      'init_snapshot': 'id',
                      'update': 'instance_id'}

    def transform(self, entity_event):
        pass

    def key_fields(self):
        return [vertex_cons.TYPE, vertex_cons.SUB_TYPE, vertex_cons.ID]

    def extract_key(self, entity_event):

        sync_mode = entity_event['sync_mode']
        return KEY_SEPARATOR.join(
            [ENTITY_TYPE,
             INSTANCE_SUB_TYPE,
             entity_event[self.ENTITY_ID_DICT[sync_mode]]])
