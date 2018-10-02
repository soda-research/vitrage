# Copyright 2018 - Nokia
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
from base64 import standard_b64decode
from six.moves import cPickle
import time
import zlib

from oslo_log import log
import oslo_messaging

from vitrage import messaging
from vitrage import rpc as vitrage_rpc

LOG = log.getLogger(__name__)


def create_rpc_client_instance(conf):
    transport = messaging.get_rpc_transport(conf)
    target = oslo_messaging.Target(topic=conf.rpc_topic_collector)
    client = vitrage_rpc.get_client(transport, target)
    return client


def get_all(rpc_client, events_coordination, driver_names, action,
            retry_on_fault=False):
    LOG.info('get_all starting for %s', driver_names)
    t1 = time.time()

    def _call():
        result = rpc_client.call(
            {},
            'driver_get_all',
            driver_names=driver_names,
            action=action,
            retry_on_fault=retry_on_fault)
        events = cPickle.loads(zlib.decompress(standard_b64decode(result)))
        for e in events:
            yield e

    try:
        events = _call()
    except oslo_messaging.MessagingTimeout:
        LOG.exception('Got MessagingTimeout')
        events = _call() if retry_on_fault else []
    t2 = time.time()
    count = events_coordination.handle_multiple_low_priority(events)
    t3 = time.time()
    LOG.info('get_all took %s, processing took %s for %s events',
             t2 - t1, t3 - t2, count)


def get_changes(rpc_client, events_coordination, driver_name):
    LOG.info('get_changes starting %s', driver_name)
    result = rpc_client.call(
        {},
        'driver_get_changes',
        driver_name=driver_name)
    events = cPickle.loads(zlib.decompress(standard_b64decode(result)))
    events_coordination.handle_multiple_low_priority(events)
