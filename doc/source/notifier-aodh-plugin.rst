===============================
Vitrage Notifier plugins - AODH
===============================

Overview
========
The Evaluator performs root cause analysis on the Vitrage Graph and may determine that an alarm should be created, deleted or otherwise updated.
Other components are notified of such changes by the Vitrage Notifier service. Among others, Vitrage Notifier is responsible for handling Aodh Alarms.

This document describes the implementation of Vitrage Notifier infrastructure and specifically notifying Aodh on Vitrage alarms.

Design
======

::

  +------------------+          +--------+
  |      Vitrage     |          | Message|       +------------------+
  |    Evaluator     ---------->|  Bus   --------> Vitrage Notifier |
  +------------------+          |        |       +------------------+
                                |        |          |        |   |
                                |        |      +---|------+ |   |
                                |        |      | Aodh     |-|-+ |
                                |        |      | notifier |   |-|--+
                                |        |   +--| plugin   |   |    |
                                |        |   |  +----------+   |    |
                                +--------+   |     +-----------+    |
                                             |         +------------+
  +------------------+                       |
  |   Aodh           <-----------------------+
  +------------------+

...

Evaluator bus notifications
---------------------------
Vitrage Evaluator will use the **vitrage.evaluator** message bus topic, and will post messages as follows:

 - message of type **vitrage.deduce_alarm.activate** :

   * name - is the alarm name in vitrage
   * severity - is the alarm severity
   * affected_resource_id - is the openstack id of the resource on which the alarm was raised

 - **vitrage.deduce_alarm.deactivate**

   * id - is the alarm id

Notifier
========
 - Is a new running service
 - Receives notifications from the message bus
 - Holds instances of all the plugins
 - Upon a received notification, calls 'notify(msg)' for all the plugins
 - Each plugin is responsible of how and whether to process the notification

Aodh Plugin
===========
Vitrage alarms should be reflected as possible in Aodh. the aodh plugin has ceilometer client by which it can send rest calls to aodh

Handle vitrage.deduce_alarm.activate:
-------------------------------------
Create an event alarm with the specified severity, where the alarm name is vitrage_alarm_name+resource_id so to be unique

Handle vitrage.deduce_alarm.deactivate:
---------------------------------------
delete an event alarm with the specified id
