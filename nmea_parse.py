#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import re
from os import listdir
from time import sleep
import logging


class NMEAParser(object):
    u""" NMEAパーサークラス

    指定ｳれたNORMALディレクトリ内のNMEAデータからSN等を算出する
    """

    def __init__(self, isAll=0):
        pass
        self.__log = logging.getLogger(__name__)

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
                    * key1: "fixed"
                        * key1: "ttff"
                        * key2: "ttffnmea"
                        * key3: "sn", value(list): SNリスト
                            * key1:"num"    受信衛星数
                            * key2:"time"   日時
                            * key3:"used"   使用衛星数
                            * key4:"sn"     S/N
                    * key2: "gsv"
                            * key1:"num"    受信衛星数
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
        gsv = list()
        fixed = {"ttff": "", "ttffnmea": "", "sn": []}

        for cnt, p in enumerate(pack):
            used = list()
            usedsn = list()
            gsvsn = list()
            fix_dict = dict((x, list()) for x in ["time", "num", "used", "sn"])
            gsv_dict = dict((x, list()) for x in ["num", "sn"])

            for s in p:
                nmea = s.replace("*", ",").split(",")
                num = 0

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
                        fix_dict["time"] = time

                        if not fixed["ttff"]:
                            fixed["ttff"] = str(int(cnt/2))
                            fixed["ttffnmea"] = fix_dict["time"]

                elif nmea[0] == "$GPGSA" and fixed["ttff"]:
                    used = nmea[3:3+12] if nmea[2] != 1 else []
                    while "" in used:
                        del used[used.index("")]

                elif nmea[0] == "$GPGSV":
                    num = fix_dict["num"] = int(nmea[3])
                    try:
                        for i in range(4, len(nmea), 4):
                            usedsn.append(nmea[i+3]) if nmea[i] in used else ""
                            gsvsn.append(nmea[i+3]) if nmea[i] else ""
                    except Exception:
                        pass

            if num > 0:
                gsv_dict["num"] = num
                gsv_dict["sn"] = self.__average_sn(gsvsn)
                gsv.append(gsv_dict)

            if len(used):
                fix_dict["used"] = len(used)
                fix_dict["sn"] = self.__average_sn(usedsn)
                fixed["sn"].append(fix_dict)

        return {"fixed": fixed, "gsv": gsv}

    def __average_sn(self, baselist):
        avrg = 0
        snlist = [x for x in baselist if x]
        if len(snlist):
            try:
                avrg = sum(list(map(int, snlist))) // len(snlist)
            except Exception as e:
                self.__log.warn(e)

        return avrg

    def __get_lines(self, files):
        lines = list()
        r = re.compile("^\$GP")
        for file in files:
            with open(file, "r") as f:
                for l in f:
                    lines.append(l) if r.search(l) else ""
        return lines


if __name__ == '__main__':
    print("WARN: this file is not entry point !!", file=sys.stderr)
    sleep(5)
