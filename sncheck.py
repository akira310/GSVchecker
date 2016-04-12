#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
from os import listdir
import sys
import matplotlib.pyplot as plt
import seaborn as sns
from time import sleep


class NMEAData(object):
    u""" NMEAデータ確認用クラス

    指定ｳれたNORMALディレクトリ内のNMEAデータからSN等を算出する
    """

    def __init__(self):
        pass

    def concat_trip(self, path):
        u""" 各ファイルをtrip idごとにまとめる

        Args:
            path: sd root path

        Returns:
            dict_trip: tripIDごとにファイルをまとめたdict
                 * key1: tripID, value(list): 対応tripIDのファイルフルパス
        """

        path += "\\SYSTEM\\NMEA\\NORMAL\\"
        files = listdir(path)
        files.sort()
        dict_trip = {}

        for file in files:
            file = path + file
            with open(file, "r") as f:
                key = f.readline().split(",")[-1]
                if key not in dict_trip:
                    dict_trip[key] = list()
                dict_trip[key].append(file)

        return dict_trip

    def check(self, dict_trip):
        u""" tripIDごとのTTFF,SN等を調べる

        Args:
            dict_trip: self.concat_trip()で得れるdict

        Returns:
            trip: tripIDごとのチェック結果dict
                 * key1: tripID, value(list): 対応tripIDのチェック結果dict
                    * key1: "ttff"
                    * key2: "ttffnmea"
                    * key3: "sn", value(list): SNリスト
                        * key1:"time"
                        * key2:"num"
                        * key3:"sn"
        """

        data = dict()
        trip = dict()

        for k, v in dict_trip.items():
            data[k] = self.__get_lines(v)

        for k, v in data.items():
            pack = list()
            p = list()
            r = re.compile("^\$GPRMC")
            for d in v:
                if r.search(d) and len(p) > 0:
                    pack.append(p[:])
                    p.clear()
                p.append(d)
            trip[k] = self.__check_trip(pack)
        return (trip)

    def __check_trip(self, pack):
        trip = {"ttff": "", "ttffnmea": "", "sn": []}

        for cnt, p in enumerate(pack):
            stnum = list()
            snlist = list()
            sn_dict = dict((x, list()) for x in ["time", "num", "sn"])

            for s in p:
                sentence = s.replace("*", ",").split(",")

                if sentence[0] == "$GPRMC":
                    stnum.clear()
                    if sentence[2] == 'A' and sentence[3]:
                        for i in range(0, 4, 2):
                            sn_dict["time"] += sentence[1][i:i+2] + ':'
                        sn_dict["time"] += sentence[1][4:6] + "(+UTC0) - "
                        for i in range(0, 4, 2):
                            sn_dict["time"] += sentence[9][i:i+2] + '/'
                        sn_dict["time"] += sentence[9][4:6]
                        sn_dict["time"] = ''.join(sn_dict["time"])

                        if not trip["ttff"]:
                            trip["ttff"] = str(int(cnt/2))
                            trip["ttffnmea"] = sn_dict["time"]

                elif trip["ttff"] and sentence[0] == "$GPGSA":
                    if sentence[2] != 1:
                        stnum = sentence[3:3+12]
                    while "" in stnum:
                        del stnum[stnum.index("")]

                elif trip["ttff"] and len(stnum) and sentence[0] == "$GPGSV":
                    for pos in range(4, len(sentence), 4):
                        if sentence[pos] in stnum:
                            snlist.append(sentence[pos+3])

            if snlist:
                sn_dict["num"] = len(stnum)
                sn_dict["sn"] = self.__average_sn(snlist)
                trip["sn"].append(sn_dict)
        return trip

    def __average_sn(self, snlist):
        sn = ""
        try:
            sn = sum(list(map(int, snlist))) / len(snlist)
        except Exception as e:
            warning(e)

        return sn

    def __get_lines(self, files):
        lines = list()
        r = re.compile("^\$GP")
        for file in files:
            with open(file, "r") as f:
                for l in f:
                    if r.search(l):
                        lines.append(l)
        return lines


def warning(*objs):
    print("WARNING: ", *objs, file=sys.stderr)

if __name__ == '__main__':
    warning("this file is not entry point !!")
    sleep(5)
