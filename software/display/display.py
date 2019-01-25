
class CharacterDisplay(object):

  def __init__(self, driver, config):
    self._driver = driver
    self._config = config
    self._lines = []
    self._stateargs = {}
    self._nowlines = []

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
      self._nowlines = [''] * len(self._nowlines)

    for i, v in enumerate(lines):
      try:
        if v == self._nowlines[i]: continue
      except IndexError: pass  # line count may not be the same
      self._driver.writeline(i,v)
    
    self._nowlines = lines


  def _startsequence(self, seq):
    """Kick off a sequence of lines for a single state."""
    pass

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
    if 'lines' in state:
      self._setlines(state['lines'])
    elif 'seq' in state:
      self._startsequence(state['seq'])
    else:
      self._setlines([])


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
