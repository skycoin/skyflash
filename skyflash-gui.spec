#!/usr/bin/env python3

import os
import sys

block_cipher = None

# datas for all os
extrafiles = [
                ('skyflash/data/skyflash.qml', '.'),
                ('skyflash/data/skyflash.png', '.'),
            ]

# windows specific ones
if 'nt' in os.name:
    extrafiles.append(('win-build/dist/windows/flash.exe', '.'))

# posix (linux/macos)
if 'posix' in os.name:
    extrafiles.append(('posix-build/dist/pypv', '.'))

a = Analysis(['skyflash-gui.py'],
             binaries=[],
             datas=extrafiles,
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

# Linux & macos build
if 'posix' in os.name:
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
          icon='skyflash/data/skyflash.ico'
          )

    # macos app recipe
    if 'darwin' in sys.platform:
        app = BUNDLE(exe,
                    name='skyflash-gui.app',
                    icon='skyflash/data/skyflash.ico',
                    bundle_identifier='net.skycoin.skyflash'
                    )

if 'nt' in os.name:
    exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='skyflash-gui',
          bootloader_ignore_signals=False,
          strip=False,
          console=False,
          debug=False,
          icon='skyflash/data/skyflash.ico',
          uac_admin=True,
          )

    coll = COLLECT(exe,
           a.binaries,
           a.zipfiles,
           a.datas,
           strip=False,
           upx=False,
           name='skyflash-gui'
           )
