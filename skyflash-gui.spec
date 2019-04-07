#!/usr/bin/env python3

block_cipher = None

a = Analysis(['skyflash-gui.py'],
             binaries=[],
             datas=[
                 ('skyflash/data/skyflash.qml', '.'),
                 ('skyflash/data/skyflash.png', '.'),
            ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='skyflash-gui',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          runtime_tmpdir=None,
          console=False,
          uac_admin=True,
          uac_uiaccess=True,
          manifest='skyflash-gui.exe.manifest',
          icon='skyflash/data/skyflash.ico')
