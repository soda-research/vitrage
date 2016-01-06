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

from vitrage.common.constants import SyncMode
from vitrage.synchronizer.synchronizer import Synchronizer


LOG = log.getLogger(__name__)


class VitrageSynchronizerService(os_service.Service):

    def __init__(self, event_queue):
        super(VitrageSynchronizerService, self).__init__()
        self.queue = event_queue

    def start(self):
        LOG.info("Start VitrageSynchronizerService")

        super(VitrageSynchronizerService, self).start()

        synchronizer = Synchronizer(self.queue)

        # TODO(Alexey): remove this get_all call because it's supposed
        #               to be called Automatically from the synchronizer
        synchronizer.get_all(sync_mode=SyncMode.INIT_SNAPSHOT)

        LOG.info("Finish start VitrageSynchronizerService")

    def stop(self):
        LOG.info("Stop VitrageSynchronizerService")

        super(VitrageSynchronizerService, self).stop()

        LOG.info("Finish stop VitrageSynchronizerService")
