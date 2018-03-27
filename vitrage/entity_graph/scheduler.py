# Copyright 2018 - Nokia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from concurrent.futures import ThreadPoolExecutor
from futurist import periodics

from oslo_log import log
from vitrage.common.utils import spawn

from vitrage.entity_graph.consistency.consistency_enforcer import\
    ConsistencyEnforcer
from vitrage.persistency.graph_persistor import GraphPersistor

LOG = log.getLogger(__name__)


class Scheduler(object):

    def __init__(self,
                 conf,
                 graph):
        super(Scheduler, self).__init__()
        self.conf = conf
        self.graph = graph
        self.graph_persistor = GraphPersistor(conf) if \
            self.conf.persistency.enable_persistency else None
        self.consistency = ConsistencyEnforcer(conf, graph)
        self.periodic = None

    def start_periodic_tasks(self):
        self.periodic = periodics.PeriodicWorker.create(
            [], executor_factory=lambda: ThreadPoolExecutor(max_workers=10))

        self.add_persistor_timer()
        self.add_consistency_timer()
        spawn(self.periodic.start)

    def add_persistor_timer(self):
        spacing = self.conf.persistency.graph_persistency_interval

        @periodics.periodic(spacing=spacing)
        def persist():
            if self.graph_persistor:
                try:
                    self.graph_persistor.store_graph(graph=self.graph)
                except Exception as e:
                    LOG.exception('persist failed %s', e)

        self.periodic.add(persist)
        LOG.info("periodic task - persistor %s", spacing)

    def add_consistency_timer(self):
        spacing = self.conf.datasources.snapshots_interval

        @periodics.periodic(spacing=spacing)
        def run_consistency():
            try:
                self.consistency.periodic_process()
            except Exception as e:
                LOG.exception('run_consistency failed %s', e)

        self.periodic.add(run_consistency)
        LOG.info("periodic task - run_consistency %s", spacing)
