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

from vitrage.common.constants import EntityType
from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common.exception import VitrageTransformerError
from vitrage.entity_graph.transformer.plugins.nagios import NagiosAlarm
from vitrage.entity_graph.transformer.plugins.nova.host import Host
from vitrage.entity_graph.transformer.plugins.nova.instance import Instance
from vitrage.entity_graph.transformer.plugins.nova.zone import Zone
from vitrage.entity_graph.transformer.plugins.static_physical \
    import StaticPhysical

LOG = logging.getLogger(__name__)


class TransformerManager(object):

    def __init__(self):
        self.transformers = self.register_transformer_classes()

    @staticmethod
    def register_transformer_classes():

        transformers = {}

        transformers[EntityType.NOVA_INSTANCE] = importutils.import_object(
            "%s.%s" % (Instance.__module__,
                       Instance.__name__), transformers)

        transformers[EntityType.NOVA_HOST] = importutils.import_object(
            "%s.%s" % (Host.__module__, Host.__name__),
            transformers)

        transformers[EntityType.NOVA_ZONE] = importutils.import_object(
            "%s.%s" % (Zone.__module__, Zone.__name__),
            transformers)

        transformers[EntityType.SWITCH] = importutils.import_object(
            "%s.%s" % (StaticPhysical.__module__, StaticPhysical.__name__),
            transformers)

        transformers[EntityType.NAGIOS] = importutils.import_object(
            "%s.%s" % (NagiosAlarm.__module__, NagiosAlarm.__name__),
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
