# Copyright 2016 - Nokia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import functools


class Notifier(object):
    def __init__(self):
        self._subscriptions = []

    def subscribe(self, function):
        self._subscriptions.append(function)

    def is_subscribed(self):
        return len(self._subscriptions) != 0

    def do_notify(self, prev_item, current_item):
        for func in self._subscriptions:
            func(prev_item, current_item)

    @staticmethod
    def notify(graph, curr_item, prev_item=None):
        if not graph.is_subscribed():
            return
        curr_item = graph.get_item(curr_item)
        graph.notifier.do_notify(prev_item, curr_item)

    @staticmethod
    def update_notify(func):
        @functools.wraps(func)
        def notified_func(graph, item, *args, **kwargs):
            prev_item = graph.get_item(item) if graph.is_subscribed() else None
            func(graph, item, *args, **kwargs)
            Notifier.notify(graph, item, prev_item)
        return notified_func

    @staticmethod
    def add_notify(func):
        @functools.wraps(func)
        def notified_func(graph, item, *args, **kwargs):
            func(graph, item, *args, **kwargs)
            Notifier.notify(graph, item)
        return notified_func
