#!/usr/bin/env python3
# -*- coding: utf-8 -*-

_API_URL = "https://api.stackexchange.com/2.2/"

import requests

class StackOverflow:
    """..."""

    def __init__(self):
        self._session = requests.Session()

    def request(self, method, **kwargs):
        return self._session.get(_API_URL + method, params=kwargs).json()
