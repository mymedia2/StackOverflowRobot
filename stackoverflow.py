#!/usr/bin/env python3
# -*- coding: utf-8 -*-

_API_URL = "https://api.stackexchange.com/2.2/"

import requests

class StackOverflow:
    """..."""

    def __init__(self, key, main_filter):
        self._session = requests.Session()
        self._key = key
        self._main_filter = main_filter

    def request(self, method, **kwargs):
        method = method.format(**kwargs)
        kwargs.setdefault('key', self._key)
        kwargs.setdefault('filter', self._main_filter)
        # XXX: maybe unnecessary parameters ...
        return self._session.get(_API_URL + method, params=kwargs).json()
