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

import multiprocessing

from oslo_concurrency import processutils
from oslo_log import log

from vitrage.entity_graph import EVALUATOR_TOPIC
from vitrage.entity_graph.graph_clone import base
from vitrage.evaluator.scenario_evaluator import ScenarioEvaluator
from vitrage.evaluator.scenario_repository import ScenarioRepository
from vitrage.messaging import VitrageNotifier

LOG = log.getLogger(__name__)

START_EVALUATION = 'start_evaluation'
RELOAD_TEMPLATES = 'reload_templates'


class EvaluatorManager(base.GraphCloneManagerBase):

    def __init__(self, conf, entity_graph):
        workers_num = conf.evaluator.workers or processutils.get_worker_count()
        super(EvaluatorManager, self).__init__(conf, entity_graph, workers_num)

    def before_subscribe(self):
        self.start_evaluations()

    def _run_worker(self, worker_index, workers_num):
        """Create an EvaluatorWorker and it's task queue

        The new worker is initialized with a scenario repository
        that only contains a portion of the templates
        """

        tasks_queue = multiprocessing.JoinableQueue()
        w = EvaluatorWorker(
            self._conf,
            tasks_queue,
            self._entity_graph,
            worker_index,
            workers_num)
        self._p_launcher.launch_service(w)
        return tasks_queue

    def start_evaluations(self):
        self._notify_and_wait((START_EVALUATION,))

    def reload_evaluators_templates(self):
        self._notify_and_wait((RELOAD_TEMPLATES,))


class EvaluatorWorker(base.GraphCloneWorkerBase):
    def __init__(self,
                 conf,
                 task_queue,
                 e_graph,
                 worker_index,
                 workers_num):
        super(EvaluatorWorker, self).__init__(conf, task_queue, e_graph)
        self._worker_index = worker_index
        self._workers_num = workers_num
        self._evaluator = None

    def start(self):
        super(EvaluatorWorker, self).start()
        scenario_repo = ScenarioRepository(self._conf, self._worker_index,
                                           self._workers_num)
        actions_callback = VitrageNotifier(
            conf=self._conf,
            publisher_id='vitrage_evaluator',
            topic=EVALUATOR_TOPIC).notify
        self._evaluator = ScenarioEvaluator(
            self._conf,
            self._entity_graph,
            scenario_repo,
            actions_callback,
            enabled=False)
        self._evaluator.scenario_repo.log_enabled_scenarios()

    def do_task(self, task):
        super(EvaluatorWorker, self).do_task(task)
        action = task[0]
        if action == START_EVALUATION:
            self._evaluator.run_evaluator()
        elif action == RELOAD_TEMPLATES:
            self._reload_templates()

    def _reload_templates(self):
        scenario_repo = ScenarioRepository(self._conf, self._worker_index,
                                           self._workers_num)
        self._evaluator.scenario_repo = scenario_repo
        LOG.info("reloading evaluator scenarios")
        self._evaluator.scenario_repo.log_enabled_scenarios()
