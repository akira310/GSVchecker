# -*- mode: python -*-

block_cipher = None


a = Analysis(['main.py'],
             pathex=['E:\\dev\\src\\gitlab.com\\akira310\\GSVchecker'],
             binaries=None,
             datas=[
                 ('C:\\Anaconda3\\envs\\pyinstall\\Library\\bin\\mkl_avx.dll','.'),
                 ('C:\\Anaconda3\\envs\\pyinstall\\Library\\bin\\mkl_def.dll','.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='gsvchecker',
          debug=False,
          strip=False,
          upx=True,
          console=True )
