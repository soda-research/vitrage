====================================
Static Physical Plugin Configuration
====================================

Configure Access to Static Physical
-----------------------------------

The following should be set in **/etc/vitrage/vitrage.conf**, under synchronizer_plugins section:

+----------------------+------------------------------------+--------------------------------+
| Name                 | Description                        | Default Value                  |
+======================+====================================+================================+
| static_plugins_dir   | Directory path from where to load  | /etc/vitrage/static_plugins/   |
|                      | the configurations                 |                                |
+----------------------+------------------------------------+--------------------------------+


Configure Static Physical Mapping
---------------------------------

Physical configuration is made for configuring statically physical entities, and their relationships to other entities in the topology.

Some physical entities, such as switches, can not be retrieved from OpenStack, so for now we will configure them statically.

There may be more than one configuration file. All files will be read from /etc/vitrage/static_plugins/.

**Format**
::


 entities:
  - name: <Physical entity name as appears in configuration>
    id: <Physical entity id as appears in configuration>
    type: <Physical entity type - must be from constants.EntityType>
    state: <resource state>
    relationships:
      - type: <Physical entity type it is connected to - must be from constants.EntityType>
        name: <Physical entity name connected to as appears in configuration>
        id: <Physical entity id connected to as appears in configuration>
        relation_type: <Relation name>
      - type: <Physical entity type it is connected to - must be from constants.EntityType>
        name: <Physical entity name connected to as appears in configuration>
        id: <Physical entity id connected to as appears in configuration>
        relation_type: <Relation name>

  ...


**Example**

The following will define a switch that is attached to host-1 and is a backup of switch-2

::

 entities:
  - type: switch
    name: switch-1
    id: 11111
    state: available
    relationships:
      - type: nova.host
        name: host-1
        id: 22222
        relation_type: attached
      - type: switch
        name: switch-2
        id: 33333
        relation_type: backup

