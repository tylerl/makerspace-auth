import yaml


class ConfigError(Exception):
  "Couldn't load a valid config."


class NoMatchingConfigError(ConfigError):
  "No config matched provided criteria"


class InvalidConfigError(ConfigError):
  "Config doesn't contain a spec: key"


def LoadYaml(stream, kind=None, metadata=None):
  """Find the config that matches the selector, and return its spec.
  Args:
    kind: string
    metadata: dict

    If present, kind and metadata must match the corresponding fields in the
    configuration, or the next items is used.
  """
  #
  for cfg in yaml.safe_load_all(stream):
    if kind and cfg.get('kind') != kind:
      continue
    if filter:
      if type(cfg.get('metadata') != dict):
        continue
      if not all(cfg['metadata'].get(k) == v for k, v in metadata.items()):
        continue
    break
  else:
    raise NoMatchingConfigError()

  try:
    return cfg['spec']
  except KeyError:
    raise
