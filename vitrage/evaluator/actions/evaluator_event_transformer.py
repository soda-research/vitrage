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

from vitrage.common.constants import EdgeLabels
from vitrage.common.constants import EdgeProperties as EProps
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import EventAction
from vitrage.common.constants import VertexProperties as VProps
from vitrage.common.exception import VitrageTransformerError
from vitrage.evaluator.actions.recipes.action_steps import ADD_EDGE
from vitrage.evaluator.actions.recipes.action_steps import ADD_VERTEX
from vitrage.evaluator.actions.recipes.action_steps import REMOVE_EDGE
from vitrage.evaluator.actions.recipes.action_steps import REMOVE_VERTEX
from vitrage.evaluator.actions.recipes.action_steps import UPDATE_VERTEX
from vitrage.evaluator.actions.recipes.base import EVALUATOR_EVENT_TYPE
from vitrage.evaluator.template_fields import TemplateFields as TFields
import vitrage.graph.utils as graph_utils
from vitrage.graph import Vertex
from vitrage.synchronizer.plugins import transformer_base


LOG = logging.getLogger(__name__)


VITRAGE_TYPE = 'vitrage'


class EvaluatorEventTransformer(transformer_base.TransformerBase):

    def __init__(self, transformers):
        self.transformers = transformers

    def _create_entity_vertex(self, event):

        event_type = event[EVALUATOR_EVENT_TYPE]

        if event_type == UPDATE_VERTEX:
            properties = {
                VProps.VITRAGE_STATE: event[VProps.VITRAGE_STATE],
                VProps.UPDATE_TIMESTAMP: event[VProps.UPDATE_TIMESTAMP],
                VProps.SAMPLE_TIMESTAMP: event[VProps.SAMPLE_TIMESTAMP]
            }
            return Vertex(event[VProps.VITRAGE_ID], properties)

        if event_type in [ADD_VERTEX, REMOVE_VERTEX]:

            metadata = {
                VProps.UPDATE_TIMESTAMP: event[VProps.UPDATE_TIMESTAMP],
                VProps.SAMPLE_TIMESTAMP: event[VProps.SAMPLE_TIMESTAMP],
                VProps.NAME: event[TFields.ALARM_NAME],
                VProps.SEVERITY: event[TFields.SEVERITY],
                VProps.STATE: event[VProps.STATE]
            }
            return graph_utils.create_vertex(
                self.extract_key(event),
                entity_category=EntityCategory.ALARM,
                entity_type=VITRAGE_TYPE,
                sample_timestamp=event[VProps.SAMPLE_TIMESTAMP],
                update_timestamp=event[VProps.UPDATE_TIMESTAMP],
                metadata=metadata)

        return None

    def _create_neighbors(self, event):

        event_type = event[EVALUATOR_EVENT_TYPE]

        if event_type in [ADD_EDGE, REMOVE_EDGE]:

            relation_edge = graph_utils.create_edge(
                source_id=event[TFields.SOURCE],
                target_id=event[TFields.TARGET],
                relationship_type=event[EProps.RELATIONSHIP_TYPE],
                update_timestamp=event[EProps.UPDATE_TIMESTAMP])

            return [transformer_base.Neighbor(None, relation_edge)]

        if event_type == ADD_VERTEX:

            relation_edge = graph_utils.create_edge(
                source_id=self.extract_key(event),
                target_id=event[TFields.TARGET],
                relationship_type=EdgeLabels.ON,
                update_timestamp=event[EProps.UPDATE_TIMESTAMP])

            neighbor_props = {
                VProps.IS_PLACEHOLDER: True,
                VProps.UPDATE_TIMESTAMP: event[VProps.UPDATE_TIMESTAMP],
                VProps.SAMPLE_TIMESTAMP: event[VProps.SAMPLE_TIMESTAMP]
            }
            neighbor = Vertex(event[TFields.TARGET], neighbor_props)
            return [transformer_base.Neighbor(neighbor, relation_edge)]

        return []

    def _extract_action_type(self, event):

        event_type = event[EVALUATOR_EVENT_TYPE]

        if event_type == UPDATE_VERTEX:
            return EventAction.UPDATE_ENTITY
        if event_type == ADD_VERTEX:
            return EventAction.CREATE_ENTITY
        if event_type == REMOVE_VERTEX:
            return EventAction.DELETE_ENTITY
        if event_type == ADD_EDGE:
            return EventAction.UPDATE_RELATIONSHIP
        if event_type == REMOVE_EDGE:
            return EventAction.DELETE_RELATIONSHIP

        raise VitrageTransformerError(
            'Invalid Evaluator event type: (%s)' % event_type)

    def extract_key(self, event):
        key_fields = self.key_values(event[TFields.ALARM_NAME],
                                     event[TFields.TARGET])
        return transformer_base.build_key(key_fields)

    def key_values(self, *args):
        return (EntityCategory.ALARM, VITRAGE_TYPE) + args

    def create_placeholder_vertex(self, **kwargs):
        LOG.info('Evaluator does not create placeholders')
