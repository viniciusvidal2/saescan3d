# saescan3d.spec
block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('modules', 'modules'),
        ('windows', 'windows'),
        ('resources', 'resources'),
        ('dependencies/meshroom', 'dependencies/meshroom'),
    ],
    hiddenimports=[
        'numpy', 'open3d', 'utm', 'rasterio', 'rasterio.sample', 'rasterio.vrt', 'rasterio._features',
        'pyvista', 'pyvistaqt', 'PySide6',
        'vtkmodules', 'vtkmodules.all', 'vtkmodules.util', 'vtkmodules.util.data_model', 'vtkmodules.util.execution_model'
    ],
    excludes=[
        'PyQt5', 'PyQt5.sip', 'PyQt6', 'PySide2',
        'tkinter'
    ],
    hookspath=['.'],
    runtime_hooks=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    exclude_binaries=True,
    name='SAEScan3D',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='resources/saescan3d.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='saescan3d'
)
