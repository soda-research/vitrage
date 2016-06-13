# Copyright 2016 - Nokia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,  software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND,  either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo_config import cfg

ZABBIX_DATASOURCE = 'zabbix'

OPTS = [
    cfg.StrOpt('transformer',
               default='vitrage.datasources.zabbix.transformer.'
                       'ZabbixTransformer',
               help='Zabbix transformer class path',
               required=True),
    cfg.StrOpt('driver',
               default='vitrage.datasources.zabbix.driver.ZabbixDriver',
               help='Zabbix driver class path',
               required=True),
    cfg.IntOpt('changes_interval',
               default=30,
               min=30,
               help='interval between checking changes in zabbix data source',
               required=True),
    cfg.StrOpt('user', default='admin',
               help='Zabbix user name'),
    cfg.StrOpt('password', default='zabbix',
               help='Zabbix user password'),
    cfg.StrOpt('url', default='',
               help='Zabbix url'),
    cfg.StrOpt('config_file', default='/etc/vitrage/zabbix_conf.yaml',
               help='Zabbix configuration file'),
]
