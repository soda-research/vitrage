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

**The Vitrage API provides a RESTful JSON interface for interacting with Vitrage Engine.**

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

query expression
================
::

 query := expression
 expression := simple_expression|complex_expression
 simple_expression := {simple_operator: {field_name: value}}
 simple_operator := = | != | < | <= | > | >=
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
      "query" :
       {
          "or":
          [
              "=":
                  {
                    "type":"host"
                  },
              "=":
                  {
                    "type":"instance"
                  },
              "=":
                  {
                    "type":"zone"
                  },
              "=":
                  {
                    "type":"node"
                  }
          ]
       }
       "graph_type" : "tree"
       limit : 4
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
      "category": "RESOURCE",
      "is_placeholder": false,
      "is_deleted": false,
      "name": "vm-8",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "type": "nova.instance",
      "id": "20d12a8a-ea9a-89c6-5947-83bea959362e",
      "vitrage_id": "RESOURCE:nova.instance:20d12a8a-ea9a-89c6-5947-83bea959362e"
    },
    {
      "category": "RESOURCE",
      "is_placeholder": false,
      "is_deleted": false,
      "name": "vm-2",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "type": "nova.instance",
      "id": "dc35fa2f-4515-1653-ef6b-03b471bb395b",
      "vitrage_id": "RESOURCE:nova.instance:dc35fa2f-4515-1653-ef6b-03b471bb395b"
    },
    {
      "category": "RESOURCE",
      "is_placeholder": false,
      "is_deleted": false,
      "name": "vm-13",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "type": "nova.instance",
      "id": "9879cf5a-bdcf-3651-3017-961ed887ec86",
      "vitrage_id": "RESOURCE:nova.instance:9879cf5a-bdcf-3651-3017-961ed887ec86"
    },
    {
      "category": "RESOURCE",
      "is_placeholder": false,
      "is_deleted": false,
      "name": "vm-10",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "type": "nova.instance",
      "id": "fe124f4b-9ed7-4591-fcd1-803cf5c33cb1",
      "vitrage_id": "RESOURCE:nova.instance:fe124f4b-9ed7-4591-fcd1-803cf5c33cb1"
    },
    {
      "category": "RESOURCE",
      "is_placeholder": false,
      "is_deleted": false,
      "name": "vm-11",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "type": "nova.instance",
      "id": "f2e48a97-7350-061e-12d3-84c6dc3e67c0",
      "vitrage_id": "RESOURCE:nova.instance:f2e48a97-7350-061e-12d3-84c6dc3e67c0"
    },
    {
      "category": "RESOURCE",
      "is_placeholder": false,
      "is_deleted": false,
      "name": "host-2",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "available",
      "type": "nova.host",
      "id": "host-2",
      "vitrage_id": "RESOURCE:nova.host:host-2"
    },
    {
      "category": "RESOURCE",
      "is_placeholder": false,
      "is_deleted": false,
      "name": "host-3",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "available",
      "type": "nova.host",
      "id": "host-3",
      "vitrage_id": "RESOURCE:nova.host:host-3"
    },
    {
      "category": "RESOURCE",
      "is_placeholder": false,
      "is_deleted": false,
      "name": "host-0",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "available",
      "type": "nova.host",
      "id": "host-0",
      "vitrage_id": "RESOURCE:nova.host:host-0"
    },
    {
      "category": "RESOURCE",
      "is_placeholder": false,
      "is_deleted": false,
      "name": "host-1",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "available",
      "type": "nova.host",
      "id": "host-1",
      "vitrage_id": "RESOURCE:nova.host:host-1"
    },
    {
      "category": "RESOURCE",
      "is_placeholder": false,
      "is_deleted": false,
      "name": "vm-9",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "type": "nova.instance",
      "id": "275097cf-954e-8e24-b185-9514e24b8591",
      "vitrage_id": "RESOURCE:nova.instance:275097cf-954e-8e24-b185-9514e24b8591"
    },
    {
      "category": "RESOURCE",
      "is_placeholder": false,
      "is_deleted": false,
      "name": "vm-1",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "type": "nova.instance",
      "id": "a0f0805f-c804-cffe-c25a-1b38f555ed68",
      "vitrage_id": "RESOURCE:nova.instance:a0f0805f-c804-cffe-c25a-1b38f555ed68"
    },
    {
      "category": "RESOURCE",
      "is_placeholder": false,
      "is_deleted": false,
      "name": "vm-14",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "type": "nova.instance",
      "id": "56af57d2-34a4-19b1-5106-b613637a11a7",
      "vitrage_id": "RESOURCE:nova.instance:56af57d2-34a4-19b1-5106-b613637a11a7"
    },
    {
      "category": "RESOURCE",
      "is_placeholder": false,
      "is_deleted": false,
      "name": "zone-1",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "available",
      "type": "nova.zone",
      "id": "zone-1",
      "vitrage_id": "RESOURCE:nova.zone:zone-1"
    },
    {
      "category": "RESOURCE",
      "is_placeholder": false,
      "is_deleted": false,
      "name": "vm-3",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "type": "nova.instance",
      "id": "16e14c58-d254-2bec-53e4-c766e48810aa",
      "vitrage_id": "RESOURCE:nova.instance:16e14c58-d254-2bec-53e4-c766e48810aa"
    },
    {
      "category": "RESOURCE",
      "is_placeholder": false,
      "is_deleted": false,
      "name": "vm-7",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "type": "nova.instance",
      "id": "f35a1e10-74ff-7332-8edf-83cd6ffcb2de",
      "vitrage_id": "RESOURCE:nova.instance:f35a1e10-74ff-7332-8edf-83cd6ffcb2de"
    },
    {
      "category": "RESOURCE",
      "is_placeholder": false,
      "is_deleted": false,
      "name": "vm-4",
      "update_timestamp": "2015-12-01T12:46:41Z?vitrage_id=all",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "type": "nova.instance",
      "id": "ea8a450e-cab1-2272-f431-494b40c5c378",
      "vitrage_id": "RESOURCE:nova.instance:ea8a450e-cab1-2272-f431-494b40c5c378"
    },
    {
      "category": "RESOURCE",
      "is_placeholder": false,
      "is_deleted": false,
      "name": "vm-6",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "type": "nova.instance",
      "id": "6e42bdc3-b776-1b2c-2c7d-b7a8bb98f721",
      "vitrage_id": "RESOURCE:nova.instance:6e42bdc3-b776-1b2c-2c7d-b7a8bb98f721"
    },
    {
      "category": "RESOURCE",
      "is_placeholder": false,
      "is_deleted": false,
      "name": "vm-5",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "type": "nova.instance",
      "id": "8c951613-c660-87c0-c18b-0fa3293ce8d8",
      "vitrage_id": "RESOURCE:nova.instance:8c951613-c660-87c0-c18b-0fa3293ce8d8"
    },
    {
      "category": "RESOURCE",
      "is_placeholder": false,
      "is_deleted": false,
      "name": "zone-0",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "available",
      "type": "nova.zone",
      "id": "zone-0",
      "vitrage_id": "RESOURCE:nova.zone:zone-0"
    },
    {
      "category": "RESOURCE",
      "is_placeholder": false,
      "is_deleted": false,
      "name": "vm-0",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "type": "nova.instance",
      "id": "78353ce4-2710-49b5-1341-b8cbb6000ebc",
      "vitrage_id": "RESOURCE:nova.instance:78353ce4-2710-49b5-1341-b8cbb6000ebc"
    },TODO
    {
      "category": "RESOURCE",
      "is_placeholder": false,
      "is_deleted": false,
      "name": "vm-12",
      "update_timestamp": "2015-12-01T12:46:41Z",
      "state": "ACTIVE",
      "project_id": "0683517e1e354d2ba25cba6937f44e79",
      "type": "nova.instance",
      "id": "35bf479a-75d9-80a9-874e-d3b50fb2dd2e",
      "vitrage_id": "RESOURCE:nova.instance:35bf479a-75d9-80a9-874e-d3b50fb2dd2e"
    },
    {
      "category": "RESOURCE",
      "is_placeholder": false,
      "is_deleted": false,
      "name": "openstack.cluster",
      "type": "openstack.cluster",
      "id": "openstack.cluster",
      "vitrage_id": "RESOURCE:openstack.cluster"
    }
  ],
  "links": [
    {
      "relationship_name": "contains",
      "is_deleted": false,
      "target": 3,
      "key": "contains",
      "source": 5
    },
    {
      "relationship_name": "contains",
      "is_deleted": false,
      "target": 1,
      "key": "contains",
      "source": 5
    },
    {
      "relationship_name": "contains",
      "is_deleted": false,
      "target": 16,
      "key": "contains",
      "source": 5
    },
    {
      "relationship_name": "contains",
      "is_deleted": false,
      "target": 11,
      "key": "contains",
      "source": 5
    },
    {
      "relationship_name": "contains",
      "is_deleted": false,
      "target": 13,
      "key": "contains",
      "source": 6
    },
    {
      "relationship_name": "contains",
      "is_deleted": false,
      "target": 4,
      "key": "contains",
      "source": 6
    },
    {
      "relationship_name": "contains",
      "is_deleted": false,
      "target": 14,
      "key": "contains",
      "source": 6
    },
    {
      "relationship_name": "contains",
      "is_deleted": false,
      "target": 20,
      "key": "contains",
      "source": 7
    },?vitrage_id=all
    {
      "relationship_name": "contains",
      "is_deleted": false,
      "target": 0,
      "key": "contains",
      "source": 7
    },
    {
      "relationship_name": "contains",
      "is_deleted": false,
      "target": 19,
      "key": "contains",
      "source": 7
    },
    {
      "relationship_name": "contains",
      "is_deleted": false,
      "target": 15,
      "key": "contains",
      "source": 7
    },
    {
      "relationship_name": "contains",
      "is_deleted": false,
      "target": 9,
      "key": "contains",
      "source": 8
    },
    {
      "relationship_name": "contains",
      "is_deleted": false,
      "target": 10,
      "key": "contains",
      "source": 8
    },
    {
      "relationship_name": "contains",
      "is_deleted": false,
      "target": 2,
      "key": "contains",
      "source": 8
    },
    {
      "relationship_name": "contains",
      "is_deleted": false,
      "target": 17,
      "key": "contains",
      "source": 8
    },
    {
      "relationship_name": "contains",
      "is_deleted": false,
      "target": 6,
      "key": "contains",
      "source": 12
    },
    {
      "relationship_name": "contains",
      "is_deleted": false,
      "target": 8,
      "key": "contains",
      "source": 12
    },
    {
      "relationship_name": "contains",
      "is_deleted": false,
      "target": 5,
      "key": "contains",
      "source": 18
    },
    {
      "relationship_name": "contains",
      "is_deleted": false,
      "target": 7,
      "key": "contains",
      "source": 18
    },
    {
      "relationship_name": "contains",
      "is_deleted": false,
      "target": 18,
      "key": "contains",
      "source": 21
    },
    {
      "relationship_name": "contains",
      "is_deleted": false,
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

None.

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
      "category": "ALARM",
      "type": "nagios",
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
      "category": "ALARM",
      "type": "vitrage",
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
      "category": "ALARM",
      "type": "vitrage",
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

GET /v1/alarms/
~~~~~~~~~~~~~~~

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

None.

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
       "category": "ALARM",
       "type": "nagios",
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
       "category": "ALARM",
       "type": "vitrage",
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
       "category": "ALARM",
       "type": "vitrage",
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
       "category": "ALARM",
       "type": "aodh",
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