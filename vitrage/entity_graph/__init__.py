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

from oslo_log import log
from oslo_service import service as os_service

from vitrage.entity_graph.processor import processor as proc


LOG = log.getLogger(__name__)


class VitrageEntityGraphService(os_service.Service):

    def __init__(self, event_queue):
        super(VitrageEntityGraphService, self).__init__()
        self.queue = event_queue
        self.processor = proc.Processor()

    def start(self):
        LOG.info("Start VitrageEntityGraphService")

        super(VitrageEntityGraphService, self).start()

        while True:
            event = self.queue.get()
            self.processor.process_event(event)

        LOG.info("Finish start VitrageEntityGraphService")

        # Add a dummy thread to have wait() working
        # self.tg.add_timer(604800, lambda: None)

    def stop(self):
        LOG.info("Stop VitrageEntityGraphService")

        super(VitrageEntityGraphService, self).stop()

        LOG.info("Finish stop VitrageEntityGraphService")
