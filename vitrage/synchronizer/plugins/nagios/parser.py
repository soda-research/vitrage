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

from lxml import etree
from oslo_log import log
from StringIO import StringIO
from vitrage.synchronizer.plugins.nagios.properties import NagiosProperties

LOG = log.getLogger(__name__)


class NagiosParser(object):

    STATUS_TABLE_XPATH = '/html/body/table[@class="status"]'
    SERVICE_ROWS_XPATH = 'tr[position() > 1]'
    NAME_XPATH = 'table/tr/td[position()=1]/table/tr/td/a'

    def __init__(self):
        self.last_host_name = ''
        return

    def parse(self, html):
        services = []
        parser = etree.HTMLParser()

        try:
            tree = etree.parse(StringIO(html), parser)
            status_tables = tree.xpath(self.STATUS_TABLE_XPATH)

            for status_table in status_tables:
                service_rows = status_table.xpath(self.SERVICE_ROWS_XPATH)

                for service_row in service_rows:
                    service = self._parse_service_row(service_row)
                    if service:
                        services.append(service)

        except Exception as e:
            LOG.exception('Failed to get nagios services %s', e)
            return services

        return services

    def _parse_service_row(self, service_row):
        columns = service_row.getchildren()

        # service lines have a fixed number of columns.
        # there are also two blank lines between different hosts,
        # so len(columns)==1 is also valid
        # TODO(ifat_afek): get column names by the header line
        if (len(columns) == NagiosProperties.NUM_COLUMNS):
            return self._parse_service_columns(columns)

        elif (len(columns) > NagiosProperties.NUM_COLUMNS):
            LOG.warn('Too many columns in nagios service row. '
                     'Found %d', len(columns))

        elif (len(columns) > 1):
            LOG.warn('Missing columns in nagios service row. '
                     'Found only %d', len(columns))

        return None

    def _parse_service_columns(self, columns):
        host_name = self._parse_host_name(columns[0], self.NAME_XPATH)
        service_name = self._parse_cell(columns[1], self.NAME_XPATH)
        status = columns[2].text
        last_check = columns[3].text
        duration = columns[4].text
        attempt = columns[5].text
        status_information = columns[6].text

        service = {
            NagiosProperties.RESOURCE_NAME: host_name,
            NagiosProperties.SERVICE: service_name,
            NagiosProperties.STATUS: status,
            NagiosProperties.LAST_CHECK: last_check,
            NagiosProperties.DURATION: duration,
            NagiosProperties.ATTEMPT: attempt,
            NagiosProperties.STATUS_INFO: status_information
        }

        return service

    def _parse_cell(self, column, xpath):
        contents = column.xpath(xpath)

        if len(contents) == 1:
            return contents[0].text
        elif len(contents) > 1:
            LOG.warn('Multiple entries for nagios test: %s', contents.toString)
            return contents[0].text
        else:
            # len(contents) might be 0 for a host, since each host name appears
            # only once in the table
            return ''

    def _parse_host_name(self, column, xpath):
        host_name = self._parse_cell(column, xpath)

        # host name appears only once in the table, so keep
        # using the same host name until found a new one
        if host_name:
            self.last_host_name = host_name
        else:
            host_name = self.last_host_name

        return host_name
