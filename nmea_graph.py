#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import logging
import copy
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


def add_sv2gsa(gps, gsa):
    for used in gps["GSA"]["sv"]:
        if used not in gsa["sv"]:
            gsa["sv"][used] = copy.deepcopy(gsa["sv"]["dummy"])


def add_sn2gsa(gps, gsa):
    for sv in gps["GSV"]["sv"]:
        if sv["no"] in gsa["sv"]:
            gsa["sv"][sv["no"]]["sn"].append(int(sv["sn"] if sv["sn"] else 0))
            gsa["sv"][sv["no"]]["el"].append(int(sv["el"] if sv["el"] else 0))
            if sv["az"]:
                gsa["sv"][sv["no"]]["az"].append(int(sv["az"]))
    gsa["sv"]["dummy"]["sn"].append(0)
    gsa["sv"]["dummy"]["el"].append(0)


def check_thr(gsa, thr):
    poplist = list()
    for k, v in gsa["sv"].items():
        if np.average(v["sn"]) < thr["sn"] or np.average(v["el"]) < thr["el"]:
            poplist.append(k)
    for k in poplist:
        gsa["sv"].pop(k)
    return gsa


def create_gsa(gpslist):
    gsa = {"sv": {"dummy": {"sn": [], "el": [], "az": []}}, "time": []}
    for gps in gpslist:
        if "GSA" in gps:
            add_sv2gsa(gps, gsa)
            add_sn2gsa(gps, gsa)
            gsa["time"].append("{}/{} {}".format(gps["RMC"].datestamp.month,
                                                 gps["RMC"].datestamp.day,
                                                 gps["RMC"].timestamp))
    gsa["sv"].pop("dummy")
    return gsa


class NMEAGraph(object):
    u""" NMEAパース結果描画クラス

    パースされたデータを元にグラフを描画する
    """

    def __init__(self, tid, gps):
        self._log = logging.getLogger(__name__)
        self._tid = tid
        self._gsaorg = create_gsa(gps)

    @staticmethod
    def _create_bargraph(gsa, thr, ax):
        ax.set_ylim(thr["sn"], 50)
        x = list()
        y = list()
        if len(gsa) < 1:
            return
        for k, v in sorted(gsa["sv"].items(), key=lambda x: int(x[0])):
            x.append(k)
            y.append(np.average(v["sn"]))
        rects = ax.bar(left=[x for x in range(len(x))], height=y, tick_label=x)

        svnum = len(y)
        avrg = np.average(sorted(y, reverse=True)[:3]) if svnum >= 3 else 0
        print(["{:.2f}".format(top3) for top3 in sorted(y, reverse=True)[:3]])
        ax.set_title("num:{}   top3 avrg.{:.1f}".format(svnum, avrg))
        for rect in rects:
            h = rect.get_height()
            ax.text(rect.get_x()+0.3, h, "{:.1f}".format(h),
                    ha='center', va='bottom')

    @staticmethod
    def _create_polargraph(gsa, ax):
        sv = list()
        theta = list()
        r = list()
        for k, v in sorted(gsa["sv"].items(), key=lambda x: int(x[0])):
            sv.append(k)
            theta.append(np.radians(np.average(v["az"])))
            r.append(90 - np.average(v["el"]))
        ax.set_rlim(0, 90)
        ax.set_yticklabels([])
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_thetagrids([i*45 for i in range(8)],
                          ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])
        ax.plot(theta, r, 'o')

        for s, t, v in zip(sv, theta, r):
            ax.text(t, v, s)

    @staticmethod
    def _create_linegraph(gsa, thr, ax):
        ax.set_title("fixed SN")
        ax.set_ylabel("CN")
        ax.set_ylim(thr["sn"], 50)
        if len(gsa) < 1:
            return
        for k, v in sorted(gsa["sv"].items(), key=lambda x: int(x[0])):
            ax.plot(v["sn"], label=k)
        ax.set_xticks([0, len(gsa["time"])//2, len(gsa["time"])-1])
        ax.set_xticklabels([gsa["time"][0], gsa["time"][len(gsa["time"])//2],
                            gsa["time"][-1]],
                           rotation=15, fontsize="small")
        ax.legend(bbox_to_anchor=(1, 1), loc=2, frameon=True)

    def draw(self, thr, show):
        u""" グラフ描画 """

        # sns.set(palette='colorblind')
        sns.set_style("white")
        fig = plt.figure()
        fig.suptitle("tid [{}]".format(self._tid))
        gsa = check_thr(copy.deepcopy(self._gsaorg), thr)
        row = 2 if show["avrg"] or show["pos"] else 1
        col = 2 if show["avrg"] and show["pos"] else 1
        if show["avrg"]:
            self._create_bargraph(gsa, thr, fig.add_subplot(row, col, 1))
        if show["pos"]:
            self._create_polargraph(gsa,
                                    fig.add_subplot(row, col, col, polar=True))
        self._create_linegraph(gsa, thr, fig.add_subplot(row, 1, row))
        plt.show()


if __name__ == '__main__':
    print("WARN: this file is not entry point !!", file=sys.stderr)
