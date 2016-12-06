#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import logging
import logging.config
from PyQt4 import QtCore
from PyQt4 import QtGui
import nmea_parse  # my module
import nmea_graph  # my module


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
        self._thr = {"sn": 15, "el": 5}
        self._show = {"avrg": True, "pos": True, "gsamode": True}
        self._menuobj = {}
        self._create()

    def closeEvent(self, event):
        u""" closeボタン押下時の処理 """

        sys.stdout = None
        sys.stderr = None

    def _create(self):
        self._create_menu()
        self._create_log_area()
        self._create_table_area()
        self.setGeometry(100, 100, 1000, 750)
        self.show()

    def _create_menu(self):
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(self._create_menu_fileopen())

        editMenu = menubar.addMenu('&Edit')
        threshMenu = editMenu.addMenu('Set Thresh')
        threshMenu.addAction(self._create_threshmenu("sn"))
        threshMenu.addAction(self._create_threshmenu("el"))
        showMenu = editMenu.addMenu('Show graph')
        showMenu.addAction(self._create_showmenu("gsamode"))
        showMenu.addAction(self._create_showmenu("avrg"))
        showMenu.addAction(self._create_showmenu("pos"))

    def _create_menu_fileopen(self):
        menu = QtGui.QAction(
                QtGui.QApplication.style().standardIcon(QtGui.QStyle.SP_FileDialogStart),
                'Open', self)
        menu.setShortcut('Ctrl+O')
        menu.setStatusTip('Open Dir')
        menu.triggered.connect(self._open)

        return menu

    def _create_threshmenu(self, key):
        a = {"sn": {"menu": "C/N Thresh", "tip": "Set C/N Thresh"},
             "el": {"menu": "Elevation Thresh", "tip": "Set elevation Thresh"}}
        if key in a:
            menu = QtGui.QAction(a[key]["menu"], self)
            menu.setStatusTip(a[key]["tip"])
            menu.triggered.connect(lambda: self._set_thresh(key))
            return menu
        return None

    def _create_showmenu(self, key):
        a = {"avrg": {"menu": "Show average", "tip": "Show avereage"},
             "pos": {"menu": "Show position", "tip": "Show position"},
             "gsamode": {"menu": "Use GSA", "tip": "Use GSA"}}
        if key in a:
            menu = QtGui.QAction(a[key]["menu"], self, checkable=True)
            menu.setStatusTip(a[key]["tip"])
            menu.triggered.connect(lambda: self._set_show(key))
            menu.setChecked(self._show[key])
            self._menuobj[key] = menu
            return menu
        return None

    def _open(self):
        path = QtGui.QFileDialog.getExistingDirectory(self, 'Open Dir', '.')
        self._text.clear()
        nmea = nmea_parse.NMEAParser()
        trip = dict()
        print(path)
        for tid, files in nmea.concat_trip(path).items():
            trip[tid] = {"fname": [], "gps": []}
            for f in files:
                parsed = nmea.parse(f)
                trip[tid]["gps"] += parsed
                trip[tid]["fname"].append(f)

        self._show_table(trip)

    def _set_thresh(self, key):
        a = {"sn": {"title": "Input", "str": "Set SN thresh (dB)",
                    "min": 0, "max": 100, "step": 1},
             "el": {"title": "Input", "str": "Set elevation thresh (deg)",
                    "min": 0, "max": 90, "step": 1}}
        thr, ok = QtGui.QInputDialog.getInt(self, a[key]["title"], a[key]["str"], value=self._thr[key],
                                            min=a[key]["min"], max=a[key]["max"], step=a[key]["step"])
        if ok:
            self._thr[key] = thr

    def _set_show(self, key):
        self._show[key] = self._menuobj[key].isChecked()

    def _create_log_area(self):
        self.top_dock = QtGui.QDockWidget("log", self)
        self.top_dock.setFixedHeight(100)
        self.top_dock.setWidget(self._text)
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea, self.top_dock)

        self._text.setReadOnly(True)
        sys.stdout = GuiLogger(self._text, sys.stdout)
        sys.stderr = GuiLogger(self._text, sys.stderr, QtGui.QColor("red"))

        self._text.setTextColor(QtGui.QColor("blue"))
        readme = \
            "\n==========================================================\n" +\
            " SDカードデータのrootディレクトリを指定してください" +\
            "\n==========================================================\n\n"
        self._text.setText(readme)

    def _create_table_area(self):
        self._label = ["time", "sv num"]
        self._labelwidth = [170, 60]
        self._table.setRowCount(0)
        self._table.setColumnCount(len(self._label))
        self._table.setHorizontalHeaderLabels(self._label)
        for i, w in enumerate(self._labelwidth):
            self._table.setColumnWidth(i, w)
        self._table.verticalHeader().setVisible(False)
        self.setCentralWidget(self._table)

    @staticmethod
    def _str_datetime(rmc):
        return "{} {}".format(rmc.datestamp, rmc.timestamp) if rmc.timestamp else "----"

    def _show_table(self, trip):
        self._create_table_area()
        self._table.setRowCount(0)
        row = 0
        svlist = list()
        btnrow = list()

        for (tid, parsed) in sorted(trip.items(), key=lambda x: x[1]["fname"][0]):
            gps = parsed["gps"]
            self._table.insertRow(row)

            chkbox = QtGui.QTableWidgetItem()
            chkbox.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            chkbox.setCheckState(QtCore.Qt.Unchecked)
            self._table.setItem(row, 0, chkbox)
            self._table.itemClicked.connect(self._item_clicked)

            self._table.setItem(row, 1, QtGui.QTableWidgetItem())
            self._table.setCellWidget(row, 1, self._create_graphbtn(tid, parsed))
            self._table.setSpan(row, 1, 1, 2)
            btnrow.append(row)
            row += 1

            for gpsone in gps:
                self._table.insertRow(row)
                self._table.setItem(row, 0,
                                    QtGui.QTableWidgetItem(self._str_datetime(gpsone["RMC"])))
                if "GSV" in gpsone:
                    self._table.setItem(row, 1,
                                        QtGui.QTableWidgetItem(
                                            "{}{}".format(str(len(gpsone["GSV"]["sv"])), gpsone["RMC"].status)))

                    for sv in gpsone["GSV"]["sv"]:
                        if not sv["no"]:
                            continue

                        if sv["no"] not in svlist:
                            svlist.append(sv["no"])
                            self._table.insertColumn(self._table.columnCount())
                            self._table.setColumnWidth(self._table.columnCount()-1, 40)

                        self._table.setItem(row, svlist.index(sv["no"])+len(self._label),
                                            QtGui.QTableWidgetItem("{}".format(sv["sn"] if sv["sn"] else "-")))

                if "GSA" in gpsone:
                    for used in gpsone["GSA"]["sv"]:
                        item = self._table.item(row, svlist.index(used)+len(self._label))
                        if item:
                            item.setBackgroundColor(QtGui.QColor("cyan"))

                self._table.hideRow(row)
                row += 1

        self._table.setHorizontalHeaderLabels(self._label+svlist)
        for row in btnrow:
            self._table.setSpan(row, 1, 1, self._table.columnCount()-1)

    def _create_graphbtn(self, tid, parsed):
        fname = lambda s: os.path.splitext(os.path.basename(s))[0]
        text = fname(parsed["fname"][0])
        if len(parsed["fname"]) > 1:
            text += " - " + fname(parsed["fname"][-1])
        btn = QtGui.QPushButton(text)
        btn.setStyleSheet("Text-align:left")

        graph = nmea_graph.NMEAGraph(tid, parsed["gps"])
        btn.clicked.connect(lambda: graph.draw(self._thr, self._show))
        self._tableBtn.append([btn, graph])

        return btn


    def _item_clicked(self, item):
        row = item.row() + 1
        while row < self._table.rowCount() and self._table.item(row, 0).text():
            if item.checkState() == QtCore.Qt.Checked:
                self._table.showRow(row)
            else:
                self._table.hideRow(row)
            row += 1


def main():
    app = QtGui.QApplication(sys.argv)
    ex = MyGui()
    logging.config.fileConfig('./logging.cfg', disable_existing_loggers=False)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
