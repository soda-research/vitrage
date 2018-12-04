# Copyright 2018 - Nokia Corporation
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

from oslo_log import log
from vitrage.api_handler.apis.base import EntityGraphApisBase

LOG = log.getLogger(__name__)


class OperationalApis(EntityGraphApisBase):

    def __init__(self, conf, graph):
        self.conf = conf
        self.graph = graph

    def is_alive(self, ctx):
        try:
            if self.graph and self.graph.ready:
                return True
        except Exception:
            LOG.exception("is_alive check failed.")
        LOG.warning("Api during initialization - graph not ready")
        return False