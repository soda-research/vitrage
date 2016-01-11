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
from oslo_utils import importutils
from vitrage.common.constants import VertexProperties
from vitrage.common.exception import VitrageTransformerError

LOG = logging.getLogger(__name__)


class TransformerManager(object):

    def __init__(self):
        self.transformers = self.register_transformer_classes()

    @staticmethod
    def register_transformer_classes():

        transformers = {}

        transformers['nova.instance'] = importutils.import_object(
            'vitrage.entity_graph.transformer.nova_transformers.'
            + 'InstanceTransformer')

        transformers['nova.host'] = importutils.import_object(
            'vitrage.entity_graph.transformer.nova_transformers.'
            + 'HostTransformer')

        transformers['nova.zone'] = importutils.import_object(
            'vitrage.entity_graph.transformer.nova_transformers.'
            + 'ZoneTransformer')

        transformers['nova.zone'] = importutils.import_object(
            'vitrage.entity_graph.transformer.nova_transformers.'
            + 'ZoneTransformer')

        return transformers

    def get_transformer(self, key):

        try:
            transformer = self.transformers[key]
        except KeyError:
            raise VitrageTransformerError(
                'Could not get transformer instance for %s' % key)

        return transformer

    def transform(self, entity_event):

        try:
            sync_type = entity_event['sync_type']
        except KeyError:
            raise VitrageTransformerError(
                'Entity Event must contains sync_type field.')

        return self.get_transformer(sync_type).transform(entity_event)

    def key_fields(self, vertex):

        try:
            e_sub_type = vertex[VertexProperties.SUBTYPE]
        except KeyError:
            raise VitrageTransformerError(
                'Vertex must contains SUB_TYPE field.')

        return self.get_transformer(e_sub_type).key_fields()

    def extract_key(self, entity_event):

        try:
            sync_type = entity_event['sync_type']
        except KeyError:
            raise VitrageTransformerError(
                'Entity Event must contains sync_type field.')

        return self.get_transformer(sync_type).extract_key()
