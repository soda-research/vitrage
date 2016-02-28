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
from oslo_log import log as logging

from vitrage.common.exception import VitrageAlgorithmError
from vitrage.graph.filter import check_filter

LOG = logging.getLogger(__name__)

MAPPED_V_ID = 'mapped_v_id'
NEIGHBORS_MAPPED = 'neighbors_mapped'


def get_edges_to_mapped_vertices(graph, vertex):
    """Get all edges (to/from) vertex where neighbor has a MAPPED_V_ID

    :type graph: driver.Graph
    :type vertex: driver.Vertex
    :rtype: list of driver.Edge
    """
    sub_graph_edges_to_mapped_vertices = []
    for e in graph.get_edges(vertex.vertex_id):
        t_neighbor = graph.get_vertex(e.other_vertex(vertex.vertex_id))
        if not t_neighbor:
            raise VitrageAlgorithmError('Cant get vertex for edge' + str(e))
        if t_neighbor and t_neighbor.get(MAPPED_V_ID):
            sub_graph_edges_to_mapped_vertices.append(e)
    return sub_graph_edges_to_mapped_vertices


def graph_contains_sub_graph_edges(graph, sub_graph, sub_graph_edges):
    """Check if graph contains all the expected edges

    For each (sub-graph) expected edge, check if a corresponding edge exists
    in the graph with relevant properties check

    :type graph: driver.Graph
    :type sub_graph: driver.Graph
    :type sub_graph_edges: list of driver.Edge
    :rtype: bool
    """
    for e in sub_graph_edges:
        graph_v_id_source = sub_graph.get_vertex(e.source_id).get(MAPPED_V_ID)
        graph_v_id_target = sub_graph.get_vertex(e.target_id).get(MAPPED_V_ID)
        if not graph_v_id_source or not graph_v_id_target:
            raise VitrageAlgorithmError('Cant get vertex for edge' + str(e))
        found_graph_edge = graph.get_edge(graph_v_id_source,
                                          graph_v_id_target,
                                          e.label)
        if not found_graph_edge or not check_filter(found_graph_edge, e):
            return False
    return True


def create_initial_sub_graph(graph, known_matches, sub_graph):
    """Create initial mapping graph from sub graph and known matches

    copy the sub-graph to create the first candidate mapping graph.
    In which known vertices mappings are added to vertices MAPPED_V_ID
    """
    mapping = sub_graph.copy()
    for known_match in known_matches:
        sub_graph_vertex = sub_graph.get_vertex(known_match.sub_graph_v_id)
        graph_vertex = graph.get_vertex(known_match.graph_v_id)
        if check_filter(graph_vertex, sub_graph_vertex):
            mv = sub_graph.get_vertex(sub_graph_vertex.vertex_id)
            mv[MAPPED_V_ID] = known_match.graph_v_id
            mapping.update_vertex(mv)
            edges = get_edges_to_mapped_vertices(mapping, mv)
            if not graph_contains_sub_graph_edges(graph, mapping, edges):
                return None
        else:
            return None
    return mapping


def sub_graph_matching(_graph_, sub_graph, known_matches):
    """Find all occurrences of sub_graph in the graph

    In the following, a partial mapping is a copy of the sub-graph.
    As we go, vertices of curr_mapping graph will be updated with new
    fields used only for the traversal:

     - MAPPED_V_ID:
       The vertex_id of the corresponding vertex in the graph.
       If it is not empty, than this vertex is already mapped

     - NEIGHBORS_MAPPED:
       True or None. When set True it means all the
       neighbors of this vertex have already been mapped

    Implementation Details:
    ----------------------

    - Init Step:
      copy the sub-graph to create the first candidate mapping graph. In which
      known vertices mappings are added to vertices MAPPED_V_ID. So, we now
      have a sub-graph copy where some of the vertices already have a mapping

    Main loop steps:

    - Steps 1:
      Pop a partially mapped sub-graph from the queue.
      If all its vertices have a MAPPED_V_ID, add it to final mappings

    - Steps 2 & 3:
      Find one template vertex that is not mapped but has a mapped neighbor

    - Step 4: CHECK PROPERTIES
      In the graph find candidate vertices that are linked to that neighbor
      and match the template vertex properties

    - Step 5: CHECK STRUCTURE
      Filter candidate vertices according to edges
    """
    final_sub_graphs = []
    initial_sg = create_initial_sub_graph(_graph_, known_matches, sub_graph)
    if not initial_sg:
        LOG.warning('sub_graph_matching: Initial sub-graph creation failed')
        LOG.warning('sub_graph_matching: Known matches: %s',
                    str(known_matches))
        return final_sub_graphs
    _queue_ = [initial_sg]

    while _queue_:
        curr_sub_graph = _queue_.pop(0)

        # STEP 1: STOPPING CONDITION
        mapped_vertices = filter(
            lambda v: v.get(MAPPED_V_ID),
            curr_sub_graph.get_vertices())
        if len(mapped_vertices) == sub_graph.num_vertices():
            final_sub_graphs.append(curr_sub_graph)
            continue

        # STEP 2: CAN WE THROW THIS SUB-GRAPH?
        vertices_with_unmapped_neighbors = filter(
            lambda v: not v.get(NEIGHBORS_MAPPED),
            mapped_vertices)
        if not vertices_with_unmapped_neighbors:
            continue

        # STEP 3: FIND A SUB-GRAPH VERTEX TO MAP
        v_with_unmapped_neighbors = vertices_with_unmapped_neighbors.pop(0)
        unmapped_neighbors = filter(
            lambda v: not v.get(MAPPED_V_ID),
            curr_sub_graph.neighbors(v_with_unmapped_neighbors.vertex_id))
        if not unmapped_neighbors:
            # Mark vertex as NEIGHBORS_MAPPED=True
            v_with_unmapped_neighbors[NEIGHBORS_MAPPED] = True
            curr_sub_graph.update_vertex(v_with_unmapped_neighbors)
            _queue_.append(curr_sub_graph)
            continue
        sub_graph_vertex_to_map = unmapped_neighbors.pop(0)

        # STEP 4: PROPERTIES CHECK
        graph_candidate_vertices = _graph_.neighbors(
            v_id=v_with_unmapped_neighbors[MAPPED_V_ID],
            vertex_attr_filter=sub_graph_vertex_to_map)

        # STEP 5: STRUCTURE CHECK
        edges = get_edges_to_mapped_vertices(curr_sub_graph,
                                             sub_graph_vertex_to_map)
        for graph_vertex in graph_candidate_vertices:
            sub_graph_vertex_to_map[MAPPED_V_ID] = graph_vertex.vertex_id
            curr_sub_graph.update_vertex(sub_graph_vertex_to_map)
            if graph_contains_sub_graph_edges(_graph_, curr_sub_graph, edges):
                _queue_.append(curr_sub_graph.copy())

    # Last thing: Convert results to the expected format!
    result = []
    for mapping in final_sub_graphs:
        # TODO(ihefetz) If needed, Here we can easily extract the edge
        # matches from the mapping graph
        a = {v.vertex_id: v[MAPPED_V_ID] for v in mapping.get_vertices()}
        result.append(a)
    return result
