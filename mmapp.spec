# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['mmapp.py'],
             pathex=['D:\\idk\\DFM\\venv\\Lib\\site-packages\\zmq', 'D:\\idk\\DFM\\mmapp\\transmitter',
                '/home/ninjamelons/Desktop/DFM/mmapp'],
             binaries=[],
             datas=[('./transmitter/raman_service.sqlite', './transmitter/'),
                    ('D:/idk/DFM/venv38/Lib/site-packages/dash_bootstrap_components/', './dash_bootstrap_components/'),
                    ('D:/idk/DFM/venv38/Lib/site-packages/dash_core_components/', './dash_core_components/'),
                    ('D:/idk/DFM/venv38/Lib/site-packages/dash_html_components/', './dash_html_components/'),
                    ('D:/idk/DFM/venv38/Lib/site-packages/plotly/', './plotly/'),
                    ('D:/idk/DFM/venv38/Lib/site-packages/dash_renderer/', './dash_renderer/'),
                    ('D:/idk/DFM/venv38/Lib/site-packages/pyzmq.libs/', './pyzmq.libs/'),],
             hiddenimports=[
                'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.protocols', 'uvicorn.protocols.http',
                'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto',
                'uvicorn.lifespan', 'uvicorn.lifespan.on',
                'zmq.backend', 'zmq.backend.cython', 'zmq.backend.cffi', 'zmq.error', 'zmq.sugar', 'zmq.utils',
                'sklearn.utils._weight_vector', 'plotly.validators.scatter', 'plotly.validators.surface', 'plotly.validators.surface.colorbar'],
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
          name='mmapp',
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
               name='mmapp')