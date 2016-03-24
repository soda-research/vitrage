# Copyright 2015 - Alcatel-Lucent
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

import itertools
import os
from oslo_utils import importutils

import vitrage.api
import vitrage.clients
import vitrage.entity_graph.consistency
import vitrage.evaluator
import vitrage.keystone_client
import vitrage.rpc
import vitrage.synchronizer
import vitrage.synchronizer.plugins

PLUGINS_MODULE_PATH = 'vitrage.synchronizer.plugins.'
PLUGINS_FS_PATH = os.path.join('vitrage', 'synchronizer', 'plugins')
SYNCHRONIZER_FILE = 'synchronizer.py'
TRANSFORMER_FILE = 'transformer.py'


def list_opts():
    return [
        ('api', vitrage.api.OPTS),
        ('synchronizer', vitrage.synchronizer.OPTS),
        ('evaluator', vitrage.evaluator.OPTS),
        ('synchronizer_plugins', vitrage.synchronizer.plugins.OPTS),
        ('consistency', vitrage.entity_graph.consistency.OPTS),
        ('entity_graph', vitrage.entity_graph.OPTS),
        ('service_credentials', vitrage.keystone_client.OPTS),
        ('DEFAULT',
         itertools.chain(
             vitrage.clients.OPTS,
             vitrage.rpc.OPTS))
    ]


def plugins_opts():
    top = os.getcwd()
    plugin_names = _normalize_path_to_plugin_name(
        _filter_folders_containing_transformer(
            _get_folders_containing_synchronizer(top)), top)

    return [(plugin_name, plugin_module.OPTS) for plugin_name in plugin_names
            for plugin_module in
            [importutils.import_module(PLUGINS_MODULE_PATH + plugin_name)]
            if 'OPTS' in plugin_module.__dict__]


def _get_folders_containing_synchronizer(top=os.getcwd()):
    return [os.path.dirname(os.path.join(root, name))
            for root, dirs, files in os.walk(top, topdown=False)
            for name in files if name == SYNCHRONIZER_FILE]


def _filter_folders_containing_transformer(folders):
    return [folder for folder in folders for
            root, dirs, files in os.walk(folder, topdown=False) for
            name in files if name == TRANSFORMER_FILE]


def _normalize_path_to_plugin_name(path_list, top=os.getcwd()):
    return [os.path.relpath(path, os.path.join(top, PLUGINS_FS_PATH))
            .replace(os.sep, '.') for path in path_list]
