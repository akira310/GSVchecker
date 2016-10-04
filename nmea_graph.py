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

    def __init__(self, tid, fixed_dict, gsv_dict):
        self._log = logging.getLogger(__name__)
        self._tid = tid
        self._ttff = fixed_dict["ttff"]
        self._used = list()
        self._usedsn = list()
        self._time = list()
        self._gsvnum = list()
        self._gsvsn = list()
        self._gsvfix = list()
        for fixed in fixed_dict["sn"]:
            self._used.append(fixed["used"])
            self._usedsn.append(fixed["sn"])
            self._time.append(fixed["time"])
        for gsv in gsv_dict:
            self._gsvnum.append(gsv["num"])
            self._gsvsn.append(gsv["sn"])
            self._gsvfix.append(gsv["fix"])

    def draw(self):
        u""" グラフ描画 """

        sns.set(palette='colorblind')
        sns.set_style("white")
        palette = sns.color_palette()

        fig = plt.figure()
        fig.suptitle("id: {0}".format(self._tid))
        fig.subplots_adjust(hspace=0.3)
        # fig.subplots_adjust(hspace=0.4, right=0.85)

        ax11 = fig.add_subplot(2, 1, 1)
        ax11.set_title("FIXED  TTFF: {0} sec  avg.[usednum: {1} S/N: {2}]"
                       .format(self._ttff,
                               sum(self._used)//len(self._used) if (len(self._used)) else 0,
                               sum(self._usedsn)//len(self._usedsn) if (len(self._used)) else 0))
        ax11.set_xlabel("count num")
        ax11.plot(self._used, label="st_used", color=palette[0])
        ax11.set_ylabel("st_used")
        ax11.set_ylim(0, 20)
        tw11 = ax11.twinx()
        tw11.plot(self._usedsn, label="S/N", color=palette[2])
        tw11.set_ylabel("S/N")
        tw11.set_ylim(20, 45)
        # tw11.grid(ls='--')
        h1, l1 = ax11.get_legend_handles_labels()
        h2, l2 = tw11.get_legend_handles_labels()
        ax11.legend(h1+h2, l1+l2, loc="lower right")

        ax21 = fig.add_subplot(2, 1, 2)
        ax21.set_title("ALL  num[avg:{avg} max:{max} min:{min}] avg.S/N: {sn}"
                       .format(avg=sum(self._gsvnum)//len(self._gsvnum),
                               max=max(self._gsvnum), min=min(self._gsvnum),
                               sn=sum(self._gsvsn)//len(self._gsvsn)))
        ax21.set_xlabel("t (0.5s)")
        ax21.plot(self._gsvnum, label="st_num", color=palette[0])
        ax21.set_ylabel("st_num")
        ax21.set_ylim(0, 22)
        # ax21.grid(ls='--')
        tw21 = ax21.twinx()
        tw21.plot(self._gsvsn, label="S/N", color=palette[2])
        tw21.set_ylabel("S/N")
        tw21.set_ylim(0, 45)
        tww21 = ax21.twinx()
        tww21.plot(self._gsvfix, label="fix", color=palette[4])
        tww21.set_ylim(0, 5)
        tww21.yaxis.set_major_locator(tckr.NullLocator())
        # tww21.spines["right"].set_position(("axes", 1.1))

        h1, l1 = ax21.get_legend_handles_labels()
        h2, l2 = tw21.get_legend_handles_labels()
        h3, l3 = tww21.get_legend_handles_labels()
        ax21.legend(h1+h2+h3, l1+l2+l3, loc="lower right")

        plt.show()


if __name__ == '__main__':
    print("WARN: this file is not entry point !!", file=sys.stderr)
    sleep(5)
