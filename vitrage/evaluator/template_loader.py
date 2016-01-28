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
import yaml

from oslo_log import log

from vitrage.common import file_utils


LOG = log.getLogger(__name__)


def load_templates_files(conf):

    templates_dir_path = conf.evaluator.templates_dir
    templates_files = file_utils.load_files(templates_dir_path, '.yaml')

    templates_configs = []
    for template_file in templates_files:

        full_path = templates_dir_path + '/' + template_file
        with open(full_path, 'r') as stream:
            config = yaml.load(stream)
            templates_configs.append(config)

    return templates_configs
