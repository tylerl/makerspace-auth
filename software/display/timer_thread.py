import time
import threading
import Queue
import heapq
import traceback


class Heap(list):
  def put(self, item):
    heapq.heappush(self, item)
  def pop(self):
    return heapq.heappop(self)

class _Task(object):
  def __init__(self, func, args, kwargs):
    self.func = func
    self.args = args
    self.kwargs = kwargs
    self._cancelled = False
  
  def cancel(self):
    self._cancelled = True
  
  def __call__(self):
    if not self._cancelled:
      self.func(*self.args, **self.kwargs)

class TimerThread(threading.Thread):
  """Thread which manages running commands after a given delay.  
  """
  TIMER_FUDGE = 1e-3 # dont' bother sleeping shorter than 1ms
  def __init__(self):
    self.daemon = True
    self._queue = Queue.Queue()

  def add(self, timeout_sec, func, *args, **kwargs):
    """Add a new task to execute after a delay.
    Args:
      timeout_sec: float - when to execute the command
      func:        function to run
      *args:       positional args for function
      **kwargs:    kwargs for function
    
    Returns:
      cancel():    Callable which cancels the timer.
    """
    task = _Task(func, args, kwargs)
    self._queue.put((time.time()+timeout_sec, task))
    return task.cancel

  def run(self):
    """Main thread.

    Waits for new timers to be added (via message queue), and puts them
    into a priority queue, ordered by expiration time. Waits for the 
    soonest-expiring timer and runs the associated task when it's up.
    """
    heap = Heap()

    while True:
      while heap:
        now = time.time() + self.TIMER_FUDGE        
        next_timeout = heap[0][0]
        if next_timeout <= now:
          task = heap.pop()[1]
          try: task()
          except: traceback.print_exc()
          continue
        else:
          break
      else:
        next_timeout = None
      try:
        item = self._queue.get(timeout=next_timeout)
      except Queue.Empty:
        continue
      if item:
        heap.put(item)

