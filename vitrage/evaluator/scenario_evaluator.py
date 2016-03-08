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

    def __init__(self, entity_graph, scenario_repo, event_queue):
        self._entity_graph = entity_graph
        self._graph_algs = create_algorithm(entity_graph)
        self._scenario_repo = scenario_repo
        self._action_executor = ActionExecutor(event_queue)
        self._entity_graph.subscribe(self.process_event)
        self.enabled = True

    def process_event(self, before, current, is_vertex):
        """Notification of a change in the entity graph.

        :param before: The graph element (vertex or edge) prior to the
        change that happened. None if the element was just created.
        :param current: The graph element (vertex or edge) after the
        change that happened. Deleted elements should arrive with the
        is_deleted property set to True
        """
        if not self.enabled:
            return

        # todo (erosensw): support for NOT conditions - reverse logic
        before_scenarios = self._get_element_scenarios(before, is_vertex)
        current_scenarios = self._get_element_scenarios(current, is_vertex)
        before_scenarios, current_scenarios = \
            self._remove_overlap_scenarios(before_scenarios, current_scenarios)

        actions = self._get_actions(before,
                                    before_scenarios,
                                    ActionMode.UNDO)
        actions.update(self._get_actions(current,
                                         current_scenarios,
                                         ActionMode.DO))

        for action in actions.values():
            # todo: named tuple?
            self._action_executor.execute(action[0], action[1])

    def _get_element_scenarios(self, element, is_vertex):
        if not element \
                or element.get(VProps.IS_DELETED) \
                or element.get(EProps.IS_DELETED):
            return []
        elif is_vertex:
            return self._scenario_repo.get_scenarios_by_vertex(element)
        else:  # is edge
            source = self._entity_graph.get_vertex(element.source_id)
            target = self._entity_graph.get_vertex(element.target_id)
            edge_desc = EdgeDescription(element, source, target)
            return self._scenario_repo.get_scenarios_by_edge(edge_desc)

    @staticmethod
    def _remove_overlap_scenarios(before, current):
        intersection = filter(lambda x: x in before, current)
        before = filter(lambda x: x not in intersection, before)
        current = filter(lambda x: x not in intersection, current)
        return before, current

    def _get_actions(self, element, anchored_scenarios, mode):
        actions = {}
        for anchored_scenario in anchored_scenarios:
            scenario_anchor = anchored_scenario[0]
            scenario = anchored_scenario[1]
            actions.update(self._process_scenario(element,
                                                  scenario,
                                                  scenario_anchor,
                                                  mode))
        return actions

    def _process_scenario(self, element, scenario, template_anchors, mode):
        actions = {}
        for action in scenario.actions:
            if not isinstance(template_anchors, list):
                template_anchors = [template_anchors]
            for template_anchor in template_anchors:
                matches = self._evaluate_full_condition(scenario.condition,
                                                        element,
                                                        template_anchor)
                if matches:
                    for match in matches:
                        spec, action_id = self._get_action_spec(action, match)
                        actions[action_id] = (spec, mode)
        return actions

    @staticmethod
    def _get_action_spec(action_spec, mappings):
        targets = action_spec.targets
        real_ids = {key: mappings[value] for key, value in targets.items()}
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

    def _evaluate_full_condition(self, condition, trigger, template_anchor):
        condition_matches = []
        for clause in condition:
            # OR condition means aggregation of matches, without duplicates
            simple_condition_matches = \
                self._evaluate_and_condition(clause, trigger, template_anchor)
            condition_matches += simple_condition_matches

        return condition_matches

    def _evaluate_and_condition(self, condition, trigger, template_anchor):

        condition_g = create_graph("scenario condition")
        for term in condition:
            if not term.positive:
                # todo(erosensw): add support for NOT clauses
                LOG.error('Unsupported template with NOT operator')
                return []

            if term.type == ENTITY:
                condition_g.add_vertex(term.variable)

            else:  # type = relationship
                condition_g.add_vertex(term.variable.source)
                condition_g.add_vertex(term.variable.target)
                condition_g.add_edge(term.variable.edge)

        if isinstance(trigger, Vertex):
            anchor_map = Mapping(template_anchor, trigger, True)
        else:
            anchor_map = Mapping(template_anchor.edge, trigger, False)
        return self._graph_algs.sub_graph_matching(condition_g, [anchor_map])
