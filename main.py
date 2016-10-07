#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt4 import QtCore
from PyQt4 import QtGui
import nmea_parse  # my module
import nmea_graph  # my module
import pynmea2
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
        self._table.setColumnCount(4)
        self._table.setColumnWidth(3, 250)
        self._table.setHorizontalHeaderLabels(
                ["st_num", "usednum", "SN", "time-date"])
        self._table.verticalHeader().setVisible(False)
        self.setCentralWidget(self._table)

    def _open(self):
        path = QtGui.QFileDialog.getExistingDirectory(self, 'Open Dir', '.')
        self._text.clear()
        nmea = nmea_parse.NMEAParser()
        trip = dict()
        print(path)
        for tid, files in nmea.concat_trip(path).items():
            packdata = nmea.pack(files)
            # trip[tid] = nmea.parse_packdata(packdata)
            # trip[tid] = nmea.parse_packdata2(packdata)
            trip[tid] = packdata

        # self._show_table(trip)
        self._show_table2(trip)

    def _show_table2(self, trip):
        for tid, packlist in trip.items():
            d2 = 0
            lost = 0
            gga = 0
            for pack in packlist:
                # print(pack)
                for p in pack:
                    if "GGA" in p:
                        msg = pynmea2.parse(p)
                        gga += 1
                        if int(msg.num_sats ) < 4:
                            # print(msg.num_sats, p)
                            d2 += 1

            num = len(packlist)/2
            fix = gga/2
            d2 /= 2
            lost = num - fix
            per = lambda x, y: x*100/y
            print("==== {:.2f}min 3d[{}]:{:.2f}% 2d[{}]:{:.2f}% lost[{}]:{:.2f}% ===="
                    .format(num/60, fix, per(fix, num)-per(d2, num), d2, per(d2, num), lost, per(lost, num)))

    def _show_table(self, trip):
        self._table.clear()
        self._table.setRowCount(0)
        self._table.setHorizontalHeaderLabels(
                ["st_num", "usednum", "S/N", "time-date"])
        # self._table.setSortingEnabled(True)
        row = 0

        for i, (tid, v) in enumerate(trip.items()):
            fixed = v["fixed"]
            print("==========================================")
            self._table.insertRow(row)
            chkbox = QtGui.QTableWidgetItem()
            chkbox.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            chkbox.setCheckState(QtCore.Qt.Unchecked)
            self._table.setItem(row, 0, chkbox)
            self._table.itemClicked.connect(self._item_clicked)

            self._table.setItem(row, 1, QtGui.QTableWidgetItem())
            btnstr = "tid({i}/{n}): {id}  TTFF: {ttff}(s)  {t}".format(
                      i=i+1, n=len(trip), id=tid,
                      ttff=fixed["ttff"], t=fixed["ttffnmea"])
            btn = QtGui.QPushButton(btnstr)
            self._table.setCellWidget(row, 1, btn)
            graph = nmea_graph.NMEAGraph(tid, fixed, v["gsv"])
            btn.clicked.connect(graph.draw)
            self._table.setSpan(row, 1, 1, self._table.columnCount()-1)
            self._tableBtn.append([btn, graph])
            row += 1
            print(btnstr)
            print("------------------------------------------")

            for sn in fixed["sn"]:
                self._table.insertRow(row)
                self._table.setItem(row, 0, QtGui.QTableWidgetItem("{0[num]:02d}"
                                                             .format(sn)))
                self._table.setItem(row, 1, QtGui.QTableWidgetItem("{0[used]:02d}"
                                                             .format(sn)))
                self._table.setItem(row, 2, QtGui.QTableWidgetItem("{0[sn]:02.0f}"
                                                             .format(sn)))
                self._table.setItem(row, 3, QtGui.QTableWidgetItem(sn["time"]))
                self._table.hideRow(row)
                row += 1
                print("SN[{0[used]:02d}]: {0[sn]:02.0f}\t{0[time]}"
                      .format(sn))

    def _item_clicked(self, item):
        row = item.row() + 1
        while row < self._table.rowCount() and self._table.item(row, 0).text():
            if item.checkState() == QtCore.Qt.Checked:
                self._table.showRow(row)
            else:
                self._table.hideRow(row)
            row+=1

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
