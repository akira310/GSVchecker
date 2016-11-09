#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import matplotlib.pyplot as plt
import matplotlib.ticker as tckr
import seaborn as sns
import numpy as np
from math import *
import re
import copy
import logging


class NMEAGraph(object):
    u""" NMEAパース結果描画クラス

    パースされたデータを元にグラフを描画する
    """

    def __init__(self, tid, gps):
        self._log = logging.getLogger(__name__)
        self._tid = tid
        self._gsaorg = self._create_gsa(gps)

    def _create_gsa(self, gpslist):
        gsa = {"sv":{"dummy":{"sn":[], "el":[], "az":[]}}, "time":[]}
        for gps in gpslist:
            if "GSA" in gps:
                self._add_sv2gsa(gps, gsa)
                self._add_sn2gsa(gps, gsa)
                gsa["time"].append("{}/{} {}".format(gps["RMC"].datestamp.month,
                                                     gps["RMC"].datestamp.day,
                                                     gps["RMC"].timestamp))
        gsa["sv"].pop("dummy")
        return gsa

    def _add_sv2gsa(self, gps, gsa):
        for used in gps["GSA"]["sv"]:
            if used not in gsa["sv"]:
                gsa["sv"][used] = copy.deepcopy(gsa["sv"]["dummy"])

    def _add_sn2gsa(self, gps, gsa):
        for sv in gps["GSV"]["sv"]:
            if sv["no"] in gsa["sv"]:
                gsa["sv"][sv["no"]]["sn"].append(int(sv["sn"] if sv["sn"] else 0))
                gsa["sv"][sv["no"]]["el"].append(int(sv["el"] if sv["el"] else 0))
                if sv["az"]:
                    gsa["sv"][sv["no"]]["az"].append(int(sv["az"]))
        gsa["sv"]["dummy"]["sn"].append(0)
        gsa["sv"]["dummy"]["el"].append(0)

    def _check_thr(self, gsa, thr):
        poplist = list()
        for k, v in gsa["sv"].items():
            if np.average(v["sn"]) < thr["sn"] or\
               np.average(v["el"]) < thr["el"]:
               poplist.append(k)
        for k in poplist:
            gsa["sv"].pop(k)
        return gsa


    def _create_bargraph(self, gsa, thr, ax):
        ax.set_ylim(thr["sn"], 50)
        x = list()
        y = list()
        if len(gsa) < 1:
            return
        for k, v in sorted(gsa["sv"].items(), key=lambda x: int(x[0])):
            x.append(k)
            y.append(np.average(v["sn"]))
        rects = ax.bar(left=[x for x in range(len(x))], height=y, tick_label=x)

        avrg = np.average(y) if len(y) > 0 else 0
        ax.set_title("avrg.:{}".format(avrg))
        for rect in rects:
            h = rect.get_height()
            ax.text(rect.get_x(), h+2, int(h), ha='center', va='bottom')

    def _create_polargraph(self, gsa, thr, ax):
        sv = list()
        theta = list()
        r = list()
        for k, v in sorted(gsa["sv"].items(), key=lambda x: int(x[0])):
            sv.append(k)
            theta.append(np.radians(np.average(v["az"])))
            r.append(90 - np.average(v["el"]))
        # ax.set_rlim(0, 90-thr["el"])
        ax.set_rlim(0, 90)
        ax.set_yticklabels([])
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_thetagrids([i*45 for i in range(8)], ['N','NE','E','SE','S','SW','W','NW'])
        ax.plot(theta, r, 'o')

        for s, t, v in zip(sv, theta, r):
            ax.text(t, v, s)

    def _create_linegraph(self, gsa, thr, ax):
        ax.set_title("fixed SN")
        ax.set_ylabel("CN")
        ax.set_ylim(thr["sn"], 50)
        if len(gsa) < 1:
            return
        for k, v in sorted(gsa["sv"].items(), key=lambda x: int(x[0])):
            ax.plot(v["sn"], label=k)
        ax.set_xticklabels(gsa["time"], rotation=15, fontsize="small")
        ax.legend(bbox_to_anchor=(1, 1), loc=2, frameon=True)


    def draw(self, thr):
        u""" グラフ描画 """

        # sns.set(palette='colorblind')
        sns.set_style("white")

        fig = plt.figure()
        fig.suptitle("tid [{}]".format(self._tid))
        gsa = self._check_thr(copy.deepcopy(self._gsaorg), thr)
        self._create_bargraph(gsa, thr, fig.add_subplot(2, 2, 1))
        self._create_polargraph(gsa, thr, fig.add_subplot(2, 2, 2, polar=True))
        self._create_linegraph(gsa, thr, fig.add_subplot(2, 1, 2))
        plt.show()


if __name__ == '__main__':
    print("WARN: this file is not entry point !!", file=sys.stderr)
    sleep(5)
