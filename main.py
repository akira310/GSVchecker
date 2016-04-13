#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt4 import QtCore
from PyQt4 import QtGui
import sncheck  # my module


class Logger(object):
    u""" GUIへのログ表示用クラス

    GUIへ標準出力、エラー出力をパイプする
    """

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


class MyGui(QtGui.QMainWindow):
    u""" GUI用クラス

    ディレクトリの指定や結果出力を行う
    """

    def __init__(self):
        super(MyGui, self).__init__()

        self.__textEdit = QtGui.QTextEdit()
        self.__create()

    def __print(self, type, *objs):
        printtype = {
                "ERR": lambda *objs: print("ERROR: ", *objs, file=sys.stderr),
                "WARN": lambda *objs: print("WARN: ", *objs, file=sys.stderr),
                "INFO": lambda *objs: print(*objs, file=sys.stdout),
        }

        if type in printtype:
            printtype[type](*objs)
        else:
            print(*objs, file=sys.stdout)

    def closeEvent(self, event):
        u""" closeボタン押下時の処理 """

        sys.stdout = None
        sys.stderr = None

    def __create(self):
        self.setCentralWidget(self.__textEdit)
        self.__textEdit.setReadOnly(True)
        sys.stdout = Logger(self.__textEdit, sys.stdout)
        sys.stderr = Logger(self.__textEdit, sys.stderr, QtGui.QColor("red"))

        self.__textEdit.setTextColor(QtGui.QColor("blue"))
        self.__textEdit.setText(self.__get_readme())

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

        self.setGeometry(100, 100, 750, 500)
        self.setWindowTitle('File dialog')
        self.show()

    def __open(self):
        path = QtGui.QFileDialog.getExistingDirectory(self, 'Open Dir', '.')
        self.__textEdit.clear()
        nmea = sncheck.NMEAData()
        trip = nmea.check(nmea.concat_trip(path))
        self.__show_table(trip)

    def __show_table(self, trip):
        table = QtGui.QTableWidget()
        table.resize(700, 500)
        tableItem = list()
        table.setRowCount(0)
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["st_num", "SN", "time-date"])
        # table.setSortingEnabled(True)
        row = 0

        for tid, v in trip.items():
            self.__print("", "==========================================")
            tableItem.append(QtGui.QTableWidgetItem())

            table.insertRow(row)
            table.setItem(row, 0, tableItem[-1])
            btnstr = "tid: {id}  TTFF: {ttff}(s)  {t}".format(
                        id=tid, ttff=v["ttff"], t=v["ttffnmea"])
            table.setCellWidget(row, 0, QtGui.QPushButton(btnstr))
            table.setSpan(row, 0, 1, table.columnCount())
            row += 1
            self.__print("", btnstr)
            self.__print("", "------------------------------------------")

            for sn in v["sn"]:
                table.insertRow(row)
                table.setItem(row, 0, QtGui.QTableWidgetItem("{0:02d}".format(sn["num"])))
                table.setItem(row, 1, QtGui.QTableWidgetItem("{0:02.0f}".format(sn["sn"])))
                table.setItem(row, 2, QtGui.QTableWidgetItem(sn["time"]))
                row += 1

                self.__print("", "SN[{n:02d}]: {sn:02.0f}\t{time}" .format(
                            n=sn["num"], sn=sn["sn"], time=sn["time"]))

        self.setCentralWidget(table)
        self.__print("", "\nEND")

    def __get_readme(self):
        return \
            "\n==========================================================\n" +\
            " SDカードデータのrootディレクトリを指定してください" +\
            "\n==========================================================\n\n"


def main():
    app = QtGui.QApplication(sys.argv)
    ex = MyGui()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
