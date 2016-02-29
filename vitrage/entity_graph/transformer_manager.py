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

from vitrage.common.constants import EntityType
from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common.exception import VitrageTransformerError
from vitrage.synchronizer.plugins.nagios.transformer import NagiosTransformer
from vitrage.synchronizer.plugins.nova.host.transformer import HostTransformer
from vitrage.synchronizer.plugins.nova.instance.transformer import \
    InstanceTransformer
from vitrage.synchronizer.plugins.nova.zone.transformer import ZoneTransformer
from vitrage.synchronizer.plugins.static_physical.transformer import \
    StaticPhysicalTransformer

LOG = logging.getLogger(__name__)


class TransformerManager(object):

    def __init__(self):
        self.transformers = self._register_transformer_classes()

    @staticmethod
    def _register_transformer_classes():

        transformers = {}

        transformers[EntityType.NOVA_INSTANCE] = importutils.import_object(
            "%s.%s" % (InstanceTransformer.__module__,
                       InstanceTransformer.__name__),
            transformers)

        transformers[EntityType.NOVA_HOST] = importutils.import_object(
            "%s.%s" % (HostTransformer.__module__, HostTransformer.__name__),
            transformers)

        transformers[EntityType.NOVA_ZONE] = importutils.import_object(
            "%s.%s" % (ZoneTransformer.__module__, ZoneTransformer.__name__),
            transformers)

        transformers[EntityType.SWITCH] = importutils.import_object(
            "%s.%s" % (StaticPhysicalTransformer.__module__,
                       StaticPhysicalTransformer.__name__),
            transformers)

        transformers[EntityType.NAGIOS] = importutils.import_object(
            "%s.%s" % (NagiosTransformer.__module__,
                       NagiosTransformer.__name__),
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
