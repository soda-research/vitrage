# Copyright 2016 - Nokia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo_config import cfg

OPTS = [
    cfg.StrOpt('notifier',
               default='vitrage.notifier.plugins.nova.'
                       'nova_notifier.NovaNotifier',
               help='nova notifier class path',
               required=True),
    cfg.BoolOpt('enable_host_evacuate', default=False,
                help='Evacuate a host that is marked as down'),
    cfg.BoolOpt('on_shared_storage', default=False,
                help='Indicates that all instance files are '
                     'on a shared storage'),
]
