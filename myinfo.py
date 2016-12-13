#!/usr/bin/python
# -*- coding: utf-8 -*-


def get(prop):
    INFO = {
            "version": "1.00",
            "url": "https://github.com/akira310/GSVchecker",
            "err": "Inavlid keyword",
            }

    return INFO[prop] if prop in INFO else INFO["err"]
