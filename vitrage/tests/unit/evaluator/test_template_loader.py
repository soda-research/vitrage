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

from oslo_config import cfg
from oslo_log import log as logging

from vitrage.evaluator import template_loader
from vitrage.tests import base
from vitrage.tests.mocks import utils


LOG = logging.getLogger(__name__)


class TemplateLoaderTest(base.BaseTest):

    OPTS = [
        cfg.StrOpt('templates_dir',
                   default=utils.get_resources_dir() + '/templates',
                   ),
    ]

    def setUp(self):
        super(TemplateLoaderTest, self).setUp()

        self.template_dir_path = utils.get_resources_dir() + '/templates'

        self.conf = cfg.ConfigOpts()
        self.conf.register_opts(self.OPTS, group='evaluator')

    def test_template_loader(self):

        # Setup
        total_templates = os.listdir(self.template_dir_path)

        # Action
        template_configs = template_loader.load_templates_files(self.conf)

        # Test assertions
        self.assertEqual(len(total_templates), len(template_configs))
