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
from vitrage.datasources import utils

from vitrage.common.constants import DatasourceAction
from vitrage.common.utils import spawn

from vitrage.entity_graph.consistency.consistency_enforcer import\
    ConsistencyEnforcer

LOG = log.getLogger(__name__)


class Scheduler(object):

    def __init__(self, conf, graph, driver_exec, persist):
        super(Scheduler, self).__init__()
        self.conf = conf
        self.graph = graph
        self.driver_exec = driver_exec
        self.persist = persist
        self.consistency = ConsistencyEnforcer(conf, graph)
        self.periodic = None

    def start_periodic_tasks(self):
        thread_num = len(utils.get_pull_drivers_names(self.conf))
        thread_num += 2  # for consistency and get_all
        self.periodic = periodics.PeriodicWorker.create(
            [], executor_factory=lambda: ThreadPoolExecutor(
                max_workers=thread_num))

        self._add_consistency_timer()
        self._add_datasource_timers()
        spawn(self.periodic.start)

    def _add_consistency_timer(self):
        spacing = self.conf.datasources.snapshots_interval

        @periodics.periodic(spacing=spacing)
        def consistency_periodic():
            try:
                self.consistency.periodic_process()
            except Exception:
                LOG.exception('run_consistency failed.')

        self.periodic.add(consistency_periodic)
        LOG.info("added consistency_periodic (spacing=%s)", spacing)

    def _add_datasource_timers(self):
        spacing = self.conf.datasources.snapshots_interval

        @periodics.periodic(spacing=spacing)
        def get_all_periodic():
            self.driver_exec.snapshot_get_all(DatasourceAction.SNAPSHOT)

        self.periodic.add(get_all_periodic)
        LOG.info("added get_all_periodic (spacing=%s)", spacing)

        driver_names = utils.get_pull_drivers_names(self.conf)
        for d_name in driver_names:
            spacing = self.conf[d_name].changes_interval

            @periodics.periodic(spacing=spacing)
            def get_changes_periodic():
                self.driver_exec.get_changes(d_name)

            self.periodic.add(get_changes_periodic)
            LOG.info("added get_changes_periodic %s (spacing=%s)",
                     d_name, spacing)
