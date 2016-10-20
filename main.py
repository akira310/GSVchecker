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

        self._text = QtGui.QTextEdit()
        self._table = QtGui.QTableWidget()
        self._label = ["time", "num(use/all)"]
        self._tableBtn = list()
        self._create()

    def closeEvent(self, event):
        u""" closeボタン押下時の処理 """

        sys.stdout = None
        sys.stderr = None

    def _create(self):
        self._create_menu()
        self._create_log_area()
        self._create_table_area()
        self.setGeometry(100, 100, 750, 500)
        self.show()

    def _create_menu(self):
        openFile = QtGui.QAction(
                    QtGui.QApplication.style()
                    .standardIcon(QtGui.QStyle.SP_FileDialogStart),
                    'Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open Dir')
        openFile.triggered.connect(self._open)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFile)

    def _create_log_area(self):
        self.top_dock = QtGui.QDockWidget("log", self)
        self.top_dock.setFixedHeight(100)
        self.top_dock.setWidget(self._text)
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea, self.top_dock)

        self._text.setReadOnly(True)
        sys.stdout = GuiLogger(self._text, sys.stdout)
        sys.stderr = GuiLogger(self._text, sys.stderr, QtGui.QColor("red"))

        self._text.setTextColor(QtGui.QColor("blue"))
        self._text.setText(self._get_readme())

    def _create_table_area(self):
        self._table.setRowCount(0)
        self._table.setColumnWidth(3, 250)
        self._table.setColumnCount(len(self._label))
        self._table.setHorizontalHeaderLabels(self._label)
        self._table.verticalHeader().setVisible(False)
        self.setCentralWidget(self._table)

    def _open(self):
        path = QtGui.QFileDialog.getExistingDirectory(self, 'Open Dir', '.')
        self._text.clear()
        nmea = nmea_parse.NMEAParser()
        trip = dict()
        print(path)
        for tid, files in nmea.concat_trip(path).items():
            for f in files:
                parsed = nmea.parse(f)
                trip[tid] = parsed if tid not in trip else trip[tid] + parsed

        self._show_table(trip)

    def _str_datetime(self, rmc):
        return ("{}:{}".format(rmc.datestamp, rmc.timestamp))

    def _show_table(self, trip):
        self._table.clear()
        self._table.setRowCount(0)
        row = 0
        svlist = list()
        sumlist = list()

        for i, (tid, gps) in enumerate(trip.items()):
            self._table.insertRow(row)

            chkbox = QtGui.QTableWidgetItem()
            chkbox.setFlags(
                    QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            chkbox.setCheckState(QtCore.Qt.Unchecked)
            self._table.setItem(row, 0, chkbox)
            self._table.itemClicked.connect(self._item_clicked)

            self._table.setItem(row, 1, QtGui.QTableWidgetItem())
            btnstr = "{}({}/{}): {} - {}".format(
                    tid, i+1, len(trip),
                    self._str_datetime(gps[0]["RMC"]),
                    self._str_datetime(gps[-1]["RMC"]))
            btn = QtGui.QPushButton(btnstr)
            self._table.setCellWidget(row, 1, btn)
            self._table.setSpan(row, 1, 1, 2)

            graph = nmea_graph.NMEAGraph(tid, gps)
            btn.clicked.connect(graph.draw)
            self._tableBtn.append([btn, graph])
            btnrow = row

            row += 1
            for j in range(len(gps)):
                if j > 0 \
                   and gps[j]["RMC"].timestamp == gps[j-1]["RMC"].timestamp \
                   and gps[j]["RMC"].datestamp == gps[j-1]["RMC"].datestamp:
                    continue

                self._table.insertRow(row)
                self._table.setItem(row, 0,
                        QtGui.QTableWidgetItem(self._str_datetime(gps[j]["RMC"])))
                self._table.setItem(row, 1, QtGui.QTableWidgetItem(str(len(gps[j]["GSV"]["sv"]))))

                for sv in gps[j]["GSV"]["sv"]:
                    if not sv["no"].isdigit() or not sv["sn"]:
                        continue

                    if sv["no"] not in svlist:
                        svlist.append(sv["no"])
                        sumlist.append(0)
                        self._table.insertColumn(self._table.columnCount())

                    sumlist[svlist.index(sv["no"])] += int(sv["sn"]) if sv["sn"] else 0
                    self._table.setItem(row, svlist.index(sv["no"])+len(self._label),
                                        QtGui.QTableWidgetItem(sv["sn"]))
                    self._table.hideRow(row)

                if "GSA" in gps[j]:
                    for used in gps[j]["GSA"]["sv"]:
                        item = self._table.item(row, svlist.index(used)+len(self._label))
                        if item:
                            item.setBackgroundColor(QtGui.QColor("green"))

                row += 1
            self._table.setSpan(btnrow, 1, 1, self._table.columnCount()-1)
            self._table.setHorizontalHeaderLabels(self._label+svlist)

    def _item_clicked(self, item):
        row = item.row() + 1
        while row < self._table.rowCount() and self._table.item(row, 0).text():
            if item.checkState() == QtCore.Qt.Checked:
                self._table.showRow(row)
            else:
                self._table.hideRow(row)
            row += 1

    def _get_readme(self):
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
