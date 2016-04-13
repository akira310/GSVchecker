#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import re
from os import listdir
from time import sleep


class NMEAParser(object):
    u""" NMEAパーサークラス

    指定ｳれたNORMALディレクトリ内のNMEAデータからSN等を算出する
    """

    def __init__(self, isAll=0):
        self.__isAll = isAll

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
                key = f.readline().split(",")[-1].rstrip()
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
                        * key1:"num"    受信衛星数
                        * key2:"time"   日時
                        * key3:"used"   使用衛星数
                        * key4:"sn"     S/N
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
        all_gsv = list()
        fixed = {"ttff": "", "ttffnmea": "", "sn": []}

        for cnt, p in enumerate(pack):
            used = list()
            sn = list()
            sn_dict = dict((x, list()) for x in ["time", "num", "used", "sn"])

            for s in p:
                nmea = s.replace("*", ",").split(",")

                if nmea[0] == "$GPRMC":
                    used.clear()
                    time = ""
                    if nmea[1] and nmea[9]:
                        for i in range(0, 4, 2):
                            time += nmea[1][i:i+2] + ':'
                        time += nmea[1][4:6] + "(+UTC0) - "
                        for i in range(0, 4, 2):
                            time += nmea[9][i:i+2] + '/'
                        time += nmea[9][4:6]
                        time = ''.join(time)

                    if nmea[2] == 'A' and nmea[3]:
                        sn_dict["time"] = time

                        if not fixed["ttff"]:
                            fixed["ttff"] = str(int(cnt/2))
                            fixed["ttffnmea"] = sn_dict["time"]

                elif nmea[0] == "$GPGSA" and (fixed["ttff"] or self.__isAll):
                    used = nmea[3:3+12] if nmea[2] != 1 else []
                    while "" in used:
                        del used[used.index("")]

                elif nmea[0] == "$GPGSV" and (fixed["ttff"] and len(used)):
                    sn_dict["num"] = int(nmea[3])
                    for pos in range(4, len(nmea), 4):
                        sn.append(nmea[pos+3]) if nmea[pos] in used else ""

            if sn:
                sn_dict["used"] = len(used)
                sn_dict["sn"] = self.__average_sn(sn)
                fixed["sn"].append(sn_dict)
        return fixed

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
                    lines.append(l) if r.search(l) else ""
        return lines


def warning(*objs):
    print("WARNING: ", *objs, file=sys.stderr)

if __name__ == '__main__':
    warning("this file is not entry point !!")
    sleep(5)
