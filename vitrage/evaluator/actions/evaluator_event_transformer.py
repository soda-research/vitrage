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

from vitrage.common.constants import EventAction
from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common.constants import VertexProperties as VProps
from vitrage.common.exception import VitrageTransformerError
from vitrage.evaluator.actions.recipes.action_steps import UPDATE_VERTEX
from vitrage.evaluator.actions.recipes.base import EVALUATOR_EVENT_TYPE
from vitrage.graph import Vertex
from vitrage.synchronizer.plugins import transformer_base


LOG = logging.getLogger(__name__)


class EvaluatorEventTransformer(transformer_base.TransformerBase):

    def __init__(self, transformers):
        self.transformers = transformers

    def _create_entity_vertex(self, event):

        event_type = event[EVALUATOR_EVENT_TYPE]

        if event_type == UPDATE_VERTEX:

            properties = {
                VProps.VITRAGE_STATE: event[VProps.VITRAGE_STATE],
                VProps.UPDATE_TIMESTAMP: event[SyncProps.SAMPLE_DATE]
            }
            return Vertex(event[VProps.VITRAGE_ID], properties)

        return None

    def _create_neighbors(self, event):
        return []

    def _extract_action_type(self, event):

        event_type = event[EVALUATOR_EVENT_TYPE]

        if event_type == UPDATE_VERTEX:
            return EventAction.UPDATE_ENTITY

        raise VitrageTransformerError(
            'Invalid Evaluator event type: (%s)' % event_type)

    def extract_key(self, entity_event):
        pass

    def key_values(self, mutable_fields=[]):
        pass

    def create_placeholder_vertex(self, properties={}):
        LOG.info('Evaluator does not create placeholders')
