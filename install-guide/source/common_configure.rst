2. Edit the ``/etc/vitrage/vitrage.conf`` file and complete the following
   actions:

   * In the ``[database]`` section, configure database access:

     .. code-block:: ini

        [database]
        ...
        connection = mysql+pymysql://vitrage:VITRAGE_DBPASS@controller/vitrage
