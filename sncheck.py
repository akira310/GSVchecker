#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import os


class NMEAData(object):

    def __init__(self, path):
        self.__path = path + "\\SYSTEM\\NMEA\\NORMAL\\"
        self.__trip = {}
        self.__data = {}

    def concat_trip(self):
        self.__files = os.listdir(self.__path)
        self.__files.sort()

        for file in self.__files:
            file = self.__path + file
            with open(file, "r") as f:
                key = f.readline().split(",")[-1]
                if key not in self.__trip:
                    self.__trip[key] = list()
                    self.__data[key] = list()
                self.__trip[key].append(file)

        for k, v in self.__trip.items():
            self.__data[k] = self.__get_lines(v)
        # print(self.__data)

    def check_sn(self):
        for k, v in self.__data.items():
            print("trip:", k)
            self.__check_sn(v)

    def __check_sn(self, data):
        pack = list()
        p = list()
        r = re.compile("^\$GPRMC")
        for d in data:
            if r.search(d) and len(p) > 0:
                pack.append(p[:])
                p.clear()
            p.append(d)
        self.__show_data(pack)

    def __show_data(self, pack):
        ttff = ""
        ttffdate = ""

        for i, p in enumerate(pack):
            stnum = list()
            snlist = list()
            rmc = p[0].split(",")
            if rmc[0] == "$GPRMC":
                stnum.clear()
                if rmc[2] == 'A' and rmc[3] and not ttff:
                    ttff = rmc[1]
                    ttffdate = rmc[9]
                    print("[{indx}] ttff: {date}-{time} " .format(
                         indx=int(i/2), date=ttffdate, time=ttff))
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
                    print("stnum[{num}]: SN: {sn}".format(
                        num=len(stnum), sn=self.__conv_sn(snlist)))

    def __conv_sn(self, snlist):
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

    def __show_ttff(self, tid, files):
        ttff = ""
        ttffdate = ""
        for file in files:
            with open(file, "r") as f:
                for line in f:
                    sentence = line.split(",")
                    if sentence[0] == "$GPRMC":
                        if sentence[2] == 'A' and sentence[3] and not ttff:
                            ttff = sentence[1]
                            ttffdate = sentence[9]

        print("tid", tid, "ttffdate:", ttffdate, "ttff:", ttff)


if __name__ == '__main__':
    pass
