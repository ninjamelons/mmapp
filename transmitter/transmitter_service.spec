# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['transmitter_service.py'],
             pathex=['D:\\idk\\DFM\\venv\\Lib\\site-packages\\zmq', 'D:\\idk\\DFM\\mmapp\\transmitter'],
             binaries=[],
             datas=[('raman_service.sqlite', '.'),
                    ('.\pyzmq.libs\*', 'pyzmq.libs/')],
             hiddenimports=[
                'uvicorn.logging',
                'uvicorn.loops',
                'uvicorn.loops.auto',
                'uvicorn.protocols',
                'uvicorn.protocols.http',
                'uvicorn.protocols.http.auto',
                'uvicorn.protocols.websockets',
                'uvicorn.protocols.websockets.auto',
                'uvicorn.lifespan',
                'uvicorn.lifespan.on',
                'zmq.backend', 'zmq.backend.cython', 'zmq.backend.cffi', 'zmq.error', 'zmq.sugar', 'zmq.utils'],
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
          [],
          exclude_binaries=True,
          name='transmitter_service',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='transmitter_service')
