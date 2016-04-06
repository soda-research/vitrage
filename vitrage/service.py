# Copyright 2015 - Alcatel-Lucent
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

import logging

from oslo_config import cfg
from oslo_log import log
from oslo_policy import opts as policy_opts
from oslo_utils import importutils

from vitrage import keystone_client
from vitrage import messaging
from vitrage import opts

LOG = log.getLogger(__name__)


def prepare_service(args=None, conf=None, config_files=None):
    if conf is None:
        conf = cfg.ConfigOpts()
    log.register_options(conf)
    policy_opts.set_defaults(conf)

    for group, options in opts.list_opts():
        conf.register_opts(list(options),
                           group=None if group == 'DEFAULT' else group)

    conf(args, project='vitrage', validate_default_values=True,
         default_config_files=config_files)

    for datasource in conf.datasources.types:
        load_datasource(conf, datasource, conf.datasources.path)

    keystone_client.register_keystoneauth_opts(conf)

    keystone_client.setup_keystoneauth(conf)
    log.setup(conf, 'vitrage')
    conf.log_opt_values(LOG, logging.DEBUG)
    messaging.setup()

    return conf


def load_datasource(conf, name, paths):
    for path in paths:
        try:
            opt = importutils.import_module("%s.%s" % (path, name)).OPTS
            conf.register_opts(list(opt),
                               group=None if name == 'DEFAULT' else name)
            return
        except ImportError:
            pass

    LOG.error("Failed to register config options for plugin %s" % name)
