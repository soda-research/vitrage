# Copyright 2017 - Nokia
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

from __future__ import print_function
from concurrent.futures import ThreadPoolExecutor
import cotyledon
from futurist import periodics

from oslo_log import log
import oslo_messaging as oslo_m

from vitrage.common.utils import spawn
from vitrage import messaging


LOG = log.getLogger(__name__)


class PersistorService(cotyledon.Service):
    def __init__(self, worker_id, conf, db_connection):
        super(PersistorService, self).__init__(worker_id)
        self.conf = conf
        self.db_connection = db_connection
        transport = messaging.get_transport(conf)
        target = \
            oslo_m.Target(topic=conf.persistency.persistor_topic)
        self.listener = messaging.get_notification_listener(
            transport, [target],
            [VitragePersistorEndpoint(self.db_connection)])
        self.scheduler = Scheduler(conf, db_connection)

    def run(self):
        LOG.info("Vitrage Persistor Service - Starting...")

        self.listener.start()
        self.scheduler.start_periodic_tasks()

        LOG.info("Vitrage Persistor Service - Started!")

    def terminate(self):
        LOG.info("Vitrage Persistor Service - Stopping...")

        self.listener.stop()
        self.listener.wait()

        LOG.info("Vitrage Persistor Service - Stopped!")


class VitragePersistorEndpoint(object):

    funcs = {}

    def __init__(self, db_connection):
        self.db_connection = db_connection

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        LOG.debug('Event_type: %s Payload %s', event_type, payload)
        if event_type and event_type in self.funcs.keys():
            self.funcs[event_type](self.db_connection, event_type, payload)


class Scheduler(object):

    def __init__(self, conf, db):
        self.conf = conf
        self.db = db
        self.periodic = None

    def start_periodic_tasks(self):
        self.periodic = periodics.PeriodicWorker.create(
            [], executor_factory=lambda: ThreadPoolExecutor(max_workers=10))

        self.add_expirer_timer()
        spawn(self.periodic.start)

    def add_expirer_timer(self):
        spacing = 60

        @periodics.periodic(spacing=spacing)
        def expirer_periodic():
            try:
                event_id = self.db.graph_snapshots.query_snapshot_event_id()
                if event_id:
                    LOG.debug('Expirer deleting event - id=%s', event_id)
                    self.db.events.delete(event_id)

            except Exception:
                LOG.exception('DB periodic cleanup run failed.')

        self.periodic.add(expirer_periodic)
        LOG.info("Database periodic cleanup starting (spacing=%ss)", spacing)
