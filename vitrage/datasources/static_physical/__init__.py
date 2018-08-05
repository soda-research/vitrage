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
# WARRANTIES OR  CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


from oslo_config import cfg
from oslo_log import versionutils

from vitrage.common.constants import DatasourceOpts as DSOpts
from vitrage.common.constants import UpdateMethod
from vitrage.common import utils

STATIC_PHYSICAL_DATASOURCE = 'static_physical'
SWITCH = 'switch'

_DEPRECATED_MSG = utils.fmt("""
`Static_physical` was deprecated in Queens and and will be removed in Stein.
Please use static Datasource.
""")

OPTS = [
    cfg.StrOpt(DSOpts.TRANSFORMER,
               default='vitrage.datasources.static_physical.transformer.'
                       'StaticPhysicalTransformer',
               help='Static physical transformer class path',
               deprecated_for_removal=True,
               deprecated_reason=_DEPRECATED_MSG,
               deprecated_since=versionutils.deprecated.QUEENS,
               required=True),
    cfg.StrOpt(DSOpts.DRIVER,
               default='vitrage.datasources.static_physical.driver.'
                       'StaticPhysicalDriver',
               help='Static physical driver class path',
               required=True),
    cfg.StrOpt(DSOpts.UPDATE_METHOD,
               default=UpdateMethod.PULL,
               help='None: updates only via Vitrage periodic snapshots.'
                    'Pull: updates every [changes_interval] seconds.'
                    'Push: updates by getting notifications from the'
                    ' datasource itself.',
               deprecated_for_removal=True,
               deprecated_reason=_DEPRECATED_MSG,
               deprecated_since=versionutils.deprecated.QUEENS,
               required=True),
    cfg.IntOpt(DSOpts.CHANGES_INTERVAL,
               default=20,
               min=5,
               help='interval between checking changes in the configuration '
                    'files of the physical topology data sources',
               deprecated_for_removal=True,
               deprecated_reason=_DEPRECATED_MSG,
               deprecated_since=versionutils.deprecated.QUEENS),

    cfg.StrOpt('directory', default='/etc/vitrage/static_datasources',
               help='Static physical data sources directory',
               deprecated_for_removal=True,
               deprecated_reason=_DEPRECATED_MSG,
               deprecated_since=versionutils.deprecated.QUEENS),
    cfg.ListOpt('entities',
                default=[SWITCH],
                help='Static physical entity types list',
                deprecated_for_removal=True,
                deprecated_reason=_DEPRECATED_MSG,
                deprecated_since=versionutils.deprecated.QUEENS)
]
