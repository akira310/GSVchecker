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

    def pack(self, files):
        u""" NMEAセンテンスをRMC毎にまとめる

        Args:
            files: nmea files

        Returns:
            packed: RMC毎にまとめたセンテンスlist
        """

        packed = list()
        packing = list()
        r = re.compile("^\$GPRMC")

        for d in self._get_gpslines(files):
            if r.search(d) and len(packing) > 0:
                packed.append(packing[:])
                packing.clear()
            packing.append(d)

        return (packed[1::2])

    def parse_packdata(self, packed):
        u""" tripIDごとのTTFF,SN等を調べる

        Args:
            packed: self.pack()で得れるlist

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
                            * key2:"sn"     S/N
                            * key3:"fix"    fix or not
        """

        return (self._check_trip(packed))

    def _check_trip(self, pack):
        gsv = list()
        fixed = {"ttff": "", "ttffnmea": "", "sn": []}

        for cnt, p in enumerate(pack):
            used = list()
            usedsn = list()
            gsvsn = list()
            fix_dict = dict((x, list()) for x in ["time", "num", "used", "sn"])
            gsv_dict = dict((x, list()) for x in ["num", "sn", "fix"])

            for s in p:
                nmea = s.replace("*", ",").split(",")
                num = 0

                if nmea[0] == "$GPRMC":
                    used.clear()
                    time = ""
                    gsv_dict["fix"] = 0
                    if nmea[1] and nmea[9]:
                        for i in range(0, 4, 2):
                            time += nmea[1][i:i+2] + ':'
                        time += nmea[1][4:6] + "(+UTC0) - "
                        for i in range(0, 4, 2):
                            time += nmea[9][i:i+2] + '/'
                        time += nmea[9][4:6]
                        time = ''.join(time)

                    if nmea[2] == 'A' and nmea[3]:
                        gsv_dict["fix"] = 1
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
                gsv_dict["sn"] = self._average_sn(gsvsn)
                gsv.append(gsv_dict)

            if len(used):
                fix_dict["used"] = len(used)
                fix_dict["sn"] = self._average_sn(usedsn)
                fixed["sn"].append(fix_dict)

        return {"fixed": fixed, "gsv": gsv}

    def _average_sn(self, baselist):
        avrg = 0
        snlist = [x for x in baselist if x]
        if len(snlist):
            try:
                avrg = sum(list(map(int, snlist))) // len(snlist)
            except Exception as e:
                self._log.warn(e)

        return avrg

    def _get_gpslines(self, files):
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
