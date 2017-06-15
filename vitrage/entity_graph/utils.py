# Copyright 2017 - Nokia
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

from oslo_utils import importutils as utils

from vitrage.common.constants import DatasourceOpts as DSOpts
from vitrage.common.constants import UpdateMethod
from vitrage.utils import opt_exists


def get_drivers(conf):
    return {datasource: utils.import_object(conf[datasource].driver, conf)
            for datasource in conf.datasources.types}


def get_pull_datasources(conf):
    return (datasource for datasource in conf.datasources.types
            if conf[datasource].update_method.lower() == UpdateMethod.PULL
            and opt_exists(conf[datasource], DSOpts.CHANGES_INTERVAL))


def get_push_datasources(drivers, conf):
    return (driver_cls for datasource, driver_cls in drivers.items()
            if conf[datasource].update_method.lower() == UpdateMethod.PUSH)
