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
        self.__log = logging.getLogger(__name__)
        self.__tid = tid
        self.__ttff = fixed_dict["ttff"]
        self.__used = list()
        self.__usedsn = list()
        self.__time = list()
        self.__gsvnum = list()
        self.__gsvsn = list()
        self.__gsvfix = list()
        for fixed in fixed_dict["sn"]:
            self.__used.append(fixed["used"])
            self.__usedsn.append(fixed["sn"])
            self.__time.append(fixed["time"])
        for gsv in gsv_dict:
            self.__gsvnum.append(gsv["num"])
            self.__gsvsn.append(gsv["sn"])
            self.__gsvfix.append(gsv["fix"])

    def draw(self):
        u""" グラフ描画 """

        sns.set(palette='colorblind')
        sns.set_style("white")
        palette = sns.color_palette()

        fig = plt.figure()
        fig.suptitle("id: {0}".format(self.__tid))
        fig.subplots_adjust(hspace=0.3)
        # fig.subplots_adjust(hspace=0.4, right=0.85)

        ax11 = fig.add_subplot(2, 1, 1)
        ax11.set_title("FIXED  TTFF: {0} sec  avg.[usednum: {1} S/N: {2}]"
                       .format(self.__ttff,
                               sum(self.__used)//len(self.__used),
                               sum(self.__usedsn)//len(self.__usedsn)))
        ax11.set_xlabel("count num")
        ax11.plot(self.__used, label="st_used", color=palette[0])
        ax11.set_ylabel("st_used")
        ax11.set_ylim(0, 20)
        tw11 = ax11.twinx()
        tw11.plot(self.__usedsn, label="S/N", color=palette[2])
        tw11.set_ylabel("S/N")
        tw11.set_ylim(20, 45)
        # tw11.grid(ls='--')
        h1, l1 = ax11.get_legend_handles_labels()
        h2, l2 = tw11.get_legend_handles_labels()
        ax11.legend(h1+h2, l1+l2, loc="upper left")

        ax21 = fig.add_subplot(2, 1, 2)
        ax21.set_title("ALL  num[avg:{avg} max:{max} min:{min}] avg.S/N: {sn}]"
                       .format(avg=sum(self.__gsvnum)//len(self.__gsvnum),
                               max=max(self.__gsvnum), min=min(self.__gsvnum),
                               sn=sum(self.__gsvsn)//len(self.__gsvsn)))
        ax21.set_xlabel("t (0.5s)")
        ax21.plot(self.__gsvnum, label="st_num", color=palette[0])
        ax21.set_ylabel("st_num")
        ax21.set_ylim(0, 22)
        # ax21.grid(ls='--')
        tw21 = ax21.twinx()
        tw21.plot(self.__gsvsn, label="S/N", color=palette[2])
        tw21.set_ylabel("S/N")
        tw21.set_ylim(0, 45)
        tww21 = ax21.twinx()
        tww21.plot(self.__gsvfix, label="fix", color=palette[4])
        tww21.set_ylim(0, 5)
        tww21.yaxis.set_major_locator(tckr.NullLocator())
        # tww21.spines["right"].set_position(("axes", 1.1))

        h1, l1 = ax21.get_legend_handles_labels()
        h2, l2 = tw21.get_legend_handles_labels()
        h3, l3 = tww21.get_legend_handles_labels()
        ax21.legend(h1+h2+h3, l1+l2+l3, loc="upper left")

        plt.show()


if __name__ == '__main__':
    print("WARN: this file is not entry point !!", file=sys.stderr)
    sleep(5)
