#!/usr/bin/python
#
# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Main API for Authbox.

This is the core items like BaseDispatcher (which you should subclass); for
peripherals see other files.
"""

import Queue
import sys
import threading
import traceback
# TODO give each object a logger and use that instead of print statements.

# This simplifies imports for other modules that are already importing from api.
try:
  from RPi import GPIO
  # TODO check version and output error
except ImportError:
  import warnings
  warnings.warn('Using FakeRPi suitable for testing only!')
  from FakeRPi import GPIO

CLASS_REGISTRY = [
    'authbox.badgereader_hid_keystroking.HIDKeystrokingReader',
    'authbox.gpio_button.Button',
    'authbox.gpio_relay.Relay',
    'authbox.gpio_buzzer.Buzzer',
    'authbox.timer.Timer',
]

# Add this to event_queue to request a graceful shutdown.
SHUTDOWN_SENTINEL = object()


class BaseDispatcher(object):
  def __init__(self, config):
    self.config = config
    self.event_queue = Queue.Queue()  # unbounded
    self.threads = []

  def load_config_object(self, name, **kwargs):
    # N.b. args are from config, kwargs are passed from python.
    # This sometimes causes confusing error messages like
    # "takes at least 5 arguments (5 given)".
    options = self.config.get('pins', name).split(':')
    cls_name = options[0]
    for c in CLASS_REGISTRY:
      if c.endswith('.' + cls_name):
        cls = _import(c)
        break
    else:
      # This is a Python for-else, which executes if the body above didn't
      # execute 'break'.
      raise Exception('Unknown item', name)
    print "Instantiating", cls, self.event_queue, name, options[1:], kwargs
    obj = cls(self.event_queue, name, *options[1:], **kwargs)
    setattr(self, name, obj)
    self.threads.append(obj)

  def run_loop(self):
    # Doesn't really support calling run_loop() more than once
    for th in self.threads:
      th.start()
    try:
      while True:
        # We pass a small timeout because .get(block=True) without it causes
        # trouble handling Ctrl-C.
        try:
          item = self.event_queue.get(timeout=1.0)
        except Queue.Empty:
          continue
        if item is SHUTDOWN_SENTINEL:
          break
        # These only happen here to serialize access regardless of what thread
        # handled it.
        func, args = item[0], item[1:]
        try:
          func(*args)
        except Exception as e:
          print "Got exception", repr(e), "executing", func, args
    except KeyboardInterrupt:
      print "Got Ctrl-C, shutting down."

    # Assuming all threads are daemonized, we will now shut down.


class BaseDerivedThread(threading.Thread):
  def __init__(self, event_queue, config_name):
    # TODO should they also have numeric ids?
    thread_name = "%s %s" % (self.__class__.__name__, config_name)
    super(BaseDerivedThread, self).__init__(name=thread_name)
    self.daemon = True

    self.event_queue = event_queue
    self.config_name = config_name

  def run(self):
    while True:
      try:
        self.run_inner()
      except Exception as e:
        traceback.print_exc()


class BasePinThread(BaseDerivedThread):
  def __init__(self, event_queue, config_name, input_pin, output_pin):
    super(BasePinThread, self).__init__(event_queue, config_name)

    self.input_pin = input_pin
    self.output_pin = output_pin

    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)  # for reusing pins
    if self.input_pin:
      GPIO.setup(self.input_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    if self.output_pin:
      GPIO.setup(self.output_pin, GPIO.OUT)


class NoMatchingDevice(Exception):
  """Generic exception for missing devices."""


def _import(name):
  module, object_name = name.rsplit('.', 1)
  # The return value of __import__ requires walking the dots, so
  # this is a fairly standard workaround that's easier.  Intermediate
  # names appear to always get added to sys.modules.
  __import__(module)
  return getattr(sys.modules[module], object_name)


