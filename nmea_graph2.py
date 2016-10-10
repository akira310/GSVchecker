#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import matplotlib.pyplot as plt
import matplotlib.ticker as tckr
import seaborn as sns
from math import *
import re
import logging


class NMEAGraph2(object):
    u""" NMEAパース結果描画クラス

    パースされたデータを元にグラフを描画する
    """

    def __init__(self, tid, gps):
        self._log = logging.getLogger(__name__)
        self._tid = tid
        self._gps = gps

    def draw(self):
        u""" グラフ描画 """

        sns.set(palette='colorblind')
        sns.set_style("white")

        fig = plt.figure()
        fig.suptitle("{}: {}".format(self._tid, len(self._gps)))
        fig.subplots_adjust(hspace=0.3)

        ax11 = fig.add_subplot(2, 1, 1)
        ax11.set_title("title")
        ax11.set_xlabel("time(4sec)")
        ax11.set_ylabel("CN")
        ax11.set_ylim(10, 50)
        svlist = dict()
        svlist["dummy"] = list()
        for g in self._gps:
            if "GSA" in g:
                for used in g["GSA"]["sv"]:
                    if used not in svlist:
                        svlist[used] = svlist["dummy"][:]

                for sv in g["GSV"]["sv"]:
                    if sv["no"] in svlist:
                        svlist[sv["no"]].append(int(sv["sn"] if sv["sn"] else 0))

                svlist["dummy"].append(0)

        for k, v in svlist.items():
            if k != "dummy":
                ax11.plot(v, label=k)

        ax21 = fig.add_subplot(2, 1, 2)
        ax21.set_title("avrg")
        ax21.set_ylim(0, 50)
        svlist.pop("dummy")
        x = list()
        y = list()
        for k, v in svlist.items():
            x.append(k)
            y.append(sum(list(map(int, v)))//len(v))
        ax21.bar([x for x in range(len(x))], y)
        ax21.set_xticklabels(x)

        plt.show()


if __name__ == '__main__':
    print("WARN: this file is not entry point !!", file=sys.stderr)
    sleep(5)
