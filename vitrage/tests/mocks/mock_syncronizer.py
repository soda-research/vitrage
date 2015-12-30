# Copyright 2015 - Alcatel-Lucent
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


"""Methods for generating synchronizer events

For each type of entity, need to supply configuration files that specify (a
regex of) what can be returned, which will be used to generate sync events

usage example:
    test_entity_spec_list = [
        {mg.DYNAMIC_INFO_FKEY: 'dynamic_snapshot.json',
         mg.STATIC_INFO_FKEY: 'static_snapshot.json',
         mg.MAPPING_KEY: [('vm1', 'host1'), ('vm2', 'host1'), ('vm3','host2')],
         mg.NAME_KEY: 'Instance (vm) generator',
         NUM_EVENTS_KEY: 10
         }
    ]
    spec_list = get_mock_generators(test_entity_spec_list)
    events = generate_random_events_list(spec_list)
    for e in events:
        print e
"""

import random

import vitrage.tests.mocks.trace_generator as tg


def generate_random_events_list(generator_spec_list):
    """Generates random events for the generators given.

     Each element in the list of generators includes a generator and
     number of events to generate for it's entities

     :param generator_spec_list: list of generators
     :type generator_spec_list: list

     :param default_num: default number of events to generate
     :type default_num: list

     :return list of synchronizer events
     :rtype list

    """

    data = []
    for spec in generator_spec_list:
        generator = spec[tg.GENERATOR]
        data += tg.generate_data_stream(generator.models, spec[tg.NUM_EVENTS])
    random.shuffle(data)
    return data


def simple_instance_generators(host_num, vm_num,
                               snapshot_events=0, update_events=0,
                               snap_vals=None, update_vals=None):
    """A function for returning vm event generators.

    Returns generators for a given number of hosts and
    instances. Instances will be distributed across hosts in round-robin style.

    :param host_num: number of hosts
    :param vm_num: number of vms
    :param snapshot_events: number of snapshot events per instance
    :param update_events: number of update events per instance
    :param snap_vals: preset vals for ALL snapshot events
    :param update_vals: preset vals for ALL update events
    :return: generators for vm_num vms as specified
    """

    mapping = [('vm-{0}'.format(index), 'host-{0}'.format(index % host_num))
               for index in range(vm_num)
               ]

    test_entity_spec_list = []
    if snapshot_events:
        test_entity_spec_list.append(
            {tg.DYNAMIC_INFO_FKEY: tg.SYNC_INST_SNAPSHOT_D,
             tg.STATIC_INFO_FKEY: tg.SYNC_INST_SNAPSHOT_S,
             tg.EXTERNAL_INFO_KEY: snap_vals,
             tg.MAPPING_KEY: mapping,
             tg.NAME_KEY: 'Instance (vm) snapshot generator',
             tg.NUM_EVENTS: snapshot_events
             }
        )
    if update_events:
        test_entity_spec_list.append(
            {tg.DYNAMIC_INFO_FKEY: tg.SYNC_INST_UPDATE_D,
             tg.STATIC_INFO_FKEY: None,
             tg.EXTERNAL_INFO_KEY: update_vals,
             tg.MAPPING_KEY: mapping,
             tg.NAME_KEY: 'Instance (vm) update generator',
             tg.NUM_EVENTS: update_events
             }
        )
    return tg.get_trace_generators(test_entity_spec_list)
