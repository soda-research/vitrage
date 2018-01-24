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

from oslo_log import log

from vitrage.common.constants import TemplateStatus as TStatus
from vitrage.common.constants import TemplateTypes as TType
from vitrage.common.exception import VitrageError
from vitrage.entity_graph import EVALUATOR_TOPIC
from vitrage.entity_graph.graph_clone import base
from vitrage.evaluator.actions.base import ActionMode
from vitrage.evaluator.scenario_evaluator import ScenarioEvaluator
from vitrage.evaluator.scenario_repository import ScenarioRepository
from vitrage.messaging import VitrageNotifier

LOG = log.getLogger(__name__)

TEMPLATE_ACTION = 'template_action'
ADD = 'add'
DELETE = 'delete'


class TemplateLoaderManager(base.GraphCloneManagerBase):

    def __init__(self, conf, entity_graph, db):
        super(TemplateLoaderManager, self).__init__(conf, entity_graph, 1)
        self._db = db

    def _run_worker(self, worker_index, workers_num):
        tasks_queue = multiprocessing.JoinableQueue()
        w = TemplateLoaderWorker(
            self._conf,
            tasks_queue,
            self._entity_graph)
        self._p_launcher.launch_service(w)
        return tasks_queue

    def handle_template_event(self, event):
        template_action = event.get(TEMPLATE_ACTION)

        if template_action == ADD:
            templates = self._db.templates.query(status=TStatus.LOADING)
            new_status = TStatus.ACTIVE
            action_mode = ActionMode.DO
        elif template_action == DELETE:
            templates = self._db.templates.query(status=TStatus.DELETING)
            new_status = TStatus.DELETED
            action_mode = ActionMode.UNDO
        else:
            raise VitrageError('Invalid template_action %s' % template_action)

        self._template_worker_task(
            [t.name for t in templates if t.template_type == TType.STANDARD],
            action_mode)

        for t in templates:
            self._db.templates.update(t.uuid, 'status', new_status)

    def _template_worker_task(self, template_names, action_mode):
        self._notify_and_wait((TEMPLATE_ACTION, template_names, action_mode))


class TemplateLoaderWorker(base.GraphCloneWorkerBase):
    def __init__(self,
                 conf,
                 task_queue,
                 e_graph):
        super(TemplateLoaderWorker, self).__init__(conf, task_queue, e_graph)
        self._evaluator = None

    def start(self):
        super(TemplateLoaderWorker, self).start()
        actions_callback = VitrageNotifier(
            conf=self._conf,
            publisher_id='vitrage_evaluator',
            topic=EVALUATOR_TOPIC).notify
        self._evaluator = ScenarioEvaluator(
            self._conf,
            self._entity_graph,
            None,
            actions_callback,
            enabled=False)

    def do_task(self, task):
        super(TemplateLoaderWorker, self).do_task(task)
        action = task[0]
        if action == TEMPLATE_ACTION:
            (action, template_names, action_mode) = task
            self._template_action(template_names, action_mode)

    def _template_action(self, template_names, action_mode):
        self._enable_evaluator_templates(template_names)
        self._evaluator.run_evaluator(action_mode)
        self._disable_evaluator()

    def _enable_evaluator_templates(self, template_names):
        scenario_repo = ScenarioRepository(self._conf)
        for s in scenario_repo._all_scenarios:
            s.enabled = False
            for template_name in template_names:
                if s.id.startswith(template_name):
                    s.enabled = True
        self._evaluator.scenario_repo = scenario_repo
        self._evaluator.scenario_repo.log_enabled_scenarios()
        self._evaluator.enabled = True

    def _disable_evaluator(self):
        self._entity_graph.notifier._subscriptions = []  # Quick n dirty
        self._evaluator.enabled = False
