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
from oslo_log import log
import sys

from vitrage.cli import VITRAGE_TITLE
from vitrage.common.utils import spawn
from vitrage.entity_graph.graph_init import VitrageGraphInit
from vitrage.entity_graph.workers import GraphWorkersManager
from vitrage import service

LOG = log.getLogger(__name__)


def main():
    """Main method of vitrage-graph"""

    conf = service.prepare_service()
    LOG.info(VITRAGE_TITLE)

    workers = GraphWorkersManager(conf)
    spawn(init, conf, workers)
    workers.run()


def init(conf, workers):
    # Because fork duplicates the process memory.
    # We should only create master process resources after workers are forked.
    workers.wait_for_worker_start()
    VitrageGraphInit(conf, workers).run()

if __name__ == "__main__":
    sys.exit(main())
