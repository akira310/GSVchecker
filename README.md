# check-NMEA-SN
GPS受信性能評価用C/Nチェック

更新日: 2016/12/13


## 概要
* RMCセンテンス間を１つのまとまりとして,GSVの各衛星情報をパースする
* GSVの情報をグラフ化する

## 機能
* 時刻毎の各衛星C/Nパース(Table化)
* C/Nパース結果のグラフ化
    * 各衛星毎C/Nの平均値算出
    * 全衛星中C/N上位3衛星分の平均値算出
    * 衛星位置表示(GSA情報がある場合のみ)
    * 各衛星毎のC/N時間推移
    * 下記フィルタリング
        * C/N閾値未満を非表示
        * 仰角閾値未満を非表示
        * 指定日時間の衛星情報のみ表示

## 対象ファイルフォーマット

| 必須センテンス | 推奨センテンス |
|----------------|----------------|
| RMC, GSV       | GSA            |

```
# ファイルデータサンプル
$GPRMC,053439.00,A,3540.40016,N,13921.78944,E,0.000,,011216,,,A*72
$GPGGA,053439.00,3540.40016,N,13921.78944,E,1,08,1.36,106.8,M,38.9,M,,*5A
$GPGSA,A,3,13,20,15,05,193,30,02,28,,,,,2.13,1.36,1.64*34
$GPGSV,3,1,12,02,15,168,20,04,50,040,27,05,55,097,29,13,68,009,22*76
$GPGSV,3,2,12,15,58,288,26,18,05,303,,20,61,322,22,21,26,310,18*72
$GPGSV,3,3,12,28,11,080,24,29,08,247,,30,20,043,26,193,86,159,18*4F
```

## exe化
* cx_freezeでは,includesの追加やTCL_LIBRARY,TK_LIBRARYのpath設定を反映しても
  うまくいかなかったので,諦めました
* pyinstallerでのexe化+動作は確認済です.

```
####################################
# pyinstallerを使ったexe化サンプル
####################################

# setuptoolsは2016/12/12時点では最新だとうまくいかなかったのでpyinstaller用の環境を構築する
# (https://github.com/pyinstaller/pyinstaller/issues/1773)
conda create -n pyinstall python setuptools=19.2 pyqt=4.11.4 qt=4.8.7 matplotlib seaborn
activate pyinstall

# pynmea2はcondaからのinstallでconflictが発生したので悩まずpipで入れる
pip install pynmea2
conda install --channel https://conda.anaconda.org/silg2 pyinstaller

# exeファイル生成
pyinstaller gsvchecker.spec --onefile

# 2016/12/12時点ではloggerは使えていないのでcopyしなくても実害はない
cp logging.cfg dist
```


## 注意事項
* 時刻情報が取れていないデータの場合の挙動は検証していない

## TODO
* loggingの出力をGUIのログエリアにも表示する
* 処理の最適化
    * for文回し過ぎでデータ生成まで時間がかかっている


