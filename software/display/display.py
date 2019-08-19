from . import timer_thread

class Display(object):
  """Display interface exposed to the rest of the project.
  
  The interface has only one method: "setstate", which is used
  to set the new display state as chosen from a predefined list.
  
  All the rest of the logic is self-contained.
  """

  def __init__(self):
    pass
  def setstate(self, name, **kwargs):
    """Set the new display state.

    Args:
      name: String indicating the new display state. See your
            display config for the list of configured states.

      **kwargs: Key-value pairs associated with the new state. Their meaning 
            depends on the state, but as a rule rule they are strings inserted
            into display text. If the value is callable, then it is called to
            yield the display content every time the display is refreshed.
    """
    pass

class CharacterDisplay(object):

  def __init__(self, driver, config):
    self._driver = driver
    self._config = config
    self._lines = []
    self._stateargs = {}
    self._nowlines = []
    self._seq = None

  def _getstate(self, key):
    """Abstraction for getting state dict from config."""
    return self._config['states'][key]

  def _setlines(self, lines):
    """Abstraction for setting or display lines."""
    self._lines = lines
    self.refresh()

  def _formattedlines(self):
    """Yield lines with substitions applied.""" 
    args = {k:_refresh(v) for k,v in self._stateargs.items()}    
    for l in self._lines:
      yield l.format(**args)

  def refresh(self):
    """Refresh display without changing line template."""
    lines = list(self._formattedlines())
    if lines == self._nowlines:
      return  # noop

    if len(lines) != len(self._nowlines) or not any(a==b for a,b in zip(lines,self._nowlines)):
      self._driver.clear()  # full-clear because not a minor update
      self._nowlines = []

    for i, v in enumerate(lines):
      try:
        if v == self._nowlines[i]: continue
      except IndexError: pass  # line count may not be the same
      self._driver.writeline(i,v)

    self._nowlines = lines

  def _set_sequence_timer(self, timeout):
    # set timer on sequence->next
    pass

  def _set_refresh_interval(self, interval):
    pass
  
  def _clear_refresh_interval(self):
    pass

  def _startsequence(self, seq):
    """Kick off a sequence of lines for a single state."""
    self._seq = _Sequence(seq)
    self._setlines(self._seq.lines)
    if self._seq.end:
      self._set_sequnce_timer(self._seq.end)
    
  def setstate(self, name, **kwargs):
    """Set new state.

    Args:
        name:   string, state name from config file.
      **kwargs: any string format arguments that get subbed into the output.
                Values can be functions, in which case they'll be called
                to generate new output on every refresh (e.g. current time).
    """
    self._stateargs = kwargs
    state = self._getstate(name)
    self._clear_refresh_interval()    
    if 'lines' in state:
      self._setlines(state['lines'])
    elif 'seq' in state:
      self._startsequence(state['seq'])
    else:
      self._setlines([])
    if 'refresh' in state:
      self._set_refresh_interval(state['refresh'])
    
class _Sequence(object):
  def __init__(self, seq):
    self.duration = 0
    self.refresh = 0
    self._seq = seq
    self.lines = []
    if len(seq) > 0:
      self._setstate(0)
  
  def _setstate(self, id):
    self._stateid = id
    state = self._seq[id]
    self._start = int(time.time()*1000)
    self.duration = int(state.get('duration',0))
    self.refresh = int(state.get('refresh',0))
    self.lines = state.get('lines',[])
    self.end = 0 if not self.duration else self.duration + self._start
      
  def next(self):
    self._setstate(self._stateid + 1) % len(self._seq)



def _refresh(v):
  return v() if callable(v) else v

class BaseDriver(object):
  line_len = 16

  def clear(self):
    raise NotImplementedError()

  def move(self, line, col):
    raise NotImplementedError()

  def write(self, msg):
    raise NotImplementedError()

  def writeat(self, line, col, msg):
    if len(msg) + col > self.line_len:
      msg = msg[:self.line_len - col]
    self.move(line, col)
    self.write(msg)

  def writeline(self, line, msg):
    self.writeat(line, 0, msg)
