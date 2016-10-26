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
        self._gsa = self._create_gsa(gps)

    def _create_gsa(self, gpslist):
        gsa = {"sv":{"dummy":[]}, "time":[]}
        for gps in gpslist:
            if "GSA" in gps:
                self._add_sv2gsa(gps, gsa)
                self._add_sn2gsa(gps, gsa)
                gsa["time"].append("{}/{} {}".format(gps["RMC"].datestamp.month,
                                                     gps["RMC"].datestamp.day,
                                                     gps["RMC"].timestamp))
        gsa["sv"].pop("dummy")
        return self._check_thr(gsa)

    def _add_sv2gsa(self, gps, gsa):
        for used in gps["GSA"]["sv"]:
            if used not in gsa["sv"]:
                gsa["sv"][used] = gsa["sv"]["dummy"][:]

    def _add_sn2gsa(self, gps, gsa):
        for sv in gps["GSV"]["sv"]:
            if sv["no"] in gsa["sv"]:
                gsa["sv"][sv["no"]].append(int(sv["sn"] if sv["sn"] and int(sv["el"]) > 20 else 0))
        gsa["sv"]["dummy"].append(0)

    def _check_thr(self, gsa):
        poplist = list()
        for k, v in gsa["sv"].items():
            if sum(list(map(int, v)))//len(v) < 15:
                poplist.append(k)
        for k in poplist:
            gsa["sv"].pop(k)
        return gsa


    def _create_bargraph(self, ax):
        ax.set_ylim(15, 50)
        x = list()
        y = list()
        for k, v in sorted(self._gsa["sv"].items(), key=lambda x: int(x[0])):
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
        ax.set_ylim(15, 50)
        for k, v in sorted(self._gsa["sv"].items(), key=lambda x: int(x[0])):
            ax.plot(v, label=k)
        ax.set_xticklabels(self._gsa["time"], rotation=15, fontsize="small")
        ax.legend(bbox_to_anchor=(1, 1), loc=2, frameon=True)


    def draw(self):
        u""" グラフ描画 """

        # sns.set(palette='colorblind')
        sns.set_style("white")

        fig = plt.figure()
        fig.suptitle("tid [{}]".format(self._tid))
        self._create_bargraph(fig.add_subplot(2, 1, 1))
        self._create_linegraph(fig.add_subplot(2, 1, 2))
        plt.show()


if __name__ == '__main__':
    print("WARN: this file is not entry point !!", file=sys.stderr)
    sleep(5)
