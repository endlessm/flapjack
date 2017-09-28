# Copyright 2017 Endless Mobile, Inc.

import collections
import functools
import json

from . import config
from .json_minify import json_minify


@functools.lru_cache()
def get_source_manifest():
    with open(config.source_manifest()) as f:
        # Sadly, the GNOME manifest has comments in it.
        data = json_minify(f.read())
        return json.loads(data, object_pairs_hook=collections.OrderedDict)


@functools.lru_cache()
def get_dev_tools_manifest():
    if not config.dev_tools_manifest():
        return []
    with open(config.dev_tools_manifest()) as f:
        return json.load(f, object_pairs_hook=collections.OrderedDict)
