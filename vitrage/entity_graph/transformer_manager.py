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

from oslo_log import log as logging
from oslo_utils import importutils

from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common.exception import VitrageTransformerError

LOG = logging.getLogger(__name__)


class TransformerManager(object):

    def __init__(self, conf):
        self.transformers = self.register_transformer_classes(conf)

    @staticmethod
    def register_transformer_classes(conf):

        transformers = {}
        for plugin in conf.synchronizer_plugins.plugin_type:
                transformers[plugin] = importutils.import_object(
                    conf.synchronizer_plugins[plugin]['transformer'],
                    transformers)
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
            sync_type = entity_event[SyncProps.SYNC_TYPE]
        except KeyError:
            raise VitrageTransformerError(
                'Entity Event must contains sync_type field.')

        return self.get_transformer(sync_type).transform(entity_event)

    def extract_key(self, entity_event):

        try:
            sync_type = entity_event[SyncProps.SYNC_TYPE]
        except KeyError:
            raise VitrageTransformerError(
                'Entity Event must contains sync_type field.')

        return self.get_transformer(sync_type).extract_key()
