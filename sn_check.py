#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt4 import QtGui
import matplotlib.pyplot as plt
import seaborn as sns
from math import *
import re
import os
import datetime


class Logger(object):
    def __init__(self, editor, out=None, color=None):
        self.editor = editor    # 結果出力用エディタ
        self.out = out       # 標準出力・標準エラーなどの出力オブジェクト
        # 結果出力時の色(Noneが指定されている場合、エディタの現在の色を入れる)
        if not color:
            self.color = editor.textColor()
        else:
            self.color = color

    def write(self, message):
        # カーソルを文末に移動。
        self.editor.moveCursor(QtGui.QTextCursor.End)

        # color変数に値があれば、元カラーを残してからテキストのカラーを
        # 変更する。
        self.editor.setTextColor(self.color)

        # 文末にテキストを追加。
        self.editor.insertPlainText(message)

        # 出力オブジェクトが指定されている場合、そのオブジェクトにmessageを
        # 書き出す。
        if self.out:
            self.out.write(message)


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


class MyGui(QtGui.QMainWindow):

    def __init__(self):
        super(MyGui, self).__init__()

        self.__create()

    def closeEvent(self, event):
        u"""
        closeボタン押下時の処理
        """
        sys.stdout = None
        sys.stderr = None

    def __create(self):
        self.textEdit = QtGui.QTextEdit()
        self.setCentralWidget(self.textEdit)
        self.textEdit.setReadOnly(True)
        self.textEdit.setTextColor(QtGui.QColor("blue"))
        self.textEdit.setText(self.__get_readme())
        self.textEdit.setTextColor(QtGui.QColor("black"))

        sys.stdout = Logger(self.textEdit, sys.stdout)
        sys.stderr = Logger(self.textEdit, sys.stderr, QtGui.QColor(255, 0, 0))

        openFile = QtGui.QAction(
                    QtGui.QApplication.style()
                    .standardIcon(QtGui.QStyle.SP_FileDialogStart),
                    'Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open Dir')
        openFile.triggered.connect(self.__open)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFile)

        self.setGeometry(100, 100, 750, 300)
        self.setWindowTitle('File dialog')
        self.show()

    def __get_readme(self):
        return \
            "\n==========================================================\n" +\
            " SDカードデータのrootディレクトリを指定してください" +\
            "\n==========================================================\n\n"

    def __open(self):
        path = QtGui.QFileDialog.getExistingDirectory(self, 'Open Dir', '.')
        # print("dir path: {0}".format(path))
        self.__draw(path)

    def __draw(self, path):
        nmea = NMEAData(path)
        nmea.concat_trip()
        nmea.check_sn()


def main():
    app = QtGui.QApplication(sys.argv)
    ex = MyGui()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
