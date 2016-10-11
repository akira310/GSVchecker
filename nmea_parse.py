#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import re
import os
from time import sleep
import pynmea2
import logging


class NMEAParser(object):
    u""" NMEAパーサークラス

    指定ｳれたNORMALディレクトリ内のNMEAデータからSN等を算出する
    """

    def __init__(self):
        self._log = logging.getLogger(__name__)

    def concat_trip(self, path):
        u""" 各ファイルをtrip idごとにまとめる

        Args:
            path: sd root path

        Returns:
            dict_trip: tripIDごとにファイルをまとめたdict
                 * key1: tripID, value(list): 対応tripIDのファイルフルパス
        """

        path = os.path.join(path, "SYSTEM", "NMEA", "NORMAL")
        files = os.listdir(path)
        files.sort()
        dict_trip = {}

        for file in files:
            file = os.path.join(path, file)
            with open(file, "r") as f:
                key = f.readline().split(",")[-1].rstrip()
                if key not in dict_trip:
                    dict_trip[key] = list()
                dict_trip[key].append(file)

        return dict_trip

    def parse(self, file):
        u""" 各ファイルをtrip idごとにまとめる

        Args:
            path: sd root path

        Returns:
            parsed: 各秒ごとにセンテンスparse結果をまとめたdictのlist
                    * "RMC": pynmea2のparse結果そのまま
                    * "GSA": parse結果のdict
                        * "mode"   : mode (A/M)
                        * "fixtype": fix type (1:no,2:2D,3:3D)
                        * "pdop"   : pdop
                        * "hdop"   : hdop
                        * "vdop"   : vdop
                        * "sv"     : 使用中衛星番号のlist
                    * "GSV": parse結果のdict
                        * "num_sv_in_view": 取得衛星数
                        * "sv"            : 各衛星情報dictのlist
                            * "no": 衛星番号
                            * "el": 仰角
                            * "az": 方位角
                            * "sn": 受信強度
        """

        parsed = list()

        with open(file, "r") as f:
            r = re.compile("(^\$..)(RMC|GSA|GSV)(.*)")
            line = f.readline()

            while line:
                match = r.match(line)
                if match:
                    toker = match.group(2)
                    if toker == "RMC":
                        parsed.append(dict())
                        parsed[-1][toker] = self._parse_nmea(line)
                    elif toker == "GSV" and "GSV" in parsed[-1]:
                        parsed[-1]["GSV"]["sv"] += self._parse_nmea(line)["sv"]
                    else:
                        parsed[-1][toker] = self._parse_nmea(line)
                line = f.readline()

        return parsed

    def _parse_nmea(self, sentence):
        nmea = msg = pynmea2.parse(sentence)
        if msg.sentence_type == "GSA":
            gsa = dict()
            gsa["mode"] = msg.mode
            gsa["fixtype"] = msg.mode_fix_type
            gsa["pdop"] = msg.pdop
            gsa["hdop"] = msg.hdop
            gsa["vdop"] = msg.vdop
            svidlist = list()
            for i in range(1, 13):
                svid = eval("msg.sv_id{:02d}".format(i))
                if svid:
                    svidlist.append(svid)
                else:
                    break
            gsa["sv"] = svidlist
            nmea = gsa
        elif msg.sentence_type == "GSV":
            gsv = dict()
            gsv["in_view"] = msg.num_sv_in_view
            svlist = list()
            for i in range(1, 5):
                sv = dict()
                sv["no"] = eval("msg.sv_prn_num_"+str(i))
                sv["el"] = eval("msg.elevation_deg_"+str(i))
                sv["az"] = eval("msg.azimuth_"+str(i))
                sv["sn"] = eval("msg.snr_"+str(i))
                svlist.append(sv)
            gsv["sv"] = svlist
            nmea = gsv

        return nmea


if __name__ == '__main__':
    print("WARN: this file is not entry point !!", file=sys.stderr)
    sleep(5)
