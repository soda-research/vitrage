# Copyright 2015 - Alcatel-Lucent
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

from oslo_service import service as os_service

from vitrage import entity_graph as entity_graph_svc
from vitrage import service


def entity_graph():
    conf = service.prepare_service()
    os_service.launch(conf,
                      entity_graph_svc.VitrageEntityGraphService(conf)).wait()
