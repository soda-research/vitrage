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
from oslo_log import log
import time

from vitrage.common.constants import VertexProperties as VProps

LOG = log.getLogger(__name__)


class VitrageInit(object):
    STARTED = 'started'
    RECEIVED_ALL_END_MESSAGES = 'received_all_end_messages'
    FINISHED = 'finished'

    def __init__(self, conf, graph=None, evaluator=None, template_loader=None):
        self.conf = conf
        self.graph = graph
        self.evaluator = evaluator
        self.template_loader = template_loader
        self.status = self.STARTED
        self.end_messages = {}

    def initializing_process(self, on_end_messages_func):
        try:
            LOG.info('Init Started')

            if not self._wait_for_all_end_messages():
                LOG.warning('Initialization  - max retries reached %s',
                            self.end_messages)
            else:
                LOG.info('Initialization - All end messages were received')

            on_end_messages_func()

            self.evaluator.start()
            if self.template_loader:
                self.template_loader.start()

            # TODO(idan_hefetz) As vitrage is not yet persistent, there aren't
            # TODO(idan_hefetz) any deduced alarms to be removed during init
            # if not self._wait_for_action(self.evaluator_queue.empty):
            #     LOG.error('Evaluator Queue Not Empty')
            # self._mark_old_deduced_alarms_as_deleted(timestamp, self.graph,
            #                                          self.evaluator_queue)
            self.status = self.FINISHED

            LOG.info('Init Finished')
        except Exception as e:
            LOG.exception('Init Failed: %s', e)

    def handle_end_message(self, vertex):
        self.end_messages[vertex[VProps.VITRAGE_TYPE]] = True

        if len(self.end_messages) == len(self.conf.datasources.types):
            self.status = self.RECEIVED_ALL_END_MESSAGES

    def _wait_for_all_end_messages(self):
        return self._wait_for_action(
            lambda: self.status == self.RECEIVED_ALL_END_MESSAGES)

    def _wait_for_action(self, function):
        count_retries = 0
        while True:
            if count_retries >= \
                    self.conf.consistency.initialization_max_retries:
                return False

            if function():
                return True

            count_retries += 1
            time.sleep(self.conf.consistency.initialization_interval)

    # def _mark_old_deduced_alarms_as_deleted(self, timestamp,graph,out_queue):
    #     query = {
    #         'and': [
    #             {'==': {VProps.VITRAGE_CATEGORY: EntityCategory.ALARM}},
    #             {'==': {VProps.VITRAGE_TYPE: VProps.VITRAGE_TYPE}},
    #             {'<': {VProps.VITRAGE_SAMPLE_TIMESTAMP: timestamp}}
    #         ]
    #     }
    #     old_deduced_alarms = graph.get_vertices(query_dict=query)
    #     self._push_events_to_queue(old_deduced_alarms,
    #                                GraphAction.DELETE_ENTITY,
    #                                out_queue)
    #
    # def _push_events_to_queue(self, vertices, action, out_queue):
    #     for vertex in vertices:
    #         event = {
    #             DSProps.ENTITY_TYPE: CONSISTENCY_DATASOURCE,
    #             DSProps.DATASOURCE_ACTION: DatasourceAction.UPDATE,
    #             DSProps.SAMPLE_DATE: str(utcnow()),
    #             DSProps.EVENT_TYPE: action,
    #             VProps.VITRAGE_ID: vertex[VProps.VITRAGE_ID],
    #             VProps.ID: vertex.get(VProps.ID, None),
    #             VProps.VITRAGE_TYPE: vertex[VProps.VITRAGE_TYPE],
    #             VProps.VITRAGE_CATEGORY: vertex[VProps.VITRAGE_CATEGORY],
    #             VProps.IS_REAL_VITRAGE_ID: True
    #         }
    #         out_queue.put(event)
