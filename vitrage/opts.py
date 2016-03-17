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

from oslo_config import cfg
from oslo_log import log
from oslo_policy import opts as policy_opts
from oslo_utils import importutils

import vitrage.api
import vitrage.clients
import vitrage.entity_graph.consistency
import vitrage.evaluator
import vitrage.keystone_client
import vitrage.rpc
import vitrage.synchronizer
import vitrage.synchronizer.plugins

PLUGINS_PATH = 'vitrage.synchronizer.plugins.'


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


# This is made for documentation and configuration purposes
def plugins_opts():
    conf = cfg.ConfigOpts()
    log.register_options(conf)
    policy_opts.set_defaults(conf)

    for group, options in list_opts():
        conf.register_opts(list(options),
                           group=None if group == 'DEFAULT' else group)

    return [(plugin_name, importutils.import_module(PLUGINS_PATH + plugin_name)
             .OPTS)
            for plugin_name in conf.synchronizer_plugins.plugin_type]
