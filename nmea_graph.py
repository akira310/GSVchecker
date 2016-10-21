#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import matplotlib.pyplot as plt
import matplotlib.ticker as tckr
import seaborn as sns
from math import *
import re
import logging


class NMEAGraph(object):
    u""" NMEAパース結果描画クラス

    パースされたデータを元にグラフを描画する
    """

    def __init__(self, tid, gps):
        self._log = logging.getLogger(__name__)
        self._tid = tid
        self._gsa = self._create_gsalit(gps)

    def _create_gsalit(self, gpslist):
        gsa = {"sv":{"dummy":[]}, "time":[]}
        for g in gpslist:
            if "GSA" in g:
                for used in g["GSA"]["sv"]:
                    if used not in gsa["sv"]:
                        gsa["sv"][used] = gsa["sv"]["dummy"][:]

                for sv in g["GSV"]["sv"]:
                    if sv["no"] in gsa["sv"]:
                        gsa["sv"][sv["no"]].append(int(sv["sn"] if sv["sn"] else 0))

                gsa["sv"]["dummy"].append(0)
                date = g["RMC"].datestamp
                gsa["time"].append("{}/{} {}".format(date.month, date.day,
                                                     g["RMC"].timestamp))
        gsa["sv"].pop("dummy")
        return gsa

    def _create_bargraph(self, ax):
        ax.set_ylim(0, 50)
        x = list()
        y = list()
        for k, v in self._gsa["sv"].items():
            x.append(k)
            y.append(sum(list(map(int, v)))//len(v))
        rects = ax.bar(left=[x for x in range(len(x))], height=y, tick_label=x)

        ax.set_title("avrg.:{}".format(sum(y)//len(y)))
        for rect in rects:
            h = rect.get_height()
            ax.text(rect.get_x(), h+2, int(h), ha='center', va='bottom')

    def _create_linegraph(self, ax):
        ax.set_title("fixed SN")
        ax.set_ylabel("CN")
        ax.set_ylim(10, 50)
        for k, v in self._gsa["sv"].items():
            ax.plot(v, label=k)
        ax.set_xticklabels(self._gsa["time"], rotation=15, fontsize="small")


    def draw(self):
        u""" グラフ描画 """

        sns.set(palette='colorblind')
        sns.set_style("white")

        fig = plt.figure()
        fig.suptitle("tid[{}]: {}sec".format(self._tid, len(self._gsa["time"])))
        self._create_bargraph(fig.add_subplot(2, 1, 1))
        self._create_linegraph(fig.add_subplot(2, 1, 2))
        plt.show()


if __name__ == '__main__':
    print("WARN: this file is not entry point !!", file=sys.stderr)
    sleep(5)
