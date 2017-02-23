Prerequisites
-------------

Before you install and configure the Root Cause Analyzis service,
you must create a database, service credentials, and API endpoints.

#. To create the database, complete these steps:

   * Use the database access client to connect to the database
     server as the ``root`` user:

     .. code-block:: console

        $ mysql -u root -p

   * Create the ``vitrage`` database:

     .. code-block:: mysql

        CREATE DATABASE vitrage;

   * Grant proper access to the ``vitrage`` database:

     .. code-block:: mysql

        GRANT ALL PRIVILEGES ON vitrage.* TO 'vitrage'@'localhost' \
          IDENTIFIED BY 'VITRAGE_DBPASS';
        GRANT ALL PRIVILEGES ON vitrage.* TO 'vitrage'@'%' \
          IDENTIFIED BY 'VITRAGE_DBPASS';

     Replace ``VITRAGE_DBPASS`` with a suitable password.

   * Exit the database access client.

     .. code-block:: mysql

        exit;

#. Source the ``admin`` credentials to gain access to
   admin-only CLI commands:

   .. code-block:: console

      $ . admin-openrc

#. To create the service credentials, complete these steps:

   * Create the ``vitrage`` user:

     .. code-block:: console

        $ openstack user create --domain default --password-prompt vitrage

   * Add the ``admin`` role to the ``vitrage`` user:

     .. code-block:: console

        $ openstack role add --project service --user vitrage admin

   * Create the vitrage service entities:

     .. code-block:: console

        $ openstack service create --name vitrage --description "Root Cause Analyzis" root cause analyzis

#. Create the Root Cause Analyzis service API endpoints:

   .. code-block:: console

      $ openstack endpoint create --region RegionOne \
        root cause analyzis public http://controller:XXXX/vY/%\(tenant_id\)s
      $ openstack endpoint create --region RegionOne \
        root cause analyzis internal http://controller:XXXX/vY/%\(tenant_id\)s
      $ openstack endpoint create --region RegionOne \
        root cause analyzis admin http://controller:XXXX/vY/%\(tenant_id\)s
