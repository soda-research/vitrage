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

from collections import namedtuple

from oslo_log import log
from vitrage.datasources.listener_service import defaultdict

from vitrage.common.constants import EdgeProperties as EProps
from vitrage.common.constants import VertexProperties as VProps
from vitrage.entity_graph.mappings.datasource_info_mapper \
    import DatasourceInfoMapper
from vitrage.evaluator.actions.action_executor import ActionExecutor
from vitrage.evaluator.actions.base import ActionMode
from vitrage.evaluator.actions.base import ActionType
import vitrage.evaluator.actions.priority_tools as pt
from vitrage.evaluator.template_data import ActionSpecs
from vitrage.evaluator.template_data import EdgeDescription
from vitrage.graph.algo_driver.algorithm import Mapping
from vitrage.graph.algo_driver.sub_graph_matching import \
    NEG_CONDITION
from vitrage.graph.driver import Vertex

LOG = log.getLogger(__name__)

# Entry containing action info.
# specs - ActionSpecs
# mode - DO or UNDO (the action)
# scenario_id - the scenario id in scenario_repository
# Trigger_id  - a unique identifier per match in graph (i.e., the subgraph
# that matched the action in the spec) for the specific action.
ActionInfo = \
    namedtuple('ActionInfo', ['specs', 'mode', 'scenario_id', 'trigger_id'])


class ScenarioEvaluator(object):

    def __init__(self,
                 conf,
                 entity_graph,
                 scenario_repo,
                 event_queue,
                 enabled=False):
        self.conf = conf
        self._scenario_repo = scenario_repo
        self._entity_graph = entity_graph
        self._action_executor = ActionExecutor(event_queue)
        self._entity_graph.subscribe(self.process_event)
        self._action_tracker = ActionTracker(DatasourceInfoMapper(self.conf))
        self.enabled = enabled
        self.connected_component_cache = defaultdict(dict)

    @property
    def scenario_repo(self):
        return self._scenario_repo

    @scenario_repo.setter
    def scenario_repo(self, scenario_repo):
        self._scenario_repo = scenario_repo

    def process_event(self, before, current, is_vertex, *args, **kwargs):
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
        actions.extend(self._process_and_get_actions(current,
                                                     current_scenarios,
                                                     ActionMode.DO))

        if actions:
            LOG.debug("Actions to perform: %s", actions)
            filtered_actions = \
                self._analyze_and_filter_actions(actions)
            LOG.debug("Actions filtered: %s", filtered_actions)
            for action in filtered_actions:
                self._action_executor.execute(action.specs, action.mode)

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
        intersection = list(filter(lambda x: x in before, current))
        before = list(filter(lambda x: x not in intersection, before))
        current = list(filter(lambda x: x not in intersection, current))
        return before, current

    def _process_and_get_actions(self, element, triggered_scenarios, mode):
        actions = []
        for triggered_scenario in triggered_scenarios:
            LOG.debug("Processing: %s", str(triggered_scenario))
            scenario_element = triggered_scenario[0]
            scenario = triggered_scenario[1]
            actions.extend(self._process_scenario(element,
                                                  scenario,
                                                  scenario_element,
                                                  mode))
        return actions

    def _process_scenario(self, element, scenario, scenario_elements, mode):
        if not isinstance(scenario_elements, list):
            scenario_elements = [scenario_elements]
        actions = []
        for action in scenario.actions:
            for scenario_element in scenario_elements:
                matches = self._evaluate_subgraphs(scenario.subgraphs,
                                                   element,
                                                   scenario_element,
                                                   action.targets['target'])

                actions.extend(self._get_actions_from_matches(matches,
                                                              mode,
                                                              action,
                                                              scenario))

        return actions

    def _evaluate_subgraphs(self,
                            subgraphs,
                            element,
                            scenario_element,
                            action_target):
        if isinstance(element, Vertex):
            return self._find_vertex_subgraph_matching(subgraphs,
                                                       action_target,
                                                       element,
                                                       scenario_element)
        else:
            return self._find_edge_subgraph_matching(subgraphs,
                                                     action_target,
                                                     element,
                                                     scenario_element)

    def _get_actions_from_matches(self,
                                  combined_matches,
                                  mode,
                                  action_spec,
                                  scenario):
        actions = []
        for is_switch_mode, matches in combined_matches:
            new_mode = mode
            if is_switch_mode:
                new_mode = ActionMode.UNDO \
                    if mode == ActionMode.DO else ActionMode.DO

            for match in matches:
                spec = self._get_action_spec(action_spec, match)
                items_ids = [match[1].vertex_id for match in match.items()]
                match_hash = hash(tuple(sorted(items_ids)))
                actions.append(ActionInfo(spec, new_mode,
                                          scenario.id, match_hash))

        return actions

    @staticmethod
    def _get_action_spec(action_spec, match):
        targets = action_spec.targets
        real_items = {
            target: match[target_id] for target, target_id in targets.items()
        }
        return ActionSpecs(action_spec.type,
                           real_items,
                           action_spec.properties)

    @staticmethod
    def _generate_action_id(action_spec):
        targets = [(k, v.vertex_id) for k, v in action_spec.targets.items()]
        return hash(
            (action_spec.type,
             tuple(sorted(targets)),
             tuple(sorted(action_spec.properties.items())))
        )

    def _analyze_and_filter_actions(self, actions):

        actions_to_perform = {}
        for action in actions:
            key = self._action_tracker.get_key(action.specs)
            prev_dominant = self._action_tracker.get_dominant_action(key)
            if action.mode == ActionMode.DO:
                self._action_tracker.insert_action(key, action)
            else:
                self._action_tracker.remove_action(key, action)
            new_dominant = self._action_tracker.get_dominant_action(key)

            # todo: (erosensw) improvement - first analyze DOs, then UNDOs
            if not new_dominant:  # removed last entry for key
                undo_action = ActionInfo(prev_dominant.specs,
                                         ActionMode.UNDO,
                                         prev_dominant.scenario_id,
                                         prev_dominant.trigger_id)
                actions_to_perform[key] = undo_action
            elif new_dominant != prev_dominant:
                actions_to_perform[key] = new_dominant

        # filter the same action
        final_actions = {ScenarioEvaluator._generate_action_id(action.specs):
                         action for action in actions_to_perform.values()}

        return final_actions.values()

    def _find_vertex_subgraph_matching(self,
                                       subgraphs,
                                       action_target,
                                       vertex,
                                       scenario_vertex):
        """calculates subgraph matching for vertex

        iterates over all the subgraphs, and checks if the triggered vertex is
        in the same connected component as the action then run subgraph
        matching on the vertex and return its result, otherwise return an
        empty list of matches.
        """

        matches = []
        for subgraph in subgraphs:
            connected_component = self.get_connected_component(subgraph,
                                                               action_target)

            is_switch_mode = \
                connected_component.get_vertex(scenario_vertex.vertex_id)

            if is_switch_mode:
                initial_map = Mapping(scenario_vertex, vertex, True)
                mat = self._entity_graph.algo.sub_graph_matching(subgraph,
                                                                 initial_map)
                matches.append((False, mat))
            else:
                matches.append((True, []))
        return matches

    def _find_edge_subgraph_matching(self,
                                     subgraphs,
                                     action_target,
                                     edge,
                                     scenario_edge):
        """calculates subgraph matching for edge

        iterates over all the subgraphs, and checks if the triggered edge is a
        negative edge then mark it as deleted=false and negative=false so that
        subgraph matching on that edge will work correctly. after running
        subgraph matching, we need to remove the negative vertices that were
        added due to the change above.
        """

        matches = []
        for subgraph in subgraphs:
            subgraph_edge = subgraph.get_edge(scenario_edge.source.vertex_id,
                                              scenario_edge.target.vertex_id,
                                              scenario_edge.edge.label)
            if not subgraph_edge:
                continue

            is_switch_mode = subgraph_edge.get(NEG_CONDITION, False)

            connected_component = self.get_connected_component(subgraph,
                                                               action_target)
            # change the is_deleted and negative_condition props to false when
            # is_switch_mode=true so that when we have an event on a
            # negative_condition=true edge it will find the correct subgraph
            self._switch_edge_negative_props(is_switch_mode, scenario_edge,
                                             subgraph, False)

            initial_map = Mapping(scenario_edge.edge, edge, False)
            curr_matches = \
                self._entity_graph.algo.sub_graph_matching(subgraph,
                                                           initial_map)

            # switch back to the original values
            self._switch_edge_negative_props(is_switch_mode, scenario_edge,
                                             subgraph, True)

            self._remove_negative_vertices_from_matches(curr_matches,
                                                        connected_component)

            matches.append((is_switch_mode, curr_matches))
        return matches

    def get_connected_component(self, subgraph, target):
        connected_component = self.connected_component_cache.get(
            id(subgraph), {}).get(id(target))
        if not connected_component:
            connected_component = subgraph.algo.graph_query_vertices(
                root_id=target,
                edge_query_dict={'!=': {NEG_CONDITION: True}})
            self.connected_component_cache[id(subgraph)][id(target)] = \
                connected_component
        return connected_component

    @staticmethod
    def _switch_edge_negative_props(is_switch_mode,
                                    scenario_edge,
                                    subgraph,
                                    status):
        if is_switch_mode:
            scenario_edge.edge[NEG_CONDITION] = status
            scenario_edge.edge[EProps.IS_DELETED] = status
            subgraph.update_edge(scenario_edge.edge)

    @staticmethod
    def _remove_negative_vertices_from_matches(matches, connected_component):
        for match in matches:
            ver_ids = [v.vertex_id for v in connected_component.get_vertices()]
            ver_to_remove = [id for id in match.keys() if id not in ver_ids]
            for v_id in ver_to_remove:
                del match[v_id]


class ActionTracker(object):
    """Keeps track of all active actions and relative dominance/priority.

    Actions are organized according to resource-id
    and action details.
    Examples:
    - all set_state actions on a given resource share the same entry,
    regardless of state
    - all raise_alarm of type alarm_name on a given resource share the same
     entry, regardless of severity
    """

    def __init__(self, datasource_info_mapper):
        self._tracker = {}
        alarms_score = \
            datasource_info_mapper.get_datasource_priorities('vitrage')
        all_scores = datasource_info_mapper.get_datasource_priorities()
        self._action_tools = {
            ActionType.SET_STATE: pt.SetStateTools(all_scores),
            ActionType.RAISE_ALARM: pt.RaiseAlarmTools(alarms_score),
            ActionType.ADD_CAUSAL_RELATIONSHIP: pt.BaselineTools,
            ActionType.MARK_DOWN: pt.BaselineTools
        }

    def get_key(self, action_specs):
        return self._action_tools[action_specs.type].get_key(action_specs)

    def insert_action(self, key, action):
        actions = self._tracker.get(key, [])
        actions.append(action)
        scorer = self._action_tools[action.specs.type].get_score
        self._tracker[key] = sorted(actions, key=scorer, reverse=True)

    def remove_action(self, key, action):
        # actions are unique in their trigger and scenario_ids
        def _is_equivalent(action_entry):
            return action_entry.trigger_id == action.trigger_id and \
                action_entry.scenario_id == action.scenario_id

        to_remove = [entry for entry in self._tracker.get(key, [])
                     if _is_equivalent(entry)]

        if len(to_remove) == 0:
            LOG.warning("Could not find action entry to remove "
                        "from tracker: {}".format(action))

        for entry in to_remove:
            self._tracker[key].remove(entry)

    def get_dominant_action(self, key):
        return self._tracker[key][0] if self._tracker.get(key, None) else None
