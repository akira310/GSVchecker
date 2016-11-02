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
        self._tableBtn = list()
        self._thr = 15
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

        EditMenu = menubar.addMenu('&Edit')
        EditMenu.addAction(self._create_menu_setthresh())

    def _create_menu_fileopen(self):
        menu = QtGui.QAction(
                    QtGui.QApplication.style()
                    .standardIcon(QtGui.QStyle.SP_FileDialogStart),
                    'Open', self)
        menu.setShortcut('Ctrl+O')
        menu.setStatusTip('Open Dir')
        menu.triggered.connect(self._open)

        return menu

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

    def _create_menu_setthresh(self):
        menu = QtGui.QAction(
                    QtGui.QApplication.style()
                    .standardIcon(QtGui.QStyle.SP_DialogApplyButton),
                    'Thresh', self)
        # menu.setShortcut('Ctrl+T')
        menu.setStatusTip('Set Thresh')
        menu.triggered.connect(self._setthresh)

        return menu

    def _setthresh(self):
        thr, ok = QtGui.QInputDialog.getInt(self, "Input", "Set SN thresh (dB)",
                                            value=self._thr, min=0, max=100, step=1)
        if ok:
            self._thr = thr

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
        self._label = ["time", "sv num"]
        self._labelwidth = [170, 60]
        self._table.setRowCount(0)
        self._table.setColumnCount(len(self._label))
        self._table.setHorizontalHeaderLabels(self._label)
        for i,w in enumerate(self._labelwidth):
            self._table.setColumnWidth(i, w)
        self._table.verticalHeader().setVisible(False)
        self.setCentralWidget(self._table)

    def _str_datetime(self, rmc):
        return ("{}:{}".format(rmc.datestamp, rmc.timestamp))

    def _show_table(self, trip):
        self._create_table_area()
        self._table.setRowCount(0)
        row = 0
        svlist = list()

        for i, (tid, gps) in enumerate(trip.items()):
            self._table.insertRow(row)

            chkbox = QtGui.QTableWidgetItem()
            chkbox.setFlags(
                    QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            chkbox.setCheckState(QtCore.Qt.Unchecked)
            self._table.setItem(row, 0, chkbox)
            self._table.itemClicked.connect(self._item_clicked)

            self._table.setItem(row, 1, QtGui.QTableWidgetItem())
            self._table.setCellWidget(row, 1, self._create_graphbtn(tid, (i, len(trip)), gps))
            self._table.setSpan(row, 1, 1, 2)
            btnrow = row
            row += 1

            for j in range(len(gps)):
                if gps[j]["RMC"].timestamp == None:
                    continue

                if j > 0 \
                   and gps[j]["RMC"].timestamp == gps[j-1]["RMC"].timestamp \
                   and gps[j]["RMC"].datestamp == gps[j-1]["RMC"].datestamp:
                    continue

                self._table.insertRow(row)
                self._table.setItem(row, 0,
                        QtGui.QTableWidgetItem(self._str_datetime(gps[j]["RMC"])))
                if "GSV" in gps[j]:
                    self._table.setItem(row, 1, QtGui.QTableWidgetItem(str(len(gps[j]["GSV"]["sv"]))))

                    for sv in gps[j]["GSV"]["sv"]:
                        if not sv["no"]:
                            continue

                        if sv["no"] not in svlist:
                            svlist.append(sv["no"])
                            self._table.insertColumn(self._table.columnCount())
                            self._table.setColumnWidth(self._table.columnCount()-1, 40)

                        self._table.setItem(row, svlist.index(sv["no"])+len(self._label),
                                            QtGui.QTableWidgetItem("{}".format(sv["sn"] if sv["sn"] else "-")))

                if "GSA" in gps[j]:
                    for used in gps[j]["GSA"]["sv"]:
                        item = self._table.item(row, svlist.index(used)+len(self._label))
                        if item:
                            item.setBackgroundColor(QtGui.QColor("cyan"))

                self._table.hideRow(row)
                row += 1
            self._table.setSpan(btnrow, 1, 1, self._table.columnCount()-1)
            self._table.setHorizontalHeaderLabels(self._label+svlist)

    def _create_graphbtn(self, tid, tripnum, gps):
        text = "???"
        for i in range(len(gps)):
            if gps[i]["RMC"].timestamp != None:
                text = "{}({}/{}): {} - {}".format(
                        tid, tripnum[0]+1, tripnum[1],
                        self._str_datetime(gps[i]["RMC"]),
                        self._str_datetime(gps[-1]["RMC"]))
                break
        btn = QtGui.QPushButton(text)
        graph = nmea_graph.NMEAGraph(tid, gps)
        btn.clicked.connect(lambda: graph.draw(self._thr))
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
