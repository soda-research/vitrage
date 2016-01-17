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

import datetime

from oslo_log import log
from oslo_service import service as os_service

from vitrage.entity_graph.processor import processor as proc


LOG = log.getLogger(__name__)


class VitrageGraphService(os_service.Service):

    def __init__(self, event_queue, entity_graph):
        super(VitrageGraphService, self).__init__()
        self.queue = event_queue
        self.processor = proc.Processor(e_graph=entity_graph)

    def start(self):
        LOG.info("Start VitrageGraphService")

        super(VitrageGraphService, self).start()

        self.tg.add_timer(1.0, self._process_event_non_blocking)

        LOG.info("Finish start VitrageGraphService")

    def stop(self):
        LOG.info("Stop VitrageGraphService")

        # TODO(Alexey): check if we need this command here
        self.tg.stop_timers()

        super(VitrageGraphService, self).stop()

        LOG.info("Finish stop VitrageGraphService")

    def _process_events(self):
        while True:
            self._process_event_non_blocking()

    def _process_event_non_blocking(self):
        """Process events received from the synchronizer

        In order that other services (such as graph consistency, api handler)
        could get work time as well, the work processing performed for 2
        seconds and goes to sleep for 1 second. if there are more events in
        the queue they are done when timer returns.
        """

        start_time = datetime.datetime.now()
        while not self.queue.empty():
            time_delta = datetime.datetime.now() - start_time
            if time_delta.total_seconds() >= 2:
                break

            try:
                event = self.queue.get()
                LOG.debug("got event: %s" % event)
                self.processor.process_event(event)
            except Exception as error:
                LOG.error("Exception: %s", error)
