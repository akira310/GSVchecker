#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import matplotlib.pyplot as plt
import seaborn as sns
from math import *
import re


class NMEAGraph(object):
    u""" NMEAパース結果描画クラス

    パースされたデータを元にグラフを描画する
    """

    def __init__(self, tid, sn_dict):
        self.__tid = tid
        self.__used = list()
        self.__sn = list()
        self.__time = list()
        for sn in sn_dict:
            self.__used.append(sn["used"])
            self.__sn.append(sn["sn"])
            self.__time.append(sn["time"])

    def draw(self):
        u""" グラフ描画 """

        sns.set(palette='colorblind')
        sns.set_style("white")
        palette = sns.color_palette()

        fig = plt.figure()
        fig.suptitle("trip id: {0}".format(self.__tid))

        ax11 = fig.add_subplot(1, 1, 1)
        ax11.plot(self.__used, label="st_used", color=palette[0])
        ax11.set_ylabel("st_used")
        ax11.set_ylim(0, 12)
        tw11 = ax11.twinx()
        tw11.plot(self.__sn, label="S/N", color=palette[1])
        tw11.set_ylabel("S/N")
        tw11.set_ylim(20, 40)
        # tw11.grid(ls='--')
        h1, l1 = ax11.get_legend_handles_labels()
        h2, l2 = tw11.get_legend_handles_labels()
        ax11.legend(h1+h2, l1+l2, loc="upper left")

        plt.show()


def warning(*objs):
    print("WARNING: ", *objs, file=sys.stderr)

if __name__ == '__main__':
    warning("this file is not entry point !!")
    sleep(5)
