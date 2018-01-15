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
import abc
import time

from oslo_log import log
from oslo_service import service as os_service

LOG = log.getLogger(__name__)


GRAPH_UPDATE = 'graph_update'
POISON_PILL = None


class GraphCloneManagerBase(object):

    def __init__(self, conf, entity_graph, worker_num):
        self._conf = conf
        self._entity_graph = entity_graph
        self._workers_num = worker_num
        self._worker_queues = list()
        self._p_launcher = os_service.ProcessLauncher(conf)

    def start(self):
        LOG.info('%s start %s processes', self.__class__.__name__,
                 self._workers_num)
        for i in range(self._workers_num):
            worker_queue = self._run_worker(i, self._workers_num)
            self._worker_queues.append(worker_queue)
        self.before_subscribe()
        self._entity_graph.subscribe(self.notify_graph_update)

    @abc.abstractmethod
    def _run_worker(self, worker_index, workers_num):
        raise NotImplementedError

    @abc.abstractmethod
    def before_subscribe(self):
        pass

    def notify_graph_update(self, before, current, is_vertex, *args, **kwargs):
        """Notify all workers

        This method is subscribed to entity graph changes.
        Per each change in the main entity graph, this method will notify
         each of the evaluators, causing them to update their own graph.
        """
        self._notify_and_wait((GRAPH_UPDATE, before, current, is_vertex))

    def _notify_and_wait(self, payload):
        for q in self._worker_queues:
            q.put(payload)
        time.sleep(0)  # context switch before join
        for q in self._worker_queues:
            q.join()

    def stop_all_workers(self):
        self._notify_and_wait(POISON_PILL)
        for q in self._worker_queues:
            q.close()
        self._worker_queues = list()


class GraphCloneWorkerBase(os_service.Service):
    def __init__(self,
                 conf,
                 task_queue,
                 entity_graph):
        super(GraphCloneWorkerBase, self).__init__()
        self._conf = conf
        self._task_queue = task_queue
        self._entity_graph = entity_graph

    def start(self):
        super(GraphCloneWorkerBase, self).start()
        self._entity_graph.notifier._subscriptions = []  # Quick n dirty
        self.tg.add_thread(self._read_queue)
        LOG.info("%s - Started!", self.__class__.__name__)

    def _read_queue(self):
        while True:
            next_task = self._task_queue.get()
            if next_task is POISON_PILL:
                self._task_queue.task_done()
                break
            try:
                self.do_task(next_task)
            except Exception as e:
                LOG.exception("Graph may not be in sync: exception %s", e)
            self._task_queue.task_done()
            # Evaluator queue may have been updated, thus the sleep:
            time.sleep(0)

    def do_task(self, task):
        action = task[0]
        if action == GRAPH_UPDATE:
            (action, before, current, is_vertex) = task
            self._graph_update(before, current, is_vertex)

    def _graph_update(self, before, current, is_vertex):
        if current:
            if is_vertex:
                self._entity_graph.add_vertex(current)
            else:
                self._entity_graph.add_edge(current)
        else:
            if is_vertex:
                self._entity_graph.delete_vertex(before)
            else:
                self._entity_graph.delete_edge(before)

    def stop(self, graceful=False):
        super(GraphCloneWorkerBase, self).stop(graceful)
        LOG.info("%s - Stopped!", self.__class__.__name__)
