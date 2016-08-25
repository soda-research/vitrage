============================
Enabling Vitrage in DevStack
============================

1. Download DevStack:

    git clone https://git.openstack.org/openstack-dev/devstack.git
    cd devstack

2. Add this repo as an external repository in ``local.conf`` file:

    [[local|localrc]]
    enable_plugin vitrage https://git.openstack.org/openstack/vitrage

3. Add this to add notification from nova to vitrage

::

   [[post-config|$NOVA_CONF]]
   [DEFAULT]
   notification_topics = notifications,vitrage_notifications
   notification_driver=messagingv2

4. Add this to add notification from neutron to vitrage
   (make sure neutron is enabled in devstack)

::

   [[post-config|$NEUTRON_CONF]]
   [DEFAULT]
   notification_topics = notifications,vitrage_notifications
   notification_driver=messagingv2

5. Add this to add notification from cinder to vitrage

::

   [[post-config|$CINDER_CONF]]
   [DEFAULT]
   notification_topics = notifications,vitrage_notifications
   notification_driver=messagingv2

6. Add this to add notification from heat to vitrage

::

   [[post-config|$HEAT_CONF]]
   [DEFAULT]
   notification_topics = notifications,vitrage_notifications
   notification_driver=messagingv2

7. Run ``stack.sh``.
