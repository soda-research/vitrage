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

import os

from oslo_log import log
import yaml

LOG = log.getLogger(__name__)


def load_files(dir_path, suffix=None):
    loaded_files = os.listdir(dir_path)

    if suffix:
        loaded_files = [f for f in loaded_files if f.endswith(suffix)]

    return loaded_files


def load_yaml_files(dir_path, with_exception=False):
    files = load_files(dir_path, '.yaml')

    yaml_files = []
    for file in files:
        full_path = dir_path + '/' + file

        config = load_yaml_file(full_path, with_exception)
        if config:
            yaml_files.append(config)

    return yaml_files


def load_yaml_file(full_path, with_exception=False):
    with open(full_path, 'r') as stream:
        try:
            return yaml.load(stream, Loader=yaml.BaseLoader)
        except Exception as e:
            if with_exception:
                raise e
            else:
                LOG.error("Fails to parse file: %s. %s" % (full_path, e))
                return None
