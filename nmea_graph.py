#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import matplotlib.pyplot as plt
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
        for fixed in fixed_dict["sn"]:
            self.__used.append(fixed["used"])
            self.__usedsn.append(fixed["sn"])
            self.__time.append(fixed["time"])
        for gsv in gsv_dict:
            self.__gsvnum.append(gsv["num"])
            self.__gsvsn.append(gsv["sn"])

    def draw(self):
        u""" グラフ描画 """

        sns.set(palette='colorblind')
        sns.set_style("white")
        palette = sns.color_palette()

        fig = plt.figure()
        fig.suptitle("id: {0}  TTFF: {1} sec".format(self.__tid, self.__ttff))

        ax11 = fig.add_subplot(2, 1, 1)
        ax11.set_title("FIXED")
        ax11.plot(self.__used, label="st_used", color=palette[0])
        ax11.set_ylabel("st_used")
        ax11.set_ylim(0, 12)
        tw11 = ax11.twinx()
        tw11.plot(self.__usedsn, label="S/N", color=palette[1])
        tw11.set_ylabel("S/N")
        tw11.set_ylim(20, 40)
        # tw11.grid(ls='--')
        h1, l1 = ax11.get_legend_handles_labels()
        h2, l2 = tw11.get_legend_handles_labels()
        ax11.legend(h1+h2, l1+l2, loc="upper left")

        ax21 = fig.add_subplot(2, 1, 2)
        ax21.set_title("ALL")
        ax21.plot(self.__gsvnum, label="st_num", color=palette[2])
        ax21.set_ylabel("st_num")
        ax21.set_ylim(0, 22)
        # ax21.grid(ls='--')
        tw21 = ax21.twinx()
        tw21.plot(self.__gsvsn, label="S/N", color=palette[3])
        tw21.set_ylabel("S/N")
        tw21.set_ylim(0, 40)
        h1, l1 = ax21.get_legend_handles_labels()
        h2, l2 = tw21.get_legend_handles_labels()
        ax21.legend(h1+h2, l1+l2, loc="upper left")

        plt.show()


if __name__ == '__main__':
    print("WARN: this file is not entry point !!", file=sys.stderr)
    sleep(5)
