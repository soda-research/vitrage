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
from oslo_service import service as os_service

from vitrage.entity_graph.consistency.consistency_enforcer \
    import ConsistencyEnforcer
from vitrage.entity_graph import EVALUATOR_TOPIC
from vitrage.messaging import VitrageNotifier

LOG = log.getLogger(__name__)


class VitrageConsistencyService(os_service.Service):

    def __init__(self,
                 conf,
                 entity_graph):
        super(VitrageConsistencyService, self).__init__()
        self.conf = conf
        self.entity_graph = entity_graph
        self.actions_notifier = VitrageNotifier(
            conf, 'vitrage_consistency', EVALUATOR_TOPIC)

    def start(self):
        LOG.info("Vitrage Consistency Service - Starting...")

        super(VitrageConsistencyService, self).start()

        consistency_enf = ConsistencyEnforcer(
            conf=self.conf,
            actions_callback=self.actions_notifier.notify,
            entity_graph=self.entity_graph)
        self.tg.add_timer(self.conf.datasources.snapshots_interval,
                          consistency_enf.periodic_process,
                          initial_delay=60 +
                          self.conf.datasources.snapshots_interval)

        LOG.info("Vitrage Consistency Service - Started!")

    def stop(self, graceful=False):
        LOG.info("Vitrage Consistency Service - Stopping...")

        super(VitrageConsistencyService, self).stop()

        LOG.info("Vitrage Consistency Service - Stopped!")
