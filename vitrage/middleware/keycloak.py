# Copyright 2017 - Nokia
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

import jwt
import requests

from oslo_config import cfg
from oslo_middleware import base
from oslo_serialization import jsonutils
from webob import exc

OPENID_CONNECT_USERINFO = '%s/realms/%s/protocol/openid-connect/userinfo'

KEYCLOAK_OPTS = [
    cfg.StrOpt('auth_url', default='http://127.0.0.1:9080/auth',
               help='Keycloak authentication server ip',),
    cfg.StrOpt('insecure', default=False,
               help='If True, SSL/TLS certificate verification is disabled'),
]


class KeycloakAuth(base.ConfigurableMiddleware):

    def __init__(self, application, conf=None):
        super(KeycloakAuth, self).__init__(application, conf)

        self.oslo_conf.register_opts(KEYCLOAK_OPTS, 'keycloak')
        self.auth_url = self._conf_get('auth_url', 'keycloak')
        self.insecure = self._conf_get('insecure', 'keycloak')

    @property
    def reject_auth_headers(self):
        header_val = 'Keycloak uri=\'%s\'' % self.auth_url
        return [('WWW-Authenticate', header_val)]

    @property
    def roles(self):
        decoded = {}
        try:
            decoded = jwt.decode(self.token, algorithms=['RS256'],
                                 verify=False)
        except jwt.DecodeError:
            message = "Token can't be decoded because of wrong format."
            self._unauthorized(message)

        return ','.join(decoded['realm_access']['roles']) \
            if 'realm_access' in decoded else ''

    def process_request(self, req):
            self._authenticate(req)

    def _authenticate(self, req):
        self.token = req.headers.get('X-Auth-Token')
        if self.token:
            self._decode(req)
        else:
            message = 'Auth token must be provided in "X-Auth-Token" header.'
            self._unauthorized(message)

    def _decode(self, req):
        realm_name = req.headers.get('X-Project-Id')
        endpoint = OPENID_CONNECT_USERINFO % (self.auth_url, realm_name)
        headers = {'Authorization': 'Bearer %s' % self.token}

        resp = requests.get(endpoint, headers=headers,
                            verify=not self.insecure)

        resp.raise_for_status()

        self._set_req_headers(req)

    def _set_req_headers(self, req):
        req.headers['X-Identity-Status'] = 'Confirmed'
        req.headers['X-Roles'] = self.roles

    def _unauthorized(self, message):
        body = {'error': {
            'code': 401,
            'title': 'Unauthorized',
            'message': message,
        }}

        raise exc.HTTPUnauthorized(body=jsonutils.dumps(body),
                                   headers=self.reject_auth_headers,
                                   charset='UTF-8',
                                   content_type='application/json')


filter_factory = KeycloakAuth.factory
