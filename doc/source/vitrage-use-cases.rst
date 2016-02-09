=================
Vitrage Use Cases
=================

Add Nova Instance
-----------------
.. image:: ./images/add_nova_instance_flow.png
   :width: 100%
   :align: center


#. Nova Synchronizer plugin queries all Nova instances, or gets a message bus notification about a new Nova instance
#. Nova Synchronizer plugin sends corresponding events to the Entity Queue
#. The Entity Processor polls the Entity Queue and gets the new Nova Instance event
#. The Entity Processor passes the event to the Nova Instance Transformer plugin, which returns a Vertex with the instance data, and an edge to the host Vertex in the graph
#. The Entity Processor adds the new vertex and edge to the Graph

.. image:: ./images/add_nova_instance_graph.png
   :width: 100%
   :align: center


Add Aodh Alarm
--------------
.. image:: ./images/add_aodh_alarm_flow.png
   :width: 100%
   :align: center


#. Aodh Synchronizer plugin queries all Aodh alarms, or gets a notification (TBD) about an Aodh alarm state change
#. Aodh Synchronizer plugin sends corresponding events to the Entity Queue
#. The Entity Processor polls the Entity Queue and gets the Aodh Alarm event, for example threshold alarm on Instance1 CPU
#. The Entity Processor passes the event to the Aodh Alarm Transformer plugin, which returns a Vertex with the alarm data, and an edge to the instance Vertex
#. The Entity Processor adds the new vertex and edge to the Graph

.. image:: ./images/add_aodh_alarm_graph.png
   :width: 100%
   :align: center


Nagios Alarm Causes Deduced Alarm
---------------------------------
.. image:: ./images/nagios_causes_deduced_flow.png
   :width: 100%
   :align: center


5.  (steps 1-5) Nagios Synchronizer plugin pushes a nagios alarm on a switch to the Entity Queue, which is converted by Nagios Transformer to a vertex and inserted to the Graph
6. The Evaluator is notified about a new Vertex (Nagios switch alarm) that was added to the graph
7. The Evaluator performs its calculations (TBD) and deduces that alarms should be triggered on every instance on every host attached to this switch
8. The Evaluator pushes alarms to the Entity Queue
9. The Evaluator asks the notifier to notify on these new alarms
10. Aodh Notifier creates new alarm definitions in Aodh, and sets their states to "alarm"

.. image:: ./images/nagios_causes_deduced_graph.png
   :width: 100%
   :align: center


Create RCA Insights
-------------------
.. image:: ./images/rca_flow.png
   :width: 100%
   :align: center


#. The Evaluator is notified of a new alarm.
#. The Evaluator evaluates the templates and the Graph (TBD), and decides that there is a root cause relation between two alarms. It adds a "causes" edge to the Graph

.. image:: ./images/rca_graph.png
   :width: 100%
   :align: center


Note that in future versions the graph with RCA information may become more complex, for example:

.. image:: ./images/complex_rca_graph.png
   :width: 100%
   :align: center


