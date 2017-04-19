# Copyright 2016 - ZTE, Nokia
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
import copy
import json
from oslo_log import log

from vitrage.api_handler.apis.base import EntityGraphApisBase
from vitrage.api_handler.apis.base import RESOURCES_ALL_QUERY
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import VertexProperties as VProps


LOG = log.getLogger(__name__)


class ResourceApis(EntityGraphApisBase):

    def __init__(self, entity_graph, conf):
        self.entity_graph = entity_graph
        self.conf = conf

    def get_resources(self, ctx, resource_type=None, all_tenants=False):
        LOG.debug('ResourceApis get_resources - resource_type: %s,'
                  'all_tenants: %s', str(resource_type), all_tenants)

        project_id = ctx.get(self.TENANT_PROPERTY, None)
        is_admin_project = ctx.get(self.IS_ADMIN_PROJECT_PROPERTY, False)

        if all_tenants:
            resource_query = RESOURCES_ALL_QUERY
        else:
            resource_query = self._get_query_with_project(
                EntityCategory.RESOURCE,
                project_id,
                is_admin_project)
        query = copy.deepcopy(resource_query)

        if resource_type:
            type_query = {'==': {VProps.TYPE: resource_type}}
            query['and'].append(type_query)

        resources = self.entity_graph.get_vertices(query_dict=query)
        return json.dumps({'resources': [resource.properties
                                         for resource in resources]})

    def show_resource(self, ctx, vitrage_id):
        LOG.debug('Show resource with vitrage_id: %s', str(vitrage_id))

        project_id = ctx.get(self.TENANT_PROPERTY, None)
        is_admin_project = ctx.get(self.IS_ADMIN_PROJECT_PROPERTY, False)

        resource = self.entity_graph.get_vertex(vitrage_id)
        if resource:
            project = resource.get(VProps.PROJECT_ID)
            if is_admin_project:
                return json.dumps(resource.properties)
            else:
                if project and project_id == project:
                    return json.dumps(resource.properties)
            LOG.warn('Have no authority to get resource with vitrage_id(%s)',
                     str(vitrage_id))
        else:
            LOG.warn('Can not find the resource with vitrage_id(%s)',
                     str(vitrage_id))
        return None
