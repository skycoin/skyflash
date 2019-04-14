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

import platform
import os

# Linux build
if platform.system() == "Linux":
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
            icon='skyflash/data/skyflash.png')

if platform.system() == "Windows":
    exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          exclude_binaries=False,
          name='skyflash-gui',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          icon='skyflash/data/skyflash.png')
