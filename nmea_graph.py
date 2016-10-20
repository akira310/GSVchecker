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
        self._gps = gps[::2]

    def draw(self):
        u""" グラフ描画 """

        sns.set(palette='colorblind')
        sns.set_style("white")

        fig = plt.figure()
        fig.suptitle("tid[{}]: {}sec".format(self._tid, len(self._gps)))

        ax21 = fig.add_subplot(2, 1, 2)
        ax21.set_title("fixed SN")
        ax21.set_ylabel("CN")
        ax21.set_ylim(10, 50)
        svlist = dict()
        svlist["dummy"] = list()
        timelist = list()
        for g in self._gps:
            if "GSA" in g:
                for used in g["GSA"]["sv"]:
                    if used not in svlist:
                        svlist[used] = svlist["dummy"][:]

                for sv in g["GSV"]["sv"]:
                    if sv["no"] in svlist:
                        svlist[sv["no"]].append(int(sv["sn"] if sv["sn"] else 0))

                svlist["dummy"].append(0)
                date = g["RMC"].datestamp
                timelist.append("{}/{} {}".format(date.month, date.day, g["RMC"].timestamp))

        for k, v in svlist.items():
            if k != "dummy":
                ax21.plot(v, label=k)
        ax21.set_xticklabels(timelist, rotation=15, fontsize="small")

        ax11 = fig.add_subplot(2, 1, 1)
        ax11.set_ylim(0, 50)
        svlist.pop("dummy")
        x = list()
        y = list()
        for k, v in svlist.items():
            x.append(k)
            y.append(sum(list(map(int, v)))//len(v))
        rects = ax11.bar(left=[x for x in range(len(x))], height=y, tick_label=x)

        ax11.set_title("avrg.:{}".format(sum(y)//len(y)))
        for rect in rects:
            h = rect.get_height()
            ax11.text(rect.get_x(), h+2, int(h), ha='center', va='bottom')


        plt.show()


if __name__ == '__main__':
    print("WARN: this file is not entry point !!", file=sys.stderr)
    sleep(5)
