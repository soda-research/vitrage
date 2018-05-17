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

import sys

from vitrage.cli import VITRAGE_TITLE
from vitrage.entity_graph import get_graph_driver
from vitrage.entity_graph.graph_init import VitrageGraphInit
from vitrage import service
from vitrage import storage


def main():
    """Main method of vitrage-graph"""

    print(VITRAGE_TITLE)
    conf = service.prepare_service()
    e_graph = get_graph_driver(conf)('Entity Graph')
    db_connection = storage.get_connection_from_config(conf)
    clear_active_actions_table(db_connection)

    VitrageGraphInit(conf, e_graph, db_connection).run()


def clear_active_actions_table(db_connection):
    """Delete all data from active_actions table

    The following deletes the entire vitrage database
    It should be removed once graph is persistent
    """
    db_connection.active_actions.delete()


if __name__ == "__main__":
    sys.exit(main())
