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

import json
from oslo_log import log

from vitrage.common.constants import EdgeLabel
from vitrage.common.constants import EdgeProperties as EProps
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources.nova.host import NOVA_HOST_DATASOURCE
from vitrage.datasources.nova.instance import NOVA_INSTANCE_DATASOURCE
from vitrage.datasources.nova.zone import NOVA_ZONE_DATASOURCE
from vitrage.datasources import OPENSTACK_CLUSTER
from vitrage.evaluator.template_fields import TemplateFields
from vitrage.evaluator.template_validation.status_messages import status_msgs
from vitrage.evaluator.template_validation.template_content_validator import \
    content_validation
from vitrage.evaluator.template_validation.template_syntax_validator import \
    syntax_validation
from vitrage.graph import create_algorithm
from vitrage.graph import Direction

LOG = log.getLogger(__name__)

# Used for Sunburst to show only specific resources
TREE_TOPOLOGY_QUERY = {
    'and': [
        {'==': {VProps.CATEGORY: EntityCategory.RESOURCE}},
        {'==': {VProps.IS_DELETED: False}},
        {'==': {VProps.IS_PLACEHOLDER: False}},
        {
            'or': [
                {'==': {VProps.TYPE: OPENSTACK_CLUSTER}},
                {'==': {VProps.TYPE: NOVA_INSTANCE_DATASOURCE}},
                {'==': {VProps.TYPE: NOVA_HOST_DATASOURCE}},
                {'==': {VProps.TYPE: NOVA_ZONE_DATASOURCE}}
            ]
        }
    ]
}

TOPOLOGY_AND_ALARMS_QUERY = {
    'and': [
        {'==': {VProps.IS_DELETED: False}},
        {'==': {VProps.IS_PLACEHOLDER: False}},
        {
            'or': [
                {'==': {VProps.CATEGORY: EntityCategory.ALARM}},
                {'==': {VProps.CATEGORY: EntityCategory.RESOURCE}}
            ]
        }
    ]
}

RCA_QUERY = {
    'and': [
        {'==': {VProps.CATEGORY: EntityCategory.ALARM}},
        {'==': {VProps.IS_DELETED: False}}
    ]
}

ALARMS_ALL_QUERY = {
    'and': [
        {'==': {VProps.CATEGORY: EntityCategory.ALARM}},
        {'==': {VProps.IS_DELETED: False}}
    ]
}


class EntityGraphApis(object):
    def __init__(self, entity_graph):
        self.entity_graph = entity_graph

    def get_alarms(self, ctx, arg):
        LOG.debug("EntityGraphApis get_alarms arg:%s", str(arg))
        vitrage_id = arg
        if not vitrage_id or vitrage_id == 'all':
            items_list = self.entity_graph.get_vertices(
                query_dict=ALARMS_ALL_QUERY)
        else:
            items_list = self.entity_graph.neighbors(
                vitrage_id,
                vertex_attr_filter={VProps.CATEGORY: EntityCategory.ALARM,
                                    VProps.IS_DELETED: False})

        # TODO(alexey) this should not be here, but in the transformer
        modified_alarms = self._add_resource_details_to_alarms(items_list)

        return json.dumps({'alarms': [v.properties for v in modified_alarms]})

    def get_topology(self, ctx, graph_type, depth, query, root):
        LOG.debug("EntityGraphApis get_topology root:%s", str(root))

        ga = create_algorithm(self.entity_graph)
        if graph_type == 'tree':
            if not query:
                LOG.error("Graph-type 'tree' requires a filter.")
                return {}
            found_graph = ga.graph_query_vertices(
                query_dict=query,
                root_id=root,
                depth=depth)
        elif graph_type == 'graph':
            final_query = query if query else TOPOLOGY_AND_ALARMS_QUERY
            if root:
                found_graph = ga.graph_query_vertices(
                    query_dict=final_query,
                    root_id=root,
                    depth=depth)
            else:
                found_graph = ga.create_graph_from_matching_vertices(
                    query_dict=final_query)
        return found_graph.json_output_graph()

    def get_rca(self, ctx, root):
        LOG.debug("EntityGraphApis get_rca root:%s", str(root))

        ga = create_algorithm(self.entity_graph)
        found_graph_in = ga.graph_query_vertices(
            query_dict=RCA_QUERY,
            root_id=root,
            direction=Direction.IN)
        found_graph_out = ga.graph_query_vertices(
            query_dict=RCA_QUERY,
            root_id=root,
            direction=Direction.OUT)
        unified_graph = found_graph_in
        unified_graph.union(found_graph_out)
        json_graph = unified_graph.json_output_graph(
            inspected_index=self._find_rca_index(unified_graph, root))
        return json_graph

    @staticmethod
    def _get_first(lst):
        if len(lst) == 1:
            return lst[0]
        else:
            return None

    def _add_resource_details_to_alarms(self, alarms):
        incorrect_alarms = []
        for alarm in alarms:
            try:
                resources = self.entity_graph.neighbors(
                    v_id=alarm.vertex_id,
                    edge_attr_filter={EProps.RELATIONSHIP_TYPE: EdgeLabel.ON},
                    direction=Direction.OUT)

                resource = self._get_first(resources)
                if resource:
                    alarm["resource_id"] = resource.get(VProps.ID, '')
                    alarm["resource_type"] = resource.get(VProps.TYPE, '')
                else:
                    alarm["resource_id"] = ''
                    alarm["resource_type"] = ''

            except ValueError as ve:
                incorrect_alarms.append(alarm)
                LOG.error('Alarm %s\nException %s', alarm, ve)

        return [item for item in alarms if item not in incorrect_alarms]

    @staticmethod
    def _find_rca_index(found_graph, root):
        for root_index, vertex in enumerate(found_graph._g):
            if vertex == root:
                return root_index
        return 0


class TemplateApis(object):

    FAILED_MSG = 'validation failed'
    OK_MSG = 'validation OK'

    def __init__(self, templates):
        self.templates = templates

    def get_templates(self, ctx):
        LOG.debug("TemplateApis get_templates")

        templates_details = []
        for uuid, template in self.templates.items():

            template_metadata = template.data[TemplateFields.METADATA]

            templates_details.append({
                'uuid': str(template.uuid),
                'name': template_metadata[TemplateFields.NAME],
                'status': self._get_template_status(template.result),
                'status details': template.result.comment,
                'date': template.date.strftime('%Y-%m-%dT%H:%M:%SZ')
            })
        return json.dumps({'templates_details': templates_details})

    def show_template(self, ctx, template_uuid):

        LOG.debug("Show template with uuid: $s", str(template_uuid))

        template = self.templates[template_uuid]

        if template:
            return json.dumps(template.data)
        else:
            return json.dumps({'ERROR': 'Incorrect uuid'})

    def validate_template(self, ctx, templates):
        LOG.debug("TemplateApis validate_template templates:"
                  "%s", str(templates))

        results = []
        for template in templates:

            template_def = template[1]
            path = template[0]

            syntax_result = syntax_validation(template_def)
            if not syntax_result.is_valid:
                self._add_result(path,
                                 self.FAILED_MSG,
                                 syntax_result.description,
                                 syntax_result.comment,
                                 syntax_result.status_code,
                                 results)
                continue

            content_result = content_validation(template_def)
            if not content_result.is_valid:
                self._add_result(path,
                                 self.FAILED_MSG,
                                 content_result.description,
                                 content_result.comment,
                                 content_result.status_code,
                                 results)
                continue

            self._add_result(path,
                             self.OK_MSG,
                             'Template validation',
                             status_msgs[0],
                             0,
                             results)

        return json.dumps({'results': results})

    @staticmethod
    def _add_result(template_path, status, description, message, status_code,
                    results):

        results.append({
            'file path': template_path,
            'status': status,
            'description': description,
            'message': str(message),
            'status code': status_code
        })

    @staticmethod
    def _get_template_status(result):

        if result.is_valid:
            return 'pass'
        else:
            return 'failed'
