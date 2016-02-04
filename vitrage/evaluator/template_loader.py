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

from vitrage.common import file_utils

LOG = log.getLogger(__name__)


def load_templates_files(conf):

    templates_dir_path = conf.evaluator.templates_dir
    template_files = file_utils.load_yaml_files(templates_dir_path)

    for template_file in template_files:
        pass
