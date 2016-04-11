#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import os
import matplotlib.pyplot as plt
import seaborn as sns


class NMEAData(object):

    def __init__(self):
        pass

    def concat_trip(self, path):
        path += "\\SYSTEM\\NMEA\\NORMAL\\"
        files = os.listdir(path)
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
        data = {}
        for k, v in dict_trip.items():
            data[k] = self.__get_lines(v)

        for k, v in data.items():
            print("trip:", k)
            pack = list()
            p = list()
            r = re.compile("^\$GPRMC")
            for d in v:
                if r.search(d) and len(p) > 0:
                    pack.append(p[:])
                    p.clear()
                p.append(d)
            self.__show_data(pack)

    def __show_data(self, pack):
        ttff = ""
        ttffnmea = ""

        for i, p in enumerate(pack):
            stnum = list()
            snlist = list()
            sn_dict = dict((x, list()) for x in ["time", "num", "sn"])
            rmc = p[0].split(",")
            if rmc[0] == "$GPRMC":
                stnum.clear()
                if rmc[2] == 'A' and rmc[3] and not ttff:
                    sn_dict["time"] = rmc[1] + "-" + rmc[9]
                    ttff = str(int(i/2))
                    ttffnmea = sn_dict["time"]
                    print("ttff: {indx}(s) {t}" .format(
                        indx=ttff, t=ttffnmea))
            if ttff:
                for s in p:
                    sentence = s.replace("*", ",").split(",")

                    if sentence[0] == "$GPGSA":
                        if sentence[2] != 1:
                            stnum = sentence[3:3+12]
                        while "" in stnum:
                            del stnum[stnum.index("")]

                    if sentence[0] == "$GPGSV" and len(stnum) > 0:
                        pos = 4
                        while(pos < len(sentence)):
                            if sentence[pos] in stnum:
                                snlist.append(sentence[pos+3])
                            pos += 4

                if snlist:
                    sn_dict["num"] = len(stnum)
                    sn_dict["sn"] = self.__average_sn(snlist)
                    print("num[{n}]: SN: {sn}".format(
                        n=sn_dict["num"], sn=sn_dict["sn"]))
                    # print("time:{t} num[{n}]: SN: {sn}".format(
                    #     n=sn_dict["num"], sn=sn_dict["sn"], t=sn_dict["time"]))

    def __average_sn(self, snlist):
        sn = ""
        try:
            sn = str(sum(list(map(int, snlist))) / len(snlist))
        except Exception as e:
            print(e)

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

if __name__ == '__main__':
    pass
