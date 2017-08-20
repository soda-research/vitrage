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
import time

from oslo_log import log
from oslo_service import service as os_service
from vitrage.common.constants import DatasourceAction

LOG = log.getLogger(__name__)


class DatasourceService(os_service.Service):
    def __init__(self, conf, registered_datasources, send_to_queue_func):
        super(DatasourceService, self).__init__()
        self.conf = conf
        self.registered_datasources = registered_datasources
        self.send_to_queue = send_to_queue_func


class SnapshotsService(DatasourceService):
    def __init__(self, conf, registered_datasources, callback_function):
        super(SnapshotsService, self).__init__(conf,
                                               registered_datasources,
                                               callback_function)

    def start(self):
        LOG.info("Vitrage datasources Snapshot Service - Starting...")
        super(SnapshotsService, self).start()

        standard_interval = self.conf.datasources.snapshots_interval
        fault_interval = self.conf.datasources.snapshot_interval_on_fault
        init_ttl = self.conf.consistency.initialization_max_retries * \
            self.conf.consistency.initialization_interval

        for ds_driver in self.registered_datasources.values():
            callback = self.entities_to_queue(
                ds_driver,
                DatasourceAction.INIT_SNAPSHOT,
                fault_interval,
                init_ttl)
            self.tg.add_thread(callback)

            callback = self.entities_to_queue(
                ds_driver,
                DatasourceAction.SNAPSHOT,
                fault_interval,
                standard_interval)
            self.tg.add_timer(standard_interval, callback, standard_interval)

        LOG.info('Vitrage datasources Snapshot Service - Started!')

    def entities_to_queue(self, driver, action, fault_interval, timeout):
        def _entities_to_queue():
            endtime = time.time() + timeout
            while time.time() < endtime:
                try:
                    LOG.info('Driver %s - %s', type(driver).__name__, action)
                    items = driver.get_all(action)
                    for entity in items:
                        self.send_to_queue(entity)
                    break
                except Exception as e:
                    LOG.exception('Driver Exception: {0}'.format(e))
                    time.sleep(fault_interval)
                    driver.callback_on_fault(e)
        return _entities_to_queue

    def stop(self, graceful=False):
        LOG.info("Vitrage datasources Snapshot Service - Stopping...")

        super(SnapshotsService, self).stop(graceful)

        LOG.info("Vitrage datasources Snapshot Service - Stopped!")


class ChangesService(DatasourceService):
    def __init__(self, conf,
                 registered_datasources,
                 changes_interval,
                 callback_function):
        super(ChangesService, self).__init__(conf,
                                             registered_datasources,
                                             callback_function)
        self.changes_interval = changes_interval

    def start(self):
        LOG.info("Vitrage Datasource Changes Service For: %s - Starting...",
                 self.registered_datasources[0].__class__.__name__)

        super(ChangesService, self).start()
        self.tg.add_timer(interval=self.changes_interval,
                          callback=self._get_changes,
                          initial_delay=self.changes_interval)

        LOG.info("Vitrage Datasource Changes Service For: %s - Started!",
                 self.registered_datasources[0].__class__.__name__)

    def stop(self, graceful=False):
        LOG.info("Vitrage Datasource Changes Service For: %s - Stopping...",
                 self.registered_datasources[0].__class__.__name__)

        super(ChangesService, self).stop(graceful)

        LOG.info("Vitrage Datasource Changes Service For: %s - Stopped!",
                 self.registered_datasources[0].__class__.__name__)

    def _get_changes(self):
        LOG.debug("start get changes")
        for datasource in self.registered_datasources:
            try:
                for entity in datasource.get_changes(DatasourceAction.UPDATE):
                    self.send_to_queue(entity)
            except Exception as e:
                LOG.exception("Get changes Failed - %s", e)
        LOG.debug("end get changes")
