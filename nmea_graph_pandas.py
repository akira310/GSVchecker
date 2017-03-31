#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import time
import logging
import copy
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


def add_timediff(dt, tdiff):
    return datetime.datetime.fromtimestamp(int(time.mktime(dt.timetuple())) + tdiff)

def check_thr(panel, thr, show, timewidth, tdiff):
    print(timewidth)
    cmn = panel.minor_xs("cmn").T
    start = add_timediff(timewidth[0], -1*tdiff) if timewidth[0] else None  # start time
    end = add_timediff(timewidth[1], -1*tdiff) if timewidth[1] else None    # end time
    indx = {"start": 0, "end": len(cmn)}

    for i, (d, t) in enumerate(zip(cmn["date"], cmn["time"])):
        if start == None and end == None:
            break

        if d != None and t != None:
            try:
                dt = datetime.datetime.combine(d, t)

                if start and start <= dt:
                    indx["start"] = i
                    start = None

                if end and end < dt:
                    indx["end"] = i
                    end = None
            except TypeError:
                pass

    checkeddf = dict()
    for sv in panel.ix[0].columns:
        df = panel.minor_xs(sv)
        if sv == "cmn" or\
            (pd.to_numeric(df.ix["sn"].fillna(0)).mean() > thr["sn"] and
            (show["gsamode"] and pd.to_numeric(df.ix["el"].fillna(0)).mean() > thr["el"])):
            checkeddf[sv] = df.T

    return pd.Panel(checkeddf)[indx["start"]:indx["end"]]

def make_timestr(t, tdiff):
    if t:
        t_mod = add_timediff(datetime.datetime.combine(t[0], t[1]), tdiff)
        return "{}/{} {}".format(t_mod.date().month, t_mod.date().day, t_mod.time())
    return "----"

def conv2num(panel):


class NMEAGraph(object):
    u""" NMEAパース結果描画クラス

    パースされたデータを元にグラフを描画する
    """

    def __init__(self, tid, gpspanel, tz):
        self._log = logging.getLogger(__name__)
        self._tid = tid
        self._tz = tz
        self._gpspanel = conv2num(gpspanel)

    def _create_bargraph(panel, thr, ax):
        ax.set_ylim(thr["sn"], 50)
        x = list()
        y = list()
        if len(panel) < 1:
            return

        for sv in panel.items:
            if sv == "cmn":
                continue
            x.append(sv)
            y.append()


        for k, v in sorted(panel["sv"].items(), key=lambda x: int(x[0])):
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

        for k, v in gps["sv"].items():
            if np.min(v["az"]) > 0 and np.min(v["el"]) > 0:
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

    def draw(self, thr, show, timewidth):
        u""" グラフ描画 """

        # sns.set(palette='colorblind')
        sns.set_style("white")
        fig = plt.figure()
        fig.suptitle("tid [{}]".format(self._tid))

        panel = check_thr(copy.deepcopy(self._gpspanel), thr, show, timewidth, self._tz)
        row = 2 if show["avrg"] or show["pos"] else 1
        col = 2 if show["avrg"] and show["pos"] else 1
        if show["avrg"]:
            self._create_bargraph(panel, thr, fig.add_subplot(row, col, 1))
        if show["pos"]:
            self._create_polargraph(panel, gsamode, fig.add_subplot(row, col, col, polar=True))
        self._create_linegraph(panel, thr, self._tz, fig.add_subplot(row, 1, row))
        plt.show()


if __name__ == '__main__':
    print("WARN: this file is not entry point !!", file=sys.stderr)
