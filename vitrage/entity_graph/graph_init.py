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
import threading
import time

from oslo_log import log
import oslo_messaging

from vitrage.common.constants import VertexProperties as VProps
from vitrage.common.utils import spawn
from vitrage.datasources.transformer_base import TransformerBase
from vitrage.entity_graph import driver_exec
from vitrage.entity_graph import EVALUATOR_TOPIC
from vitrage.entity_graph.graph_persistency import GraphPersistency
from vitrage.entity_graph.processor.notifier import GraphNotifier
from vitrage.entity_graph.processor.notifier import PersistNotifier
from vitrage.entity_graph.processor.processor import Processor
from vitrage.entity_graph.scheduler import Scheduler
from vitrage.entity_graph.workers import GraphWorkersManager
from vitrage.graph.driver.networkx_graph import NXGraph
from vitrage import messaging


LOG = log.getLogger(__name__)


class VitrageGraphInit(object):
    def __init__(self, conf, graph, db_connection):
        self.conf = conf
        self.graph = graph
        self.db = db_connection
        self.workers = GraphWorkersManager(conf, graph, db_connection)
        self.events_coordination = EventsCoordination(conf, self.process_event)
        self.persist = GraphPersistency(conf, db_connection, graph)
        self.driver_exec = driver_exec.DriverExec(
            self.conf,
            self.events_coordination.handle_multiple_low_priority,
            self.persist)
        self.scheduler = Scheduler(conf, graph, self.driver_exec, self.persist)
        self.processor = Processor(conf, graph)

    def run(self):
        LOG.info('Init Started')
        graph_snapshot = self.persist.query_recent_snapshot()
        if graph_snapshot:
            self._restart_from_stored_graph(graph_snapshot)
        else:
            self._start_from_scratch()
        self.workers.run()

    def _restart_from_stored_graph(self, graph_snapshot):
        LOG.info('Initializing graph from database snapshot (%sKb)',
                 len(graph_snapshot.graph_snapshot) / 1024)
        NXGraph.read_gpickle(graph_snapshot.graph_snapshot, self.graph)
        self.persist.replay_events(self.graph, graph_snapshot.event_id)
        self._recreate_transformers_id_cache()
        LOG.info("%s vertices loaded", self.graph.num_vertices())
        self.subscribe_presist_notifier()
        spawn(self._start_all_workers, is_snapshot=True)

    def _start_from_scratch(self):
        LOG.info('Starting for the first time')
        LOG.info('Clearing database active_actions')
        self.db.active_actions.delete()
        LOG.info('Disabling previously active alarms')
        self.db.history_facade.disable_alarms_in_history()
        self.subscribe_presist_notifier()
        self.driver_exec.snapshot_get_all()
        LOG.info("%s vertices loaded", self.graph.num_vertices())
        spawn(self._start_all_workers, is_snapshot=False)

    def _start_all_workers(self, is_snapshot):
        if is_snapshot:
            self.workers.submit_enable_evaluations()
        else:
            self.workers.submit_start_evaluations()
        self._add_graph_subscriptions()
        self.scheduler.start_periodic_tasks()
        LOG.info('Init Finished')
        self.events_coordination.start()

    def process_event(self, event):
        if event.get('template_action'):
            self.workers.submit_template_event(event)
            self.workers.submit_evaluators_reload_templates()
        else:
            self.processor.process_event(event)

    def _recreate_transformers_id_cache(self):
        for v in self.graph.get_vertices():
            if not v.get(VProps.VITRAGE_CACHED_ID):
                LOG.warning("Missing vitrage_cached_id in the vertex. "
                            "Vertex is not added to the ID cache %s", str(v))
            else:
                TransformerBase.key_to_uuid_cache[v[VProps.VITRAGE_CACHED_ID]]\
                    = v.vertex_id

    def _add_graph_subscriptions(self):
        self.graph.subscribe(self.workers.submit_graph_update)
        vitrage_notifier = GraphNotifier(self.conf)
        if vitrage_notifier.enabled:
            self.graph.subscribe(vitrage_notifier.notify_when_applicable)
            LOG.info('Subscribed vitrage notifier to graph changes')
        self.graph.subscribe(self.persist.persist_event,
                             finalization=True)

    def subscribe_presist_notifier(self):
        self.graph.subscribe(PersistNotifier(self.conf).notify_when_applicable)

PRIORITY_DELAY = 0.05


class EventsCoordination(object):
    def __init__(self, conf, do_work_func):
        self._conf = conf
        self._lock = threading.Lock()
        self._high_event_finish_time = 0

        def do_work(event):
            try:
                return do_work_func(event)
            except Exception:
                LOG.exception('Got Exception for event %s', str(event))

        self._do_work_func = do_work

        self._low_pri_listener = None
        self._high_pri_listener = None

    def start(self):
        self._low_pri_listener = driver_exec.DriversNotificationEndpoint(
            self._conf,
            self.handle_multiple_low_priority).init().get_listener()
        self._high_pri_listener = self._init_listener(
            EVALUATOR_TOPIC,
            self._do_high_priority_work)
        LOG.info('Listening on %s', self._high_pri_listener.targets[0].topic)
        LOG.info('Listening on %s', self._low_pri_listener.targets[0].topic)
        self._high_pri_listener.start()
        self._low_pri_listener.start()

    def stop(self):
        self._low_pri_listener.stop()
        self._high_pri_listener.stop()

    def wait(self):
        self._low_pri_listener.wait()
        self._high_pri_listener.wait()

    def _do_high_priority_work(self, event):
        self._lock.acquire()
        self._do_work_func(event)
        self._high_event_finish_time = time.time()
        self._lock.release()

    def _do_low_priority_work(self, event):
        while True:
            self._lock.acquire()
            if (time.time() - self._high_event_finish_time) < PRIORITY_DELAY:
                self._lock.release()
                time.sleep(PRIORITY_DELAY)
            else:
                break
        self._do_work_func(event)
        self._lock.release()

    def handle_multiple_low_priority(self, events):
        index = 0
        for index, e in enumerate(events):
            self._do_low_priority_work(e)
        return index

    def _init_listener(self, topic, callback):
        if not topic:
            return
        return messaging.get_notification_listener(
            transport=messaging.get_transport(self._conf),
            targets=[oslo_messaging.Target(topic=topic)],
            endpoints=[PushNotificationsEndpoint(callback)])


class PushNotificationsEndpoint(object):
    def __init__(self, process_event_callback):
        self.process_event_callback = process_event_callback

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        try:
            self.process_event_callback(payload)
        except Exception:
            LOG.exception('Failed to process event callback.')
