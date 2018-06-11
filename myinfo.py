#!/usr/bin/python
# -*- coding: utf-8 -*-


def get(prop):
    INFO = {
            "version": "1.0.1",
            "url": "https://github.com/sakirror/GSVchecker",
            "err": "Inavlid keyword",
            }

    return INFO[prop] if prop in INFO else INFO["err"]
