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

from vitrage.common.constants import EdgeProperties as EProps
from vitrage.common.constants import VertexProperties as VProps
from vitrage.evaluator.actions.action_executor import ActionExecutor
from vitrage.evaluator.actions.base import ActionMode
from vitrage.evaluator.template import ActionSpecs
from vitrage.evaluator.template import EdgeDescription
from vitrage.evaluator.template import ENTITY
from vitrage.graph.algo_driver.algorithm import Mapping
from vitrage.graph import create_algorithm
from vitrage.graph import create_graph
from vitrage.graph.driver import Vertex


LOG = log.getLogger(__name__)


class ScenarioEvaluator(object):

    def __init__(self,
                 conf,
                 entity_graph,
                 scenario_repo,
                 event_queue,
                 enabled=False):
        self.conf = conf
        self._entity_graph = entity_graph
        self._graph_algs = create_algorithm(entity_graph)
        self._scenario_repo = scenario_repo
        self._action_executor = ActionExecutor(event_queue)
        self._entity_graph.subscribe(self.process_event)
        self.enabled = enabled

    def process_event(self, before, current, is_vertex):
        """Notification of a change in the entity graph.

        :param is_vertex:
        :param before: The graph element (vertex or edge) prior to the
        change that happened. None if the element was just created.
        :param current: The graph element (vertex or edge) after the
        change that happened. Deleted elements should arrive with the
        is_deleted property set to True
        """

        if not self.enabled:
            LOG.debug("Process event disabled")
            return

        LOG.debug('Process event - starting')
        LOG.debug("Element before event: %s, Current element: %s",
                  str(before),
                  str(current))

        # todo (erosensw): support for NOT conditions - reverse logic
        before_scenarios = self._get_element_scenarios(before, is_vertex)
        current_scenarios = self._get_element_scenarios(current, is_vertex)
        before_scenarios, current_scenarios = \
            self._remove_overlap_scenarios(before_scenarios, current_scenarios)

        if len(before_scenarios) + len(current_scenarios):
            LOG.debug("Number of relevant scenarios found: undo = %s, do = %s",
                      str(len(before_scenarios)),
                      str(len(current_scenarios)))

        actions = self._process_and_get_actions(before,
                                                before_scenarios,
                                                ActionMode.UNDO)
        actions.update(self._process_and_get_actions(current,
                                                     current_scenarios,
                                                     ActionMode.DO))

        if actions:
            LOG.debug("Actions to perform: %s", actions.values())
        for action in actions.values():
            action_spec = action[0]
            action_mode = action[1]
            self._action_executor.execute(action_spec, action_mode)

        LOG.debug('Process event - completed')

    def _get_element_scenarios(self, element, is_vertex):
        if not element \
                or element.get(VProps.IS_DELETED) \
                or element.get(EProps.IS_DELETED):
            return []
        elif is_vertex:
            return self._scenario_repo.get_scenarios_by_vertex(element)
        else:  # is edge
            edge_desc = self._get_edge_description(element)
            return self._scenario_repo.get_scenarios_by_edge(edge_desc)

    def _get_edge_description(self, element):
        source = self._entity_graph.get_vertex(element.source_id)
        target = self._entity_graph.get_vertex(element.target_id)
        edge_desc = EdgeDescription(element, source, target)
        return edge_desc

    @staticmethod
    def _remove_overlap_scenarios(before, current):
        intersection = filter(lambda x: x in before, current)
        before = filter(lambda x: x not in intersection, before)
        current = filter(lambda x: x not in intersection, current)
        return before, current

    def _process_and_get_actions(self, element, triggered_scenarios, mode):
        actions = {}
        for triggered_scenario in triggered_scenarios:
            LOG.debug("Processing: %s", str(triggered_scenario))
            scenario_element = triggered_scenario[0]
            scenario = triggered_scenario[1]
            actions.update(self._process_scenario(element,
                                                  scenario,
                                                  scenario_element,
                                                  mode))
        return actions

    def _process_scenario(self, element, scenario, scenario_elements, mode):
        if not isinstance(scenario_elements, list):
            scenario_elements = [scenario_elements]
        actions = {}
        for action in scenario.actions:
            for scenario_element in scenario_elements:
                matches = self._evaluate_full_condition(scenario.condition,
                                                        element,
                                                        scenario_element)
                if matches:
                    for match in matches:
                        spec, action_id = self._get_action_spec(action, match)
                        actions[action_id] = (spec, mode)
        return actions

    @staticmethod
    def _get_action_spec(action_spec, match):
        targets = action_spec.targets
        real_ids = {
            target: match[target_id] for target, target_id in targets.items()
        }
        revised_spec = ActionSpecs(action_spec.type,
                                   real_ids,
                                   action_spec.properties)
        action_id = ScenarioEvaluator._generate_action_id(revised_spec)
        return revised_spec, action_id

    @staticmethod
    def _generate_action_id(action_spec):
        return hash(
            (action_spec.type,
             tuple(sorted(action_spec.targets.items())),
             tuple(sorted(action_spec.properties.items())))
        )

    def _evaluate_full_condition(self, condition, element, scenario_element):
        condition_matches = []
        for clause in condition:
            # OR condition means aggregation of matches, without duplicates
            and_condition_matches = \
                self._evaluate_and_condition(clause, element, scenario_element)
            condition_matches += and_condition_matches

        return condition_matches

    def _evaluate_and_condition(self, condition, element, scenario_element):

        condition_g = create_graph("scenario condition")
        for term in condition:
            if not term.positive:
                # todo(erosensw): add support for NOT clauses
                LOG.error('Unsupported template with NOT operator')
                return []

            if term.type == ENTITY:
                term.variable[VProps.IS_DELETED] = False
                condition_g.add_vertex(term.variable)

            else:  # type = relationship
                edge_desc = term.variable
                self._set_relationship_not_deleted(edge_desc)
                self._add_relationship(condition_g, edge_desc)

        if isinstance(element, Vertex):
            initial_map = Mapping(scenario_element, element, True)
        else:
            initial_map = Mapping(scenario_element.edge, element, False)
        return self._graph_algs.sub_graph_matching(condition_g, [initial_map])

    @staticmethod
    def _set_relationship_not_deleted(edge_description):
        edge_description.source[VProps.IS_DELETED] = False
        edge_description.target[VProps.IS_DELETED] = False
        edge_description.edge[EProps.IS_DELETED] = False

    @staticmethod
    def _add_relationship(condition_graph, edge_description):
        condition_graph.add_vertex(edge_description.source)
        condition_graph.add_vertex(edge_description.target)
        condition_graph.add_edge(edge_description.edge)
