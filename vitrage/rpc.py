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


from oslo_config import cfg
from oslo_log import log
import oslo_messaging as messaging
from oslo_messaging.rpc import dispatcher
from osprofiler import profiler

OPTS = [
    cfg.StrOpt('rpc_topic',
               default='rpcapiv1',
               help='The topic vitrage listens on'),
]

LOG = log.getLogger(__name__)


class ProfilerContextSerializer(messaging.Serializer):
    def __init__(self, base):
        self._base = base

    def serialize_entity(self, context, entity):
        if not self._base:
            return entity
        return self._base.serialize_entity(context, entity)

    def deserialize_entity(self, context, entity):
        if not self._base:
            return entity
        return self._base.deserialize_entity(context, entity)

    def serialize_context(self, context):
        ctx = self._base.serialize_context(context) if self._base else {}

        pfr = profiler.get()

        if pfr:
            ctx['trace_info'] = {
                "hmac_key": pfr.hmac_key,
                "base_id": pfr.get_base_id(),
                "parent_id": pfr.get_id()
            }

        return ctx

    def deserialize_context(self, context):
        trace_info = context.pop('trace_info', None)

        if trace_info:
            profiler.init(**trace_info)

        return self._base.deserialize_context(context)\
            if self._base else context


def set_defaults(control_exchange):
    messaging.set_transport_defaults(control_exchange)


def get_client(transport, target, version_cap=None, serializer=None):
    assert transport is not None

    if profiler:
        LOG.info('profiler enabled for RPC client')
        serializer = ProfilerContextSerializer(base=serializer)

    return messaging.RPCClient(transport,
                               target,
                               version_cap=version_cap,
                               serializer=serializer)


def get_server(target, endpoints, transport, serializer=None):
    assert transport is not None

    if profiler:
        LOG.info('profiler enabled for RPC server')
        serializer = ProfilerContextSerializer(base=serializer)

    access_policy = dispatcher.DefaultRPCAccessPolicy
    return messaging.get_rpc_server(transport,
                                    target,
                                    endpoints,
                                    executor='eventlet',
                                    serializer=serializer,
                                    access_policy=access_policy)
