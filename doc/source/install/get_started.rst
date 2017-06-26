====================================
Root Cause Analysis service overview
====================================

Vitrage provides a root cause analysis service, which is used for analyzing the topology and alarms of the cloud, and providing insights about it.

The Root Cause Analysis service consists of the following components:

``vitrage-graph`` service
  The main process. It holds the in-memory entity graph, the template evaluator, and the different datasources.
``vitrage-notifier`` service
  Used for notifying external systems about Vitrage alarms/state changes. It only calls Nova force-down API
  and Simple Network Management Protocol (SNMP) in the Ocata release.
``vitrage-api`` service
  The API layer for Vitrage.
