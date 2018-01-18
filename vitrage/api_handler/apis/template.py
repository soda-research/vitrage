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

from vitrage.evaluator.template_validation.content.template_content_validator \
    import content_validation
from vitrage.evaluator.template_validation.status_messages import status_msgs
from vitrage.evaluator.template_validation.template_syntax_validator import \
    syntax_validation


LOG = log.getLogger(__name__)


@profiler.trace_cls("template apis",
                    info={}, hide_args=False, trace_private=False)
class TemplateApis(object):

    FAILED_MSG = 'validation failed'
    OK_MSG = 'validation OK'

    def __init__(self, notifier=None):
        self.notifier = notifier

    def validate_template(self, ctx, templates):
        LOG.debug("TemplateApis validate_template templates:"
                  "%s", str(templates))

        results = []
        for template in templates:

            template_definition = template[1]
            path = template[0]

            syntax_result = syntax_validation(template_definition)
            if not syntax_result.is_valid_config:
                self._add_result(path,
                                 self.FAILED_MSG,
                                 syntax_result.description,
                                 syntax_result.comment,
                                 syntax_result.status_code,
                                 results)
                continue

            content_result = content_validation(
                template_definition,
                self.def_templates)
            if not content_result.is_valid_config:
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

    def add_template(self, ctx):
        """Signal the evaluator

         A new template has been added to the database with a status of
         LOADING that needs to be handled.
        """
        LOG.info("Add Template Running")
        self.notifier.notify("add template", {'template_action': 'add'})

    def delete_template(self, ctx):
        """Signal the evaluator

         A template status has been changed to DELETING.
        """
        LOG.info("Delete Template Running")
        self.notifier.notify("delete template", {'template_action': 'delete'})

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

        if result.is_valid_config:
            return 'pass'
        else:
            return 'failed'
