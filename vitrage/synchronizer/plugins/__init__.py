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

from oslo_config import cfg

# Register options for the service
OPTS = [

    cfg.ListOpt('plugin_type',
                default=['nagios',
                         'nova.host',
                         'nova.instance',
                         'nova.zone',
                         'switch'],
                help='Names of supported plugins'),

    cfg.DictOpt('nagios',
                default={
                    'synchronizer':
                        'vitrage.synchronizer.plugins.nagios.synchronizer'
                        '.NagiosSynchronizer',
                    'transformer': 'vitrage.synchronizer.plugins'
                                   '.nagios.transformer.NagiosTransformer',
                    'user': '',
                    'password': '',
                    'url': '',
                    'config_file': '/etc/vitrage/nagios_conf.yaml'},
                help='synchronizer:synchronizer path,\n'
                     'transformer:transformer path,\n'
                     'user:Nagios user,\n'
                     'password:Nagios password,\n'
                     'url:Nagios url for querying the data. Example: '
                     'http://<ip>/monitoring/nagios/cgi-bin/status.cgi\n'
                     'config_file:Nagios configuration file'
                ),

    cfg.DictOpt('nova.host',
                default={
                    'synchronizer':
                        'vitrage.synchronizer.plugins.nova.host.synchronizer'
                        '.HostSynchronizer',
                    'transformer': 'vitrage.synchronizer.plugins'
                                   '.nova.host.transformer.HostTransformer',
                    'user': '',
                    'password': '',
                    'url': '',
                    'version': '2.0',
                    'project': 'admin'},
                help='synchronizer:synchronizer path,\n'
                     'transformer:transformer path,\n'
                     'user:nova.host user,\n'
                     'password:nova.host password,\n'
                     'url:nova authentication url for querying the data'
                     'version: nova version\n'
                     'project: nova project'),

    cfg.DictOpt('nova.instance',
                default={
                    'synchronizer':
                        'vitrage.synchronizer.plugins.nova.instance'
                        '.synchronizer.InstanceSynchronizer',
                    'transformer':
                        'vitrage.synchronizer.plugins'
                        '.nova.instance.transformer.InstanceTransformer',
                    'user': '',
                    'password': '',
                    'url': '',
                    'version': '2.0',
                    'project': 'admin'},
                help='synchronizer:synchronizer path,\n'
                     'transformer:transformer path,\n'
                     'user:nova.instance user,\n'
                     'password:nova.instance password,\n'
                     'url:nova authentication url for querying the data'
                     'version: nova version\n'
                     'project: nova project'),

    cfg.DictOpt('nova.zone',
                default={
                    'synchronizer':
                        'vitrage.synchronizer.plugins.nova.zone.synchronizer'
                        '.ZoneSynchronizer',
                    'transformer': 'vitrage.synchronizer.plugins'
                                   '.nova.zone.transformer.ZoneTransformer',
                    'user': '',
                    'password': '',
                    'url': '',
                    'version': '2.0',
                    'project': 'admin'},
                help='synchronizer:synchronizer path,\n'
                     'transformer:transformer path,\n'
                     'user:nova.zone user,\n'
                     'password:nova.zone password,\n'
                     'url:nova authentication url for querying the data'
                     'version: nova version\n'
                     'project: nova project'),

    cfg.DictOpt('switch',
                default={
                    'synchronizer':
                        'vitrage.synchronizer.plugins.static_physical'
                        '.synchronizer.StaticPhysicalSynchronizer',
                    'transformer':
                        'vitrage.synchronizer.plugins.static_physical.'
                        'transformer.StaticPhysicalTransformer',
                    'dir': '/etc/vitrage/static_plugins'},
                help='synchronizer:synchronizer path,\n'
                     'transformer:transformer path,\n'
                     'dir: A path for the static plugins for the '
                     'synchronizer'),
]
