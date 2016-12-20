#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import time
import logging
import copy
import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


def check_thr(gps, thr, show, timewidth):
    poplist = list()
    for k, v in gps["sv"].items():
        if (np.average(v["sn"]) < thr["sn"]) or \
           (show["gsamode"] and np.average(v["el"]) < thr["el"]):
            poplist.append(k)
    for k in poplist:
        gps["sv"].pop(k)

    print(timewidth)
    if timewidth[0]:    # start time
        for i, t in enumerate(gps["time"]):
            dt = datetime.datetime.combine(t[0], t[1])
            if timewidth[0] <= dt:
                gps["time"] = gps["time"][i:]
                for v in gps["sv"].values():
                    for k in ["sn", "el", "az"]:
                        v[k] = v[k][i:]
                break

    if timewidth[1]:    # end time
        for i, t in enumerate(reversed(gps["time"])):
            dt = datetime.datetime.combine(t[0], t[1])
            if timewidth[1] >= dt:
                end = len(gps["time"])-i
                gps["time"] = gps["time"][:end]
                for v in gps["sv"].values():
                    for k in ["sn", "el", "az"]:
                        v[k] = v[k][:end]
                break

    return gps


def make_timestr(t, tdiff):
    if t:
        t_mod = datetime.datetime.fromtimestamp(
                    int(time.mktime(datetime.datetime.combine(t[0], t[1]).timetuple()))
                    + tdiff)
        return "{}/{} {}".format(t_mod.date().month, t_mod.date().day, t_mod.time())
    return "----"


def add_gsadata(gsasv, sv, gsa):
    # check SV No.
    for used in gsasv:
        if used not in gsa["sv"]:
            gsa["sv"][used] = copy.deepcopy(gsa["sv"]["dummy"])

    # add gsv data
    if sv["no"] in gsa["sv"]:
        gsa["sv"][sv["no"]]["sn"].append(int(sv["sn"] if sv["sn"] else 0))
        if sv["el"]:
            gsa["sv"][sv["no"]]["el"].append(int(sv["el"]))
        if sv["az"]:
            gsa["sv"][sv["no"]]["az"].append(int(sv["az"]))


def add_gsvdata(gps, gsv, gsa):
    if "GSV" in gps:
        for sv in gps["GSV"]["sv"]:
            # check SV No.
            if sv["no"] not in gsv["sv"]:
                gsv["sv"][sv["no"]] = copy.deepcopy(gsv["sv"]["dummy"])

            gsv["sv"][sv["no"]]["sn"].append(int(sv["sn"] if sv["sn"] else 0))
            if sv["el"]:
                gsv["sv"][sv["no"]]["el"].append(int(sv["el"]))
            if sv["az"]:
                gsv["sv"][sv["no"]]["az"].append(int(sv["az"]))

            if "GSA" in gps:
                add_gsadata(gps["GSA"]["sv"], sv, gsa)

    gsv["sv"]["dummy"]["sn"].append(0)
    gsv["sv"]["dummy"]["el"].append(0)
    if "GSA" in gps:
        gsa["sv"]["dummy"]["sn"].append(0)
        gsa["sv"]["dummy"]["el"].append(0)


def create_gpsdata(gpsinput):
    base = {"sv": {"dummy": {"sn": [], "el": [], "az": []}}, "time": []}
    gsa = copy.deepcopy(base)
    gsv = copy.deepcopy(base)

    for gps in gpsinput:
        rmc = gps["RMC"]
        now = (rmc.datestamp, rmc.timestamp) if rmc.datestamp and rmc.timestamp else None
        gsv["time"].append(now)
        if "GSA" in gps:
            gsa["time"].append(now)

        add_gsvdata(gps, gsv, gsa)

    gsa["sv"].pop("dummy")
    gsv["sv"].pop("dummy")

    return gsv, gsa


class NMEAGraph(object):
    u""" NMEAパース結果描画クラス

    パースされたデータを元にグラフを描画する
    """

    def __init__(self, tid, gpsinput):
        self._log = logging.getLogger(__name__)
        self._tid = tid
        self._gsv, self._gsa = create_gpsdata(gpsinput)

    @staticmethod
    def _create_bargraph(gps, thr, ax):
        ax.set_ylim(thr["sn"], 50)
        x = list()
        y = list()
        if len(gps) < 1:
            return
        for k, v in sorted(gps["sv"].items(), key=lambda x: int(x[0])):
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
    def _create_polargraph(gps, gsamode, ax):
        sv = list()
        theta = list()
        r = list()

        if gsamode:
            for k, v in gps["sv"].items():
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

    def _create_linegraph(self, gps, thr, tdiff, ax):
        ax.set_title("fixed SN")
        ax.set_ylabel("CN")
        ax.set_ylim(thr["sn"], 50)

        if len(gps) < 1 or len(gps["time"]) < 3:
            return

        for k, v in sorted(gps["sv"].items(), key=lambda x: int(x[0])):
            ax.plot(v["sn"], label=k)

        timespan = self._get_linegraph_timesplit(gps["time"])
        ax.set_xticks(timespan)
        ax.set_xticklabels(map(lambda i: make_timestr(gps["time"][i], tdiff), timespan),
                           rotation=15, fontsize="small")
        ax.legend(bbox_to_anchor=(1, 1), loc=2, frameon=True)

    @staticmethod
    def _get_linegraph_timesplit(time):
        l = [0]
        timelen = len(time)
        splt = 5 if timelen > 5 else timelen-1
        l = [i for i in range(0, timelen-1, (timelen-1)//splt)]
        # 分割した最後の値が終端に近すぎるとグラフ描画時に文字が重なるため削除
        if (timelen-1)-l[-1] < (l[1]-l[0])/3:
            l.pop(-1)

        return l + [timelen-1]

    def draw(self, thr, show, timewidth, tdiff=0):
        u""" グラフ描画 """

        # sns.set(palette='colorblind')
        sns.set_style("white")
        fig = plt.figure()
        fig.suptitle("tid [{}]".format(self._tid))
        gsamode = True if show["gsamode"] and len(self._gsa["sv"]) else False
        gps = copy.deepcopy(self._gsa if gsamode else self._gsv)

        gps = check_thr(gps, thr, show, timewidth)
        row = 2 if show["avrg"] or show["pos"] else 1
        col = 2 if show["avrg"] and show["pos"] else 1
        if show["avrg"]:
            self._create_bargraph(gps, thr, fig.add_subplot(row, col, 1))
        if show["pos"]:
            self._create_polargraph(gps, gsamode, fig.add_subplot(row, col, col, polar=True))
        self._create_linegraph(gps, thr, tdiff, fig.add_subplot(row, 1, row))
        plt.show()


if __name__ == '__main__':
    print("WARN: this file is not entry point !!", file=sys.stderr)
