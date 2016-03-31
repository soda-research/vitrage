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

from vitrage.synchronizer.plugins.base.resource.transformer import \
    BaseResourceTransformer


class PortTransformer(BaseResourceTransformer):

    def __init__(self, transformers):
        super(PortTransformer, self).__init__(transformers)

    def _create_entity_key(self, entity_event):
        pass

    def create_placeholder_vertex(self, **kwargs):
        pass

    def _create_snapshot_entity_vertex(self, entity_event):
        pass

    def _create_update_entity_vertex(self, entity_event):
        pass

    def _create_neighbors(self, entity_event):
        pass

    def _extract_action_type(self, entity_event):
        pass
