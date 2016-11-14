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
from oslo_log import log as logging

from vitrage.common.constants import UpdateMethod
from vitrage.datasources.static import STATIC_DATASOURCE
from vitrage.datasources.static.transformer import StaticTransformer
from vitrage.tests import base

LOG = logging.getLogger(__name__)


class TestStaticTransformer(base.BaseTest):

    OPTS = [
        cfg.StrOpt('update_method',
                   default=UpdateMethod.PULL),
    ]

    # noinspection PyAttributeOutsideInit,PyPep8Naming
    @classmethod
    def setUpClass(cls):
        cls.transformers = {}
        cls.conf = cfg.ConfigOpts()
        cls.conf.register_opts(cls.OPTS, group=STATIC_DATASOURCE)
        cls.transformers[STATIC_DATASOURCE] = \
            StaticTransformer(cls.transformers, cls.conf)

    def test_snapshot_transform(self):
        pass

    def test_update_transform(self):
        pass
