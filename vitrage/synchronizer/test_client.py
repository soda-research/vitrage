# Copyright 2015 - Alcatel-Lucent
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import multiprocessing


from synchronizer import Synchronizer


class TestClient(object):
    def queue_callback_function(self, output):
        for entity in output:
            self.queue.put(entity)

    def print_queue(self):
        while True:
            entity = self.queue.get()
            print(entity)

    def __init__(self):
        self.queue = multiprocessing.Queue()
        self.synchronizer = Synchronizer(self.queue)
        self.worker = multiprocessing.Process(target=self.print_queue)

    def get_all(self):
        self.synchronizer.get_all()


if __name__ == '__main__':
    client = TestClient()
    client.get_all()
    client.worker.start()
    client.worker.join()
