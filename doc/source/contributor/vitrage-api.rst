..
      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

Vitrage API
-----------
|

.. contents:: Contents:
   :local:

Overview
********
**This document describes the Vitrage API v1.**

**The Vitrage API provides a RESTful JSON interface for interacting with Vitrage Service.**

List Versions
^^^^^^^^^^^^^

Lists the supported versions of the Vitrage API.

GET /
~~~~~

Headers
=======

-  X-Auth-Token (string, required) - Keystone auth token
-  Accept (string) - application/json

Path Parameters
===============

None.

Query Parameters
================

None.

Request Body
============

None.

Request Examples
================

::

    GET / HTTP/1.1
    Host: 135.248.19.18:8999
    X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7
    Accept: application/json



ResponseStatus code
===================

-  200 - OK

Response Body
=============

Returns a JSON object with a 'links' array of links of supported versions.

Response Examples
=================

::

    {
        "versions": [
            {
               "id": "v1.0",
              "links": [
                    {
                     "href": "http://135.248.19.18:8999/v1/",
                    "rel": "self"
                   }
              ],
              "status": "CURRENT",
              "updated": "2015-11-29"
            }
        ]

    }



Get  topology
^^^^^^^^^^^^^

Get the topology for the cluster.
Its possible to filter the edges vertices and depth of the
graph


POST /v1/topology/
~~~~~~~~~~~~~~~~~~

Headers
=======

-  X-Auth-Token (string, required) - Keystone auth token
-  Accept (string) - application/json

Path Parameters
===============

None.

Query Parameters
================

None

Request Body
============

Consists of a topology request definition which has the following properties:

* root - (string, optional) the root node to start. defaults to the openstack node
* depth - (int, optional) the depth of the topology graph. defaults to max depth
* graph_type-(string, optional) can be either tree or graph. defaults to graph
* query - (string, optional) a json query filter to filter the graph components. defaults to return all the graph
* all_tenants - (boolean, optional) shows the entities of all the tenants in the graph (in case the user has the permissions).

.. note:: **parameter graph_type=graph with depth parameter requires root parameter**

query expression
================
::

 query := expression
 expression := simple_expression|complex_expression
 simple_expression := {simple_operator: {field_name: value}}
 simple_operator := == | != | < | <= | > | >=
 complex_expression := {complex_operator: [expression, expression, ...]} | not_expression
 not_expression := {not: expression}
 complex_operator := and | or


Query example
=============

::

    POST /v1/topology/
    Host: 135.248.19.18:8999
    Content-Type: application/json
    X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7

    {
        "query" :"
         {
            \"or\": [
              {
                \"==\": {
                  \"vitrage_type\": \"nova.host\"
                }
              },
              {
                \"==\": {
                  \"vitrage_type\": \"nova.instance\"
                }
              },
              {
                \"==\": {
                  \"vitrage_type\": \"nova.zone\"
                }
              },
              {
                \"==\": {
                  \"vitrage_type\": \"openstack.cluster\"
                }
              }
            ]

         }",
         "graph_type" : "tree"
     }

Response Status Code
====================

-  200 - OK
-  400 - Bad request

Response Body
=============

Returns a JSON object that describes a graph with nodes
and links. If a tree representation is asked then returns
a Json tree with nodes and children.

An error of cannot represent as a tree will be return if the
graph is not a tree. (400 - Bad request)

Response Examples
=================

::

 {
  "directed": true,
  "graph": {},
  "nodes": [
    {
      "vitrage_category": "RESOURCE",
      "vitrage_is_placeholder": false,
      "vitrage_is_deleted": false,
      "name": "vm-8",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "vitrage_type": "nova.instance",
      "id": "20d12a8a-ea9a-89c6-5947-83bea959362e",
      "graph_index": 0,
      "vitrage_id": "RESOURCE:nova.instance:20d12a8a-ea9a-89c6-5947-83bea959362e"
    },
    {
      "vitrage_category": "RESOURCE",
      "vitrage_is_placeholder": false,
      "vitrage_is_deleted": false,
      "name": "vm-2",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "vitrage_type": "nova.instance",
      "id": "dc35fa2f-4515-1653-ef6b-03b471bb395b",
      "graph_index": 1,
      "vitrage_id": "RESOURCE:nova.instance:dc35fa2f-4515-1653-ef6b-03b471bb395b"
    },
    {
      "vitrage_category": "RESOURCE",
      "vitrage_is_placeholder": false,
      "vitrage_is_deleted": false,
      "name": "vm-13",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "vitrage_type": "nova.instance",
      "id": "9879cf5a-bdcf-3651-3017-961ed887ec86",
      "graph_index": 2,
      "vitrage_id": "RESOURCE:nova.instance:9879cf5a-bdcf-3651-3017-961ed887ec86"
    },
    {
      "vitrage_category": "RESOURCE",
      "vitrage_is_placeholder": false,
      "vitrage_is_deleted": false,
      "name": "vm-10",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "vitrage_type": "nova.instance",
      "id": "fe124f4b-9ed7-4591-fcd1-803cf5c33cb1",
      "graph_index": 3,
      "vitrage_id": "RESOURCE:nova.instance:fe124f4b-9ed7-4591-fcd1-803cf5c33cb1"
    },
    {
      "vitrage_category": "RESOURCE",
      "vitrage_is_placeholder": false,
      "vitrage_is_deleted": false,
      "name": "vm-11",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "vitrage_type": "nova.instance",
      "id": "f2e48a97-7350-061e-12d3-84c6dc3e67c0",
      "graph_index": 4,
      "vitrage_id": "RESOURCE:nova.instance:f2e48a97-7350-061e-12d3-84c6dc3e67c0"
    },
    {
      "vitrage_category": "RESOURCE",
      "vitrage_is_placeholder": false,
      "vitrage_is_deleted": false,
      "name": "host-2",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "available",
      "vitrage_type": "nova.host",
      "id": "host-2",
      "graph_index": 5,
      "vitrage_id": "RESOURCE:nova.host:host-2"
    },
    {
      "vitrage_category": "RESOURCE",
      "vitrage_is_placeholder": false,
      "vitrage_is_deleted": false,
      "name": "host-3",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "available",
      "vitrage_type": "nova.host",
      "id": "host-3",
      "graph_index": 6,
      "vitrage_id": "RESOURCE:nova.host:host-3"
    },
    {
      "vitrage_category": "RESOURCE",
      "vitrage_is_placeholder": false,
      "vitrage_is_deleted": false,
      "name": "host-0",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "available",
      "vitrage_type": "nova.host",
      "id": "host-0",
      "graph_index": 7,
      "vitrage_id": "RESOURCE:nova.host:host-0"
    },
    {
      "vitrage_category": "RESOURCE",
      "vitrage_is_placeholder": false,
      "vitrage_is_deleted": false,
      "name": "host-1",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "available",
      "vitrage_type": "nova.host",
      "id": "host-1",
      "graph_index": 8,
      "vitrage_id": "RESOURCE:nova.host:host-1"
    },
    {
      "vitrage_category": "RESOURCE",
      "vitrage_is_placeholder": false,
      "vitrage_is_deleted": false,
      "name": "vm-9",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "vitrage_type": "nova.instance",
      "id": "275097cf-954e-8e24-b185-9514e24b8591",
      "graph_index": 9,
      "vitrage_id": "RESOURCE:nova.instance:275097cf-954e-8e24-b185-9514e24b8591"
    },
    {
      "vitrage_category": "RESOURCE",
      "vitrage_is_placeholder": false,
      "vitrage_is_deleted": false,
      "name": "vm-1",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "vitrage_type": "nova.instance",
      "id": "a0f0805f-c804-cffe-c25a-1b38f555ed68",
      "graph_index": 10,
      "vitrage_id": "RESOURCE:nova.instance:a0f0805f-c804-cffe-c25a-1b38f555ed68"
    },
    {
      "vitrage_category": "RESOURCE",
      "vitrage_is_placeholder": false,
      "vitrage_is_deleted": false,
      "name": "vm-14",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "vitrage_type": "nova.instance",
      "id": "56af57d2-34a4-19b1-5106-b613637a11a7",
      "graph_index": 11,
      "vitrage_id": "RESOURCE:nova.instance:56af57d2-34a4-19b1-5106-b613637a11a7"
    },
    {
      "vitrage_category": "RESOURCE",
      "vitrage_is_placeholder": false,
      "vitrage_is_deleted": false,
      "name": "zone-1",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "available",
      "vitrage_type": "nova.zone",
      "id": "zone-1",
      "graph_index": 12,
      "vitrage_id": "RESOURCE:nova.zone:zone-1"
    },
    {
      "vitrage_category": "RESOURCE",
      "vitrage_is_placeholder": false,
      "vitrage_is_deleted": false,
      "name": "vm-3",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "vitrage_type": "nova.instance",
      "id": "16e14c58-d254-2bec-53e4-c766e48810aa",
      "graph_index": 13,
      "vitrage_id": "RESOURCE:nova.instance:16e14c58-d254-2bec-53e4-c766e48810aa"
    },
    {
      "vitrage_category": "RESOURCE",
      "vitrage_is_placeholder": false,
      "vitrage_is_deleted": false,
      "name": "vm-7",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "vitrage_type": "nova.instance",
      "id": "f35a1e10-74ff-7332-8edf-83cd6ffcb2de",
      "graph_index": 14,
      "vitrage_id": "RESOURCE:nova.instance:f35a1e10-74ff-7332-8edf-83cd6ffcb2de"
    },
    {
      "vitrage_category": "RESOURCE",
      "vitrage_is_placeholder": false,
      "vitrage_is_deleted": false,
      "name": "vm-4",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "vitrage_type": "nova.instance",
      "id": "ea8a450e-cab1-2272-f431-494b40c5c378",
      "graph_index": 15,
      "vitrage_id": "RESOURCE:nova.instance:ea8a450e-cab1-2272-f431-494b40c5c378"
    },
    {
      "vitrage_category": "RESOURCE",
      "vitrage_is_placeholder": false,
      "vitrage_is_deleted": false,
      "name": "vm-6",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "vitrage_type": "nova.instance",
      "id": "6e42bdc3-b776-1b2c-2c7d-b7a8bb98f721",
      "graph_index": 16,
      "vitrage_id": "RESOURCE:nova.instance:6e42bdc3-b776-1b2c-2c7d-b7a8bb98f721"
    },
    {
      "vitrage_category": "RESOURCE",
      "vitrage_is_placeholder": false,
      "vitrage_is_deleted": false,
      "name": "vm-5",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "vitrage_type": "nova.instance",
      "id": "8c951613-c660-87c0-c18b-0fa3293ce8d8",
      "graph_index": 17,
      "vitrage_id": "RESOURCE:nova.instance:8c951613-c660-87c0-c18b-0fa3293ce8d8"
    },
    {
      "vitrage_category": "RESOURCE",
      "vitrage_is_placeholder": false,
      "vitrage_is_deleted": false,
      "name": "zone-0",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "available",
      "vitrage_type": "nova.zone",
      "id": "zone-0",
      "graph_index": 18,
      "vitrage_id": "RESOURCE:nova.zone:zone-0"
    },
    {
      "vitrage_category": "RESOURCE",
      "vitrage_is_placeholder": false,
      "vitrage_is_deleted": false,
      "name": "vm-0",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "vitrage_type": "nova.instance",
      "id": "78353ce4-2710-49b5-1341-b8cbb6000ebc",
      "graph_index": 19,
      "vitrage_id": "RESOURCE:nova.instance:78353ce4-2710-49b5-1341-b8cbb6000ebc"
    },
    {
      "vitrage_category": "RESOURCE",
      "vitrage_is_placeholder": false,
      "vitrage_is_deleted": false,
      "name": "vm-12",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "vitrage_type": "nova.instance",
      "id": "35bf479a-75d9-80a9-874e-d3b50fb2dd2e",
      "graph_index": 20,
      "vitrage_id": "RESOURCE:nova.instance:35bf479a-75d9-80a9-874e-d3b50fb2dd2e"
    },
    {
      "vitrage_category": "RESOURCE",
      "vitrage_is_placeholder": false,
      "vitrage_is_deleted": false,
      "name": "openstack.cluster",
      "vitrage_type": "openstack.cluster",
      "id": "openstack.cluster",
      "graph_index": 21,
      "vitrage_id": "RESOURCE:openstack.cluster"
    }
  ],
  "links": [
    {
      "relationship_type": "contains",
      "vitrage_is_deleted": false,
      "target": 3,
      "key": "contains",
      "source": 5
    },
    {
      "relationship_type": "contains",
      "vitrage_is_deleted": false,
      "target": 1,
      "key": "contains",
      "source": 5
    },
    {
      "relationship_type": "contains",
      "vitrage_is_deleted": false,
      "target": 16,
      "key": "contains",
      "source": 5
    },
    {
      "relationship_type": "contains",
      "vitrage_is_deleted": false,
      "target": 11,
      "key": "contains",
      "source": 5
    },
    {
      "relationship_type": "contains",
      "vitrage_is_deleted": false,
      "target": 13,
      "key": "contains",
      "source": 6
    },
    {
      "relationship_type": "contains",
      "vitrage_is_deleted": false,
      "target": 4,
      "key": "contains",
      "source": 6
    },
    {
      "relationship_type": "contains",
      "vitrage_is_deleted": false,
      "target": 14,
      "key": "contains",
      "source": 6
    },
    {
      "relationship_type": "contains",
      "vitrage_is_deleted": false,
      "target": 20,
      "key": "contains",
      "source": 7
    },
    {
      "relationship_type": "contains",
      "vitrage_is_deleted": false,
      "target": 0,
      "key": "contains",
      "source": 7
    },
    {
      "relationship_type": "contains",
      "vitrage_is_deleted": false,
      "target": 19,
      "key": "contains",
      "source": 7
    },
    {
      "relationship_type": "contains",
      "vitrage_is_deleted": false,
      "target": 15,
      "key": "contains",
      "source": 7
    },
    {
      "relationship_type": "contains",
      "vitrage_is_deleted": false,
      "target": 9,
      "key": "contains",
      "source": 8
    },
    {
      "relationship_type": "contains",
      "vitrage_is_deleted": false,
      "target": 10,
      "key": "contains",
      "source": 8
    },
    {
      "relationship_type": "contains",
      "vitrage_is_deleted": false,
      "target": 2,
      "key": "contains",
      "source": 8
    },
    {
      "relationship_type": "contains",
      "vitrage_is_deleted": false,
      "target": 17,
      "key": "contains",
      "source": 8
    },
    {
      "relationship_type": "contains",
      "vitrage_is_deleted": false,
      "target": 6,
      "key": "contains",
      "source": 12
    },
    {
      "relationship_type": "contains",
      "vitrage_is_deleted": false,
      "target": 8,
      "key": "contains",
      "source": 12
    },
    {
      "relationship_type": "contains",
      "vitrage_is_deleted": false,
      "target": 5,
      "key": "contains",
      "source": 18
    },
    {
      "relationship_type": "contains",
      "vitrage_is_deleted": false,
      "target": 7,
      "key": "contains",
      "source": 18
    },
    {
      "relationship_type": "contains",
      "vitrage_is_deleted": false,
      "target": 18,
      "key": "contains",
      "source": 21
    },
    {
      "relationship_type": "contains",
      "vitrage_is_deleted": false,
      "target": 12,
      "key": "contains",
      "source": 21
    }
  ],
  "multigraph": true
 }

Show RCA
^^^^^^^^

Shows the root cause analysis on an alarm.

GET /v1/rca/
~~~~~~~~~~~~

Headers
=======

-  X-Auth-Token (string, required) - Keystone auth token
-  Accept (string) - application/json

Path Parameters
===============

None.

Query Parameters
================

alarm id - (string(255)) get rca on this alarm.

Request Body
============

* all_tenants - (boolean, optional) shows the rca of all tenants (in case the user has the permissions).

Request Examples
================

::

    GET /v1/rca/alarm_id=ALARM%3Anagios%3Ahost0%3ACPU%20load HTTP/1.1
    Host: 135.248.19.18:8999
    X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7
    Accept: application/json



Response Status code
====================

-  200 - OK

Response Body
=============

Returns a JSON object represented as a graph with all the alarms that either causing the alarm or caused by the requested alarm.

Response Examples
=================

::

 {
  "directed": true,
  "graph": {

  },
  "nodes": [
    {
      "vitrage_category": "ALARM",
      "vitrage_type": "nagios",
      "name": "CPU load",
      "state": "Active",
      "severity": "WARNING",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "info": "WARNING - 15min load 1.66 at 32 CPUs",
      "resource_type": "nova.host",
      "resource_name": "host-0",
      "resource_id": "host-0",
      "id": 0,
      "vitrage_id": "ALARM:nagios:host0:CPU load"
    },
    {
      "vitrage_category": "ALARM",
      "vitrage_type": "vitrage",
      "name": "Machine Suboptimal",
      "state": "Active",
      "severity": "WARNING",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "resource_type": "nova.instance",
      "resource_name": "vm0",
      "resource_id": "20d12a8a-ea9a-89c6-5947-83bea959362e",
      "id": 1,
      "vitrage_id": "ALARM:vitrage:vm0:Machine Suboptimal"
    },
    {
      "vitrage_category": "ALARM",
      "vitrage_type": "vitrage",
      "name": "Machine Suboptimal",
      "state": "Active",
      "severity": "WARNING",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "resource_type": "nova.instance",
      "resource_name": "vm1",
      "resource_id": "275097cf-954e-8e24-b185-9514e24b8591",
      "id": 2,
      "vitrage_id": "ALARM:vitrage:vm1:Machine Suboptimal"
    }
  ],
  "links": [
    {
      "source": 0,
      "target": 1,
      "relationship": "causes"
    },
    {
      "source": 0,
      "target": 2,
      "relationship": "causes"
    }
  ],
  "multigraph": false,
  "inspected_index": 0
 }


List Alarms
^^^^^^^^^^^

Shows the alarms on a resource or all alarms

GET /v1/alarm/
~~~~~~~~~~~~~~

Headers
=======

-  X-Auth-Token (string, required) - Keystone auth token
-  Accept (string) - application/json

Path Parameters
===============

None.

Query Parameters
================

vitrage_id - (string(255)) get alarm on this resource can be 'all' for all alarms.

Request Body
============

* all_tenants - (boolean, optional) shows the alarms of all tenants (in case the user has the permissions).

Request Examples
================

::

    GET /v1/alarms/?vitrage_id=all HTTP/1.1
    Host: 135.248.19.18:8999
    X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7
    Accept: application/json

Response Status code
====================

-  200 - OK

Response Body
=============

Returns a JSON object with all the alarms requested.

Response Examples
=================

::


  [
     {
       "vitrage_category": "ALARM",
       "vitrage_type": "nagios",
       "name": "CPU load",
       "state": "Active",
       "severity": "WARNING",
       "update_timestamp": "2015-12-01T12:46:41Z",
       "info": "WARNING - 15min load 1.66 at 32 CPUs",
       "resource_type": "nova.host",
       "resource_name": "host-0",
       "resource_id": "host-0",
       "id": 0,
       "vitrage_id": "ALARM:nagios:host0:CPU load",
       "normalized_severity": "WARNING"
     },
     {
       "vitrage_category": "ALARM",
       "vitrage_type": "vitrage",
       "name": "Machine Suboptimal",
       "state": "Active",
       "severity": "CRITICAL",
       "update_timestamp": "2015-12-01T12:46:41Z",
       "resource_type": "nova.instance",
       "resource_name": "vm0",
       "resource_id": "20d12a8a-ea9a-89c6-5947-83bea959362e",
       "id": 1,
       "vitrage_id": "ALARM:vitrage:vm0:Machine Suboptimal",
       "normalized_severity": "CRITICAL"
     },
     {
       "vitrage_category": "ALARM",
       "vitrage_type": "vitrage",
       "name": "Machine Suboptimal",
       "state": "Active",
       "severity": "CRITICAL",
       "update_timestamp": "2015-12-01T12:46:41Z",
       "resource_type": "nova.instance",
       "resource_name": "vm1",
       "resource_id": "275097cf-954e-8e24-b185-9514e24b8591",
       "id": 2,
       "vitrage_id": "ALARM:vitrage:vm1:Machine Suboptimal",
       "normalized_severity": "CRITICAL"
     },
     {
       "vitrage_category": "ALARM",
       "vitrage_type": "aodh",
       "name": "Memory overload",
       "state": "Active",
       "severity": "WARNING",
       "update_timestamp": "2015-12-01T12:46:41Z",
       "info": "WARNING - 15min load 1.66 at 32 CPUs",
       "resource_type": "nova.host",
       "resource_name": "host-0",
       "resource_id": "host-0",
       "id": 3,
       "vitrage_id": "ALARM:aodh:host0:Memory overload",
       "normalized_severity": "WARNING"
     }
 ]


Show alarm
^^^^^^^^^^
Show details of the specified alarm.

GET /v1/alarm/[vitrage_id]
~~~~~~~~~~~~~~~~~~~~~~~~~~

Headers
=======

-  X-Auth-Token (string, required) - Keystone auth token
-  Accept (string) - application/json
-  User-Agent (String)
-  Content-Type (String): application/json

Path Parameters
===============

- vitrage_id.

Query Parameters
================

None.

Request Body
============

None.

Request Examples
================

::

    GET /v1/alarm/7cfed44c-52cc-4097-931f-8fbec7410c5c
    Host: 127.0.0.1:8999
    User-Agent: keystoneauth1/2.3.0 python-requests/2.9.1 CPython/2.7.6
    Accept: application/json
    X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7

Response Status code
====================

-  200 - OK
-  404 - Bad request

Response Body
=============

Returns details of the requested alarm.

Response Examples
=================

::

    {
      "vitrage_id": "019912c4-89e0-4d39-9836-237364cf6967",
      "vitrage_is_deleted": false,
      "severity": "critical",
      "update_timestamp": "2018-01-03T07:52:06Z",
      "resource_id": "82ea32a3-528b-4836-bfdb-3f17acd2f640",
      "vitrage_category": "ALARM",
      "state": "Active",
      "vitrage_type": "vitrage",
      "vitrage_sample_timestamp": "2018-01-03 07:52:06.497732+00:00",
      "vitrage_operational_severity": "CRITICAL",
      "vitrage_is_placeholder": false,
      "vitrage_aggregated_severity": "CRITICAL",
      "vitrage_resource_id": "82ea32a3-528b-4836-bfdb-3f17acd2f640",
      "vitrage_resource_type": "nova.instance",
      "is_real_vitrage_id": true,
      "name": "deducy"
    }

Show Alarm Count
^^^^^^^^^^^^^^^^

Shows how many alarms of each operations severity exist

GET /v1/alarm/count
~~~~~~~~~~~~~~~~~~~

Headers
=======

-  X-Auth-Token (string, required) - Keystone auth token

Path Parameters
===============

None.

Query Parameters
================

None.

Request Body
============

* all_tenants - (boolean, optional) includes alarms of all tenants in the count (in case the user has the permissions).

Request Examples
================

::

    GET /v1/alarm/count/ HTTP/1.1
    Host: 135.248.19.18:8999
    X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7
    Accept: application/json

Response Status code
====================

-  200 - OK

Response Body
=============

Returns a JSON object with all the alarms requested.

Response Examples
=================

::

   {
     "severe": 2,
     "critical": 1,
     "warning": 3,
     "na": 4,
     "ok": 5
   }


Template Validate
^^^^^^^^^^^^^^^^^

An API for validating templates

POST /v1/template/
~~~~~~~~~~~~~~~~~~

Headers
=======

-  X-Auth-Token (string, required) - Keystone auth token
-  Accept (string) - application/json
-  User-Agent (String)
-  Content-Type (String): application/json

Path Parameters
===============

None.

Query Parameters
================

-  path (string(255), required) - the path to template file or directory

Request Body
============

None

Request Examples
================

::

    POST /v1/template/?path=[file/dir path]
    Host: 135.248.18.122:8999
    User-Agent: keystoneauth1/2.3.0 python-requests/2.9.1 CPython/2.7.6
    Content-Type: application/json
    Accept: application/json
    X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7

Response Status code
====================

None

Response Body
=============

Returns a JSON object that is a list of results.
Each result describes a full validation (syntax and content) of one template file.

Response Examples
=================

::

    {
      "results": [
        {
          "status": "validation failed",
          "file path": "/tmp/templates/basic_no_meta.yaml",
          "description": "Template syntax validation",
          "message": "metadata is a mandatory section.",
          "status code": 62
        },
        {
          "status": "validation OK",
          "file path": "/tmp/templates/basic.yaml",
          "description": "Template validation",
          "message": "Template validation is OK",
          "status code": 4
        }
      ]
    }

Template List
=============

List all templates in the database, both those that passed validation and those that did not.

GET /v1/template/
~~~~~~~~~~~~~~~~~

Headers
=======

-  X-Auth-Token (string, required) - Keystone auth token
-  Accept (string) - application/json
-  User-Agent (String)

Path Parameters
===============

None

Query Parameters
================

None

Request Body
============

None

Request Examples
================

::

    GET /v1/template/
    Host: 135.248.18.122:8999
    User-Agent: keystoneauth1/2.3.0 python-requests/2.9.1 CPython/2.7.6
    Accept: application/json
    X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7

Response Status code
====================

None

Response Body
=============

Returns list of all templates in the database with status ACTIVE or ERROR.

Response Examples
=================

::

  +--------------------------------------+-----------------------------------------+--------+---------------------------+---------------------+-------------+
  | UUID                                 | Name                                    | Status | Status details            | Date                | Type        |
  +--------------------------------------+-----------------------------------------+--------+---------------------------+---------------------+-------------+
  | ae3c0752-1df9-408c-89d5-8b32b86f403f | host_disk_io_overloaded_usage_scenarios | ACTIVE | Template validation is OK | 2018-01-23 10:14:05 | standard    |
  | f254edb0-53cb-4552-969b-bdad24a14a03 | ceph_health_is_not_ok_scenarios         | ACTIVE | Template validation is OK | 2018-01-23 10:20:29 | standard    |
  | bf405cfa-3f19-4761-9329-6e48f21cd466 | basic_def_template                      | ACTIVE | Template validation is OK | 2018-01-23 10:20:56 | definition  |
  | 7b5d6ca8-9ee0-4388-8c91-819b8786b78e | zabbix_host_equivalence                 | ACTIVE | No Validation             | 2018-01-23 10:21:13 | equivalence |
  +--------------------------------------+-----------------------------------------+--------+---------------------------+---------------------+-------------+

Template Show
^^^^^^^^^^^^^

Shows the template body for given template ID

GET /v1/template/[template_uuid]
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Headers
=======

-  User-Agent (string)
-  X-Auth-Token (string, required) - Keystone auth token
-  Accept (string) - application/json

Path Parameters
===============

- template uuid

Query Parameters
================

None

Request Body
============

None

Request Examples
================

::

    GET /v1/template/a0bdb89a-fe4c-4b27-adc2-507b7ec44c24
    Host: 135.248.19.18:8999
    User-Agent: keystoneauth1/2.3.0 python-requests/2.9.1 CPython/2.7.6
    X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7
    Accept: application/json



Response Status code
====================

-  200 - OK
-  404 - failed to show template with uuid: [template_uuid]

Response Body
=============

Returns a JSON object which represents the template body

Response Examples
=================

::

    {
      "scenarios": [
        {
          "scenario": {
            "actions": [
              {
                "action": {
                  "action_target": {
                    "target": "instance"
                  },
                  "properties": {
                    "alarm_name": "exploding_world",
                    "severity": "CRITICAL"
                  },
                  "action_type": "raise_alarm"
                }
              }
            ],
            "condition": "alarm_1_on_host and host_contains_instance"
          }
        },
        {
          "scenario": {
            "actions": [
              {
                "action": {
                  "action_target": {
                    "source": "alarm_1",
                    "target": "alarm_2"
                  },
                  "action_type": "add_causal_relationship"
                }
              }
            ],
            "condition": "alarm_1_on_host and alarm_2_on_instance and host_contains_instance"
          }
        }
      ],
      "definitions": {
        "relationships": [
          {
            "relationship": {
              "relationship_type": "on",
              "source": "alarm_1",
              "target": "host",
              "template_id": "alarm_1_on_host"
            }
          },
          {
            "relationship": {
              "relationship_type": "on",
              "source": "alarm_2",
              "target": "instance",
              "template_id": "alarm_2_on_instance"
            }
          },
          {
            "relationship": {
              "relationship_type": "contains",
              "source": "host",
              "target": "instance",
              "template_id": "host_contains_instance"
            }
          }
        ],
        "entities": [
          {
            "entity": {
              "vitrage_category": "ALARM",
              "vitrage_type": "nagios",
              "name": "check_libvirtd",
              "template_id": "alarm_1"
            }
          },
          {
            "entity": {
              "vitrage_category": "RESOURCE",
              "vitrage_type": "nova.host",
              "template_id": "host"
            }
          },
          {
            "entity": {
              "vitrage_category": "RESOURCE",
              "vitrage_type": "nova.instance",
              "template_id": "instance"
            }
          },
          {
            "entity": {
              "vitrage_category": "ALARM",
              "vitrage_type": "vitrage",
              "name": "exploding_world",
              "template_id": "alarm_2"
            }
          }
        ]
      },
      "metadata": {
        "name": "first_deduced_alarm_ever"
    }


PUT /v1/template/
~~~~~~~~~~~~~~~~~

Headers
=======

-  X-Auth-Token (string, required) - Keystone auth token
-  Accept (string) - application/json
-  User-Agent (String)

Path Parameters
===============

None

Query Parameters
================

-  path (string, required) - the path to template file or directory
-  type (string, optional) - template type (standard,definition,equivalence)

Request Body
============

None

Request Examples
================

::

    PUT /v1/template/
    Host: 135.248.18.122:8999
    User-Agent: keystoneauth1/2.3.0 python-requests/2.9.1 CPython/2.7.6
    Accept: application/json
    X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7

Response Status code
====================

None

Response Body
=============

Returns list of all added templates.
In case of duplicate templates returns info message.

Response Examples
=================

::


   +--------------------------------------+----------------------------------+---------+---------------------------+----------------------------+----------+
   | UUID                                 | Name                             | Status  | Status details            | Date                       | Type     |
   +--------------------------------------+----------------------------------+---------+---------------------------+----------------------------+----------+
   | d661a9b1-87b5-4b2e-933f-043b19a39d17 | host_high_memory_usage_scenarios | LOADING | Template validation is OK | 2018-01-23 18:55:54.472329 | standard |
   +--------------------------------------+----------------------------------+---------+---------------------------+----------------------------+----------+



DELETE /v1/template/
~~~~~~~~~~~~~~~~~~~~

Headers
=======

-  X-Auth-Token (string, required) - Keystone auth token
-  Accept (string) - application/json
-  User-Agent (String)

Path Parameters
===============

template uuid

Query Parameters
================

None

Request Body
============

None

Request Examples
================

::

    DELETE /v1/template/
    Host: 135.248.18.122:8999
    User-Agent: keystoneauth1/2.3.0 python-requests/2.9.1 CPython/2.7.6
    Accept: string
    X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7

Response Status code
====================

None

Response Body
=============

None

Response Examples
=================

None


Event Post
^^^^^^^^^^
Post an event to Vitrage message queue, to be consumed by a datasource driver.

POST /v1/event/
~~~~~~~~~~~~~~~

Headers
=======

-  X-Auth-Token (string, required) - Keystone auth token
-  Accept (string) - application/json
-  User-Agent (String)
-  Content-Type (String): application/json

Path Parameters
===============

None.

Query Parameters
================

None.

Request Body
============

An event to be posted. Will contain the following fields:

- time: a timestamp of the event. In case of a monitor event, should specify when the fault has occurred.
- type: the type of the event.
- details: a key-value map of metadata.

A dict of some potential details, copied from the Doctor SB API reference:

- hostname: the hostname on which the event occurred.
- source: the display name of reporter of this event. This is not limited to monitor, other entity can be specified such as 'KVM'.
- cause: description of the cause of this event which could be different from the type of this event.
- severity: the severity of this event set by the monitor.
- status: the status of target object in which error occurred.
- monitorID: the ID of the monitor sending this event.
- monitorEventID: the ID of the event in the monitor. This can be used by operator while tracking the monitor log.
- relatedTo: the array of IDs which related to this event.

Request Examples
================

::

    POST /v1/event/
    Host: 135.248.18.122:8999
    User-Agent: keystoneauth1/2.3.0 python-requests/2.9.1 CPython/2.7.6
    Content-Type: application/json
    Accept: application/json
    X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7


::

    {
        'event': {
            'time': '2016-04-12T08:00:00',
            'type': 'compute.host.down',
            'details': {
                'hostname': 'compute-1',
                'source': 'sample_monitor',
                'cause': 'link-down',
                'severity': 'critical',
                'status': 'down',
                'monitor_id': 'monitor-1',
                'monitor_event_id': '123',
            }
        }
    }



Response Status code
====================

-  200 - OK
-  400 - Bad request

Response Body
=============

Returns an empty response body if the request was OK.
Otherwise returns a detailed error message (e.g. 'missing time parameter').

Resource list
^^^^^^^^^^^^^
List the resources with specified type or all the resources.

GET /v1/resources/
~~~~~~~~~~~~~~~~~~

Headers
=======

-  X-Auth-Token (string, required) - Keystone auth token
-  Accept (string) - application/json
-  User-Agent (String)
-  Content-Type (String): application/json

Path Parameters
===============

None.

Query Parameters
================

* resource_type - (string, optional) the type of resource, defaults to return all resources.
* all_tenants - (boolean, optional) shows the resources of all tenants (in case the user has the permissions).

Request Body
============

None.

Request Examples
================

::

    GET /v1/resources/?all_tenants=False&resource_type=nova.host
    Host: 135.248.18.122:8999
    User-Agent: keystoneauth1/2.3.0 python-requests/2.9.1 CPython/2.7.6
    Content-Type: application/json
    Accept: application/json
    X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7


Response Status code
====================

-  200 - OK
-  404 - Bad request

Response Body
=============

Returns a list with all the resources requested.

Response Examples
=================

::

  [
    {
      "vitrage_id": "RESOURCE:nova.host:cloud",
      "vitrage_aggregated_state": "AVAILABLE",
      "state": "available",
      "vitrage_type": "nova.host",
      "id": "cloud",
      "metadata": {
        "name": "cloud",
        "update_timestamp": "2017-04-24 04:27:47.501777+00:00"
      }
    }
  ]


Resource show
^^^^^^^^^^^^^
Show the details of specified resource.

GET /v1/resources/[vitrage_id]
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Headers
=======

-  X-Auth-Token (string, required) - Keystone auth token
-  Accept (string) - application/json
-  User-Agent (String)
-  Content-Type (String): application/json

Path Parameters
===============

- vitrage_id.

Query Parameters
================

None.

Request Body
============

None.

Request Examples
================

::

    GET /v1/resources/`<vitrage_id>`
    Host: 127.0.0.1:8999
    User-Agent: keystoneauth1/2.3.0 python-requests/2.9.1 CPython/2.7.6
    Accept: application/json
    X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7

Response Status code
====================

-  200 - OK
-  404 - Bad request

Response Body
=============

Returns details of the requested resource.

Response Examples
=================

::

    {
      "vitrage_category": "RESOURCE",
      "vitrage_is_placeholder": false,
      "vitrage_is_deleted": false,
      "name": "vm-1",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "vitrage_type": "nova.instance",
      "id": "dc35fa2f-4515-1653-ef6b-03b471bb395b",
      "vitrage_id": "RESOURCE:nova.instance:dc35fa2f-4515-1653-ef6b-03b471bb395b"
    }

Webhook List
^^^^^^^^^^^^
List all webhooks.

GET /v1/webhook/
~~~~~~~~~~~~~~~~

Headers
=======

-  X-Auth-Token (string, required) - Keystone auth token
-  Accept (string) - application/json
-  User-Agent (String)
-  Content-Type (String): application/json

Path Parameters
===============

None.

Query Parameters
================

None.

Request Body
============

None.

Request Examples
================

::

    GET /v1/webhook
    Host: 135.248.18.122:8999
    User-Agent: keystoneauth1/2.3.0 python-requests/2.9.1 CPython/2.7.6
    Content-Type: application/json
    Accept: application/json
    X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7


Response Status code
====================

-  200 - OK
-  404 - Bad request

Response Body
=============

Returns a list with all webhooks.

Response Examples
=================

::

  [
   {
      "url":"https://requestb.in/tq3fkvtq",
      "headers":"{'content-type': 'application/json'}",
      "regex_filter":"{'name':'e2e.*'}",
      "created_at":"2018-01-04T12:27:47.000000",
      "id":"c35caf11-f34d-440e-a804-0c1a4fdfb95b"
   }
  ]

Webhook Show
^^^^^^^^^^^^
Show the details of specified webhook.

GET /v1/webhook/[id]
~~~~~~~~~~~~~~~~~~~~

Headers
=======

-  X-Auth-Token (string, required) - Keystone auth token
-  Accept (string) - application/json
-  User-Agent (String)
-  Content-Type (String): application/json

Path Parameters
===============

- id.

Query Parameters
================

None.

Request Body
============

None.

Request Examples
================

::

    GET /v1/resources/`<id>`
    Host: 127.0.0.1:8999
    User-Agent: keystoneauth1/2.3.0 python-requests/2.9.1 CPython/2.7.6
    Accept: application/json
    X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7

Response Status code
====================

-  200 - OK
-  404 - Bad request

Response Body
=============

Returns details of the requested webhook.

Response Examples
=================

::

   {
      "url":"https://requestb.in/tq3fkvtq",
      "created_at":"2018-01-04T12:27:47.000000",
      "updated_at":null,
      "id":"c35caf11-f34d-440e-a804-0c1a4fdfb95b",
      "headers":"{'content-type': 'application/json'}",
      "regex_filter":"{'name':'e2e.*'}"
   }

Webhook Add
^^^^^^^^^^^
Add a webhook to the database, to be used by the notifier.

POST /v1/webhook/
~~~~~~~~~~~~~~~~~

Headers
=======

-  X-Auth-Token (string, required) - Keystone auth token
-  Accept (string) - application/json
-  User-Agent (String)
-  Content-Type (String): application/json

Path Parameters
===============

None.

Query Parameters
================

None.

Request Body
============

A webhook to be added. Will contain the following fields:

+------------------+-----------------------------------------------------------------+--------------+
| Name             | Description                                                     | Required     |
+==================+=================================================================+==============+
| url              | The webhook URL to which notifications will be sent             | Yes          |
+------------------+-----------------------------------------------------------------+--------------+
| regex_filter     | A JSON string to filter for specific events                     | No           |
+------------------+-----------------------------------------------------------------+--------------+
| headers          | A JSON string specifying additional headers to the notification | No           |
+------------------+-----------------------------------------------------------------+--------------+

- If no regex filter is supplied, all notifications will be sent.
- The defaults headers are : '{'content-type': 'application/json'}'

Request Examples
================

::

    POST /v1/webhook/
    Host: 135.248.18.122:8999
    User-Agent: keystoneauth1/2.3.0 python-requests/2.9.1 CPython/2.7.6
    Content-Type: application/json
    Accept: application/json
    X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7


::

   {
      "webhook":{
         "url":"https://requestb.in/tqfkvtqa",
         "headers":null,
         "regex_filter":"{'name':'e2e.*'}"
      }
   }


Response Status code
====================

-  200 - OK
-  400 - Bad request

Response Body
=============

Returns webhook details if request was OK,
otherwise returns a detailed error message (e.g. 'headers in bad format').

Webhook Delete
^^^^^^^^^^^^^^
Delete a specified webhook.

DELETE /v1/webhook/[id]
~~~~~~~~~~~~~~~~~~~~~~~

Headers
=======

-  X-Auth-Token (string, required) - Keystone auth token
-  Accept (string) - application/json
-  User-Agent (String)
-  Content-Type (String): application/json

Path Parameters
===============

- id.

Query Parameters
================

None.

Request Body
============

None.

Request Examples
================

::

    DELETE /v1/resources/`<id>`
    Host: 127.0.0.1:8999
    User-Agent: keystoneauth1/2.3.0 python-requests/2.9.1 CPython/2.7.6
    Accept: application/json
    X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7

Response Status code
====================

-  200 - OK
-  404 - Bad request

Response Body
=============

Returns a success message if the webhook is deleted, otherwise an error
message is returned.