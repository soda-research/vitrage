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
from osprofiler import profiler

from vitrage.evaluator.template_db import template_repository as template_repo


LOG = log.getLogger(__name__)


@profiler.trace_cls("template apis",
                    info={}, hide_args=False, trace_private=False)
class TemplateApis(object):

    FAILED_MSG = 'validation failed'
    OK_MSG = 'validation OK'

    def __init__(self, notifier=None, db=None):
        self.notifier = notifier
        self.db = db

    def validate_template(self, ctx, templates, template_type):
        LOG.debug("TemplateApis validate_template type: %s content: ",
                  str(template_type), str(templates))

        files_content = [t[1] for t in templates]
        paths = [t[0] for t in templates]
        results = template_repo.validate_templates(self.db, files_content,
                                                   template_type)
        results = [_to_result(r, p) for r, p in zip(results, paths)]
        return json.dumps({'results': results})

    def add_template(self, ctx, templates, template_type):
        """Signal the evaluator

         A new template has been added to the database with a status of
         LOADING that needs to be handled.
        """
        LOG.debug("TemplateApis add_template type: %s content: ",
                  str(template_type), str(templates))

        files_content = [t[1] for t in templates]
        results = template_repo.add_templates_to_db(self.db, files_content,
                                                    template_type)
        LOG.info("Add Template Running")
        self.notifier.notify("add template", {'template_action': 'add'})
        results = [_db_template_to_dict(r) for r in results]
        return results

    def delete_template(self, ctx):
        """Signal the evaluator

         A template status has been changed to DELETING.
        """
        LOG.info("Delete Template Running")
        self.notifier.notify("delete template", {'template_action': 'delete'})


def _to_result(result, template_path):
    if result.is_valid_config:
        return {
            'file path': template_path,
            'status': TemplateApis.OK_MSG,
            'description': 'Template validation',
            'message': str(result.comment),
            'status code': result.status_code
        }
    else:
        return {
            'file path': template_path,
            'status': TemplateApis.FAILED_MSG,
            'description': result.description,
            'message': str(result.comment),
            'status code': result.status_code
        }


def _db_template_to_dict(template):
    return {
        "uuid": template.uuid,
        "name": template.name,
        "status": template.status,
        "date": str(template.created_at),
        "status details": template.status_details,
        "type": template.template_type,
    }
