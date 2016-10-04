#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt4 import QtCore
from PyQt4 import QtGui
import nmea_parse  # my module
import nmea_graph  # my module
import logging
import logging.config


class GuiLogger(object):
    u""" GUIへのログ表示用クラス

    GUIへ標準出力、エラー出力をパイプする
    """

    def __init__(self, editor, out=None, color=None):
        self.editor = editor    # 結果出力用エディタ
        self.out = out       # 標準出力・標準エラーなどの出力オブジェクト
        # 結果出力時の色(Noneが指定されている場合、エディタの現在の色を入れる)
        self.color = editor.textColor() if not color else color

    def write(self, message):
        self.editor.moveCursor(QtGui.QTextCursor.End)
        self.editor.setTextColor(self.color)
        self.editor.insertPlainText(message)

        # 出力オブジェクトが指定されている場合、そのオブジェクトにmessageを書き出す
        self.out.write(message) if self.out else ""


class MyGui(QtGui.QMainWindow):
    u""" GUI用クラス

    ディレクトリの指定や結果出力を行う
    """

    def __init__(self):
        super(MyGui, self).__init__()

        self.__text = QtGui.QTextEdit()
        self.__table = QtGui.QTableWidget()
        self.__tableBtn = list()
        self.__create()

    def closeEvent(self, event):
        u""" closeボタン押下時の処理 """

        sys.stdout = None
        sys.stderr = None

    def __create(self):
        self.__create_menu()
        self.__create_log_area()
        self.__create_table_area()
        self.setGeometry(100, 100, 750, 500)
        self.show()

    def __create_menu(self):
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

    def __create_log_area(self):
        self.top_dock = QtGui.QDockWidget("log", self)
        self.top_dock.setFixedHeight(100)
        self.top_dock.setWidget(self.__text)
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea, self.top_dock)

        self.__text.setReadOnly(True)
        sys.stdout = GuiLogger(self.__text, sys.stdout)
        sys.stderr = GuiLogger(self.__text, sys.stderr, QtGui.QColor("red"))

        self.__text.setTextColor(QtGui.QColor("blue"))
        self.__text.setText(self.__get_readme())

    def __create_table_area(self):
        self.__table.setRowCount(0)
        self.__table.setColumnCount(4)
        self.__table.setColumnWidth(3, 250)
        self.__table.setHorizontalHeaderLabels(
                ["st_num", "usednum", "SN", "time-date"])
        self.__table.verticalHeader().setVisible(False)
        self.setCentralWidget(self.__table)

    def __open(self):
        path = QtGui.QFileDialog.getExistingDirectory(self, 'Open Dir', '.')
        self.__text.clear()
        nmea = nmea_parse.NMEAParser()
        trip = nmea.check(nmea.concat_trip(path))
        self.__show_table(trip, self.__table)

    def __show_table(self, trip, table):
        table.clear()
        tableItem = list()
        self.__table.setRowCount(0)
        self.__table.setHorizontalHeaderLabels(
                ["st_num", "usednum", "S/N", "time-date"])
        # table.setSortingEnabled(True)
        row = 0

        for i, (tid, v) in enumerate(trip.items()):
            fixed = v["fixed"]
            print("==========================================")
            tableItem.append(QtGui.QTableWidgetItem())

            # TODO: implementaiton.  using __insert_row() and lambda
            table.insertRow(row)
            table.setItem(row, 0, tableItem[-1])
            btnstr = "tid({i}/{n}): {id}  TTFF: {ttff}(s)  {t}".format(
                      i=i+1, n=len(trip), id=tid,
                      ttff=fixed["ttff"], t=fixed["ttffnmea"])
            btn = QtGui.QPushButton(btnstr)
            table.setCellWidget(row, 0, btn)
            graph = nmea_graph.NMEAGraph(tid, fixed, v["gsv"])
            btn.clicked.connect(graph.draw)
            table.setSpan(row, 0, 1, table.columnCount())
            self.__tableBtn.append([btn, graph])
            row += 1
            print(btnstr)
            print("------------------------------------------")

            for sn in fixed["sn"]:
                table.insertRow(row)
                table.setItem(row, 0, QtGui.QTableWidgetItem("{0[num]:02d}"
                                                             .format(sn)))
                table.setItem(row, 1, QtGui.QTableWidgetItem("{0[used]:02d}"
                                                             .format(sn)))
                table.setItem(row, 2, QtGui.QTableWidgetItem("{0[sn]:02.0f}"
                                                             .format(sn)))
                table.setItem(row, 3, QtGui.QTableWidgetItem(sn["time"]))
                row += 1
                print("SN[{0[used]:02d}]: {0[sn]:02.0f}\t{0[time]}"
                      .format(sn))

            table.insertRow(row)
            table.setItem(row, 0, QtGui.QTableWidgetItem(" "))
            table.setSpan(row, 0, 1, table.columnCount())
            row += 1

    def __insert_row(self, table, row, func):
        table.insertRow(row)
        func
        return row+1

    def __get_readme(self):
        return \
            "\n==========================================================\n" +\
            " SDカードデータのrootディレクトリを指定してください" +\
            "\n==========================================================\n\n"


def main():
    app = QtGui.QApplication(sys.argv)
    ex = MyGui()
    logging.config.fileConfig('./logging.cfg', disable_existing_loggers=False)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
