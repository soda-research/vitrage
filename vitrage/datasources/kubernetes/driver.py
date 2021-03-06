# Copyright 2018 - Nokia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR  CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from kubernetes import client
from kubernetes import config
from oslo_log import log
from vitrage.datasources.driver_base import DriverBase
from vitrage.datasources.kubernetes.properties import KUBERNETES_DATASOURCE
from vitrage.datasources.kubernetes.properties import KubernetesProperties\
    as kubProp

LOG = log.getLogger(__name__)


class KubernetesDriver(DriverBase):

    def __init__(self, conf):
        super(KubernetesDriver, self).__init__()
        self._client = None
        self.conf = conf

    @property
    def client(self):
        if not self._client:
            self._client = self._k8s_client(self.conf)
        return self._client

    @staticmethod
    def _k8s_client(conf):
        try:
            if not conf.kubernetes.config_file:
                LOG.warning('kubernetes config file is not defined')
                return

            kubeconf = conf.kubernetes.config_file
            config.load_kube_config(config_file=kubeconf)
            k8s_client = client.CoreV1Api()
            if k8s_client is None:
                LOG.warning('k8s client returns None')
                return

            return k8s_client
        except Exception:
            LOG.exception('Create k8s client - Got Exception')

    def get_all(self, datasource_action):
        return self.make_pickleable(self._prepare_entities(
                                    self.client.list_node()),
                                    KUBERNETES_DATASOURCE,
                                    datasource_action)

    def _prepare_entities(self, nodes):
        entities = []
        for item in nodes.items:
            metadata = item.metadata
            node_details = {
                kubProp.NAME: metadata.name,
                kubProp.UID: metadata.uid,
                kubProp.CREATION_TIMESTAMP: metadata.creation_timestamp,
                kubProp.EXTERNALID: item.spec.external_id,
                kubProp.PROVIDER_NAME: item.spec.provider_id.split(":///")[0],
                }
            entities.append(node_details)
        return [{'resources': entities}]
