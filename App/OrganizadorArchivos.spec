# Spec de PyInstaller para el Organizador de archivos (Windows).
#
# Empaquetado: onedir + windowed (sin consola).
#   .venv\Scripts\python.exe -m PyInstaller --noconfirm OrganizadorArchivos.spec
#
# Resultado: dist\OrganizadorArchivos\OrganizadorArchivos.exe
# (distribuir la carpeta completa comprimida en ZIP).
#
# Decisiones:
#   · onedir: arranque rápido, menos falsos positivos de antivirus y
#     compatible con la configuración del usuario en %APPDATA%
#     (ver gui/rutas.py; onefile dejaría la config en una carpeta
#     temporal que se borra en cada ejecución).
#   · console=False: aplicación de escritorio, sin ventana de consola.
#   · datas: los 6 SVG de gui/recursos (y el icono de la app si existe).
#     Quedan en gui/recursos dentro del bundle, la misma ruta relativa
#     que resuelve main_window.CARPETA_RECURSOS.
#   · excludes: solo módulos Qt que la aplicación no usa y que nada
#     carga implícitamente. NO se excluyen QtSvg (iconos SVG),
#     QtNetwork ni QtConcurrent: PySide6 los puede necesitar en tiempo
#     de ejecución.

# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

RAIZ = Path(SPECPATH)

# Icono del ejecutable. Si todavía no existe el archivo, se empaqueta
# sin icono: basta con colocar gui/recursos/icono_app.ico y repetir el
# build para activarlo.
ICONO = RAIZ / "gui" / "recursos" / "icono_app.ico"

# Módulos Qt y de la app que no deben entrar al bundle.
EXCLUDES = [
    # QtWebEngine (navegador embebido, cientos de MB).
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineQuick",
    # QtPdf.
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    # QML / Quick (la GUI es Widgets).
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuick3D",
    "PySide6.QtQuickWidgets",
    "PySide6.QtQuickControls2",
    # Add-ons claramente no usados.
    "PySide6.Qt3DCore",
    "PySide6.Qt3DRender",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DExtras",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtBluetooth",
    "PySide6.QtNfc",
    "PySide6.QtPositioning",
    "PySide6.QtSensors",
    "PySide6.QtSerialPort",
    "PySide6.QtSerialBus",
    "PySide6.QtSql",
    "PySide6.QtTest",
    "PySide6.QtTextToSpeech",
    "PySide6.QtWebChannel",
    "PySide6.QtWebSockets",
    "PySide6.QtRemoteObjects",
    "PySide6.QtDesigner",
    # Pruebas y desarrollo: nunca van en el ejecutable.
    "tests",
    "pytest",
]

a = Analysis(
    [str(RAIZ / "main.py")],
    pathex=[str(RAIZ)],
    binaries=[],
    datas=[(str(RAIZ / "gui" / "recursos"), "gui/recursos")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="OrganizadorArchivos",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(ICONO) if ICONO.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="OrganizadorArchivos",
)
