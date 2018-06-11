#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import re
import os
import copy
import pandas as pd
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
            i+1: total file 数
            dict_trip: tripIDごとにファイルをまとめたdict
                 * key1: tripID, value(list): 対応tripIDのファイルフルパス
        """

        if "SYSTEM" in os.listdir(path):
            path = os.path.join(path, "SYSTEM", "NMEA", "NORMAL")
        files = os.listdir(path)
        files.sort()
        dict_trip = {}
        dummy = 0

        for i, file in enumerate(files):
            file = os.path.join(path, file)
            if os.path.isfile(file):
                with open(file, "r") as f:
                    print("open:", file)
                    line = f.readline().split(",")
                    if len(line) >= 2 and "GTRIP" in line[0]:
                        key = line[1].rstrip()
                    else:
                        key = "dummy{}".format(dummy)
                        dummy += 1

                    if key not in dict_trip:
                        dict_trip[key] = list()
                    dict_trip[key].append(file)
            else:
                sys.stderr.write("{} is not file path".format(file))

        return i+1, dict_trip

    def parse(self, file):
        u""" NMEAセンテンスをパースする

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
        dflist = list()
        newnmea = True
        with open(file, "r") as f:
            r = re.compile("(^\$..)(RMC|GGA|GSA|GSV)(.*)")
            for line in f:
                match = r.match(line)
                if match:
                    toker = match.group(2)
                    if toker == "RMC":
                        rmc = self._parse_nmea(line)
                        if len(parsed) and rmc.timestamp == parsed[-1]["RMC"].timestamp:
                            newnmea = False
                            p = copy.deepcopy(parsed[-1])
                            d = dict()
                            # add common data.
                            d["cmn"] = {
                                    "date": p["RMC"].datestamp,
                                    "time": p["RMC"].timestamp,
                                    "status": p["RMC"].status,
                                    "svnum": 0,
                                    }

                            # add every SV data
                            if "GSV" in p:
                                d["cmn"]["svnum"] = p["GSV"]["num_sv_in_view"]
                                for sv in p["GSV"]["sv"]:
                                    d[sv["no"]] = copy.deepcopy(sv)
                                    d[sv["no"]].pop("no")
                                    d[sv["no"]]["use"] = False
                            if "GSA" in p:
                                for used in p["GSA"]["sv"]:
                                    d[used]["use"] = True

                            dflist.append(pd.DataFrame.from_dict(d))
                        else:
                            newnmea = True
                            parsed.append(dict())
                            parsed[-1][toker] = rmc
                    elif newnmea:
                        if toker == "GSV" and "GSV" in parsed[-1]:
                            parsed[-1]["GSV"]["sv"] += self._parse_nmea(line)["sv"]
                        else:
                            parsed[-1][toker] = self._parse_nmea(line)

        return parsed, dflist

    def _parse_nmea(self, sentence):
        try:
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
                gsv["num_sv_in_view"] = msg.num_sv_in_view
                svlist = list()
                for i in range(1, 5):
                    sv = dict()
                    sv["no"] = eval("msg.sv_prn_num_"+str(i))
                    sv["el"] = eval("msg.elevation_deg_"+str(i))
                    sv["az"] = eval("msg.azimuth_"+str(i))
                    sv["sn"] = eval("msg.snr_"+str(i))
                    if sv["no"]:
                        svlist.append(sv)
                gsv["sv"] = svlist
                nmea = gsv
            elif msg.sentence_type == "GGA":
                gga = dict()
                gga["hdop"] = msg.horizontal_dil
                nmea = gga

        except pynmea2.nmea.ChecksumError:
            tmp = sentence.split(",")
            tmp[-1] = str(pynmea2.nmea.NMEASentence.checksum(sentence))
            nmea = pynmea2.parse(",".join(tmp))

        return nmea


if __name__ == '__main__':
    print("WARN: this file is not entry point !!", file=sys.stderr)
    sleep(5)
