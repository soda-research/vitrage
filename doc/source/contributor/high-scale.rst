================================
Configure Vitrage for high-scale
================================
In a production environment with > 50,000 entities, the following configuration changes are suggested:


Tune RPC
--------

Vitrage-graph uses RPC to request data from vitrage-collector, these requests take longer, and there is a need to increase the timeout.
The following should be set in ``/etc/vitrage/vitrage.conf``, under ``[DEFAULT]`` section:

+----------------------+---------------------------------------------------------+-----------------+-----------------+
| Name                 | Description                                             | Default Value   | Suggested Value |
+======================+=========================================================+=================+=================+
| rpc_response_timeout | Seconds to wait for a response from a call              |  60             |  300            |
+----------------------+---------------------------------------------------------+-----------------+-----------------+

To apply, restart these:

``sudo service vitrage-graph restart``

``sudo service vitrage-collector restart``

Restart the Vitrage api (either vitrage-api or apache)


Tune Memory
-----------

Most of the data is held in-memory. To conserve memory usage, the number of evaluator workers should be decreased.
If using many Vitrage templates the number of evaluator workers can be increased, but kept to a minimum needed.

The following should be set in ``/etc/vitrage/vitrage.conf``, under ``[evaluator]`` section:

+----------------------+---------------------------------------------------------+-----------------+-----------------+
| Name                 | Description                                             | Default Value   | Suggested Value |
+======================+=========================================================+=================+=================+
| workers              | Number of workers for template evaluator                | number of cores |  1              |
+----------------------+---------------------------------------------------------+-----------------+-----------------+

To apply, run ``sudo service vitrage-graph restart``


Tune Mysql
----------
Vitrage periodically persists the graph to mysql, as a mysql blob. As the graph size increases, it is recommended  to increase the mysql max_allowed_packet.

The following should be set in ``/etc/mysql/my.cnf``, under ``[mysqld]`` section:

+----------------------+---------------------------------------------------------+-----------------+-----------------+
| Name                 | Description                                             | Default Value   | Suggested Value |
+======================+=========================================================+=================+=================+
| max_allowed_packet   |  The maximum size of one packet or any string           | 4M-64M          |  100M           |
+----------------------+---------------------------------------------------------+-----------------+-----------------+

To apply, run ``sudo service mysql restart``
