# Resolución centralizada de la ruta de config.json.
#
# En desarrollo la configuración sigue junto al código (App/config.json),
# como siempre. En la aplicación empaquetada (PyInstaller fija el
# atributo `sys.frozen`) el directorio de instalación puede ser de solo
# lectura y, en onefile, volátil: por eso la configuración del usuario
# se guarda en %APPDATA%\OrganizadorArchivos\config.json.
#
# Migración: si al resolver la ruta empaquetada la configuración nueva
# no existe pero sí existe una antigua (junto al ejecutable o la de
# desarrollo), se COPIA la antigua a la nueva. Nunca se borra el
# original: migrar es copiar, y la configuración del usuario no se pierde.
#
# Puntos de entrada:
#   ruta_config()                     → ruta activa según el entorno
#   resolver_ruta_config(...)         → resolución parametrizable (pruebas)
#   rutas_legado(frozen, base, raiz)  → candidatas a config antigua

import os
import shutil
import sys
from pathlib import Path

# Nombre de la carpeta de datos del usuario en %APPDATA%.
CARPETA_DATOS = "OrganizadorArchivos"

# Nombre del archivo de configuración.
NOMBRE_CONFIG = "config.json"


def _appdata() -> Path:
    """Directorio base de datos del usuario (%APPDATA%).

    Si la variable de entorno no existe (situación rara en Windows),
    se recurre a ~/AppData/Roaming para no devolver nunca None.
    """

    return Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")


def raiz_desarrollo() -> Path:
    """Carpeta App/ del proyecto (donde vive config.json en desarrollo)."""

    return Path(__file__).resolve().parent.parent


def ruta_desarrollo() -> Path:
    return raiz_desarrollo() / NOMBRE_CONFIG


def ruta_empaquetada(base=None) -> Path:
    """Configuración de la app empaquetada: %APPDATA%/OrganizadorArchivos.

    `base` permite inyectar otro directorio base (uso de pruebas).
    """

    return Path(base or _appdata()) / CARPETA_DATOS / NOMBRE_CONFIG


def rutas_legado(frozen=False, base=None) -> list[Path]:
    """Ubicaciones donde podría existir una configuración antigua.

    - Empaquetado: junto al ejecutable (onedir) y, por compatibilidad
      con ejecuciones anteriores de la versión de desarrollo, la
      App/config.json del proyecto en la misma máquina.
    - Desarrollo: solo la propia App/config.json (la activa).
    """

    candidatas = []

    if frozen:
        candidatas.append(Path(sys.executable).resolve().parent / NOMBRE_CONFIG)
        candidatas.append(ruta_desarrollo())
    else:
        candidatas.append(ruta_desarrollo())

    # Sin duplicados conservando el orden.
    unicas = []
    for candidata in candidatas:
        if candidata not in unicas:
            unicas.append(candidata)

    return unicas


def migrar_config(ruta_antigua: Path, ruta_nueva: Path) -> bool:
    """Copia una configuración antigua a la nueva si procede.

    Copia solo si la nueva no existe y la antigua sí. La antigua se
    conserva siempre (nunca se borra ni se renombra). Devuelve True si
    hubo copia. Un fallo de disco no se propaga: la app puede seguir
    creando una configuración por defecto.
    """

    ruta_antigua = Path(ruta_antigua)
    ruta_nueva = Path(ruta_nueva)

    if ruta_nueva.exists() or not ruta_antigua.exists():
        return False

    try:
        ruta_nueva.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ruta_antigua, ruta_nueva)
        return True

    except OSError:
        return False


def resolver_ruta_config(frozen=False, base=None, legado=None) -> Path:
    """Resuelve la ruta activa de config.json y migra si hace falta.

    - frozen=False (desarrollo): App/config.json, sin crear nada.
    - frozen=True (empaquetada): crea %APPDATA%/OrganizadorArchivos/
      si no existe, y copia una configuración antigua si la hay.
    - `legado`: candidatas alternativas de configuración antigua
      (uso de pruebas; None usa las estándar).
    """

    if not frozen:
        return ruta_desarrollo()

    ruta = ruta_empaquetada(base)

    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

    candidatas = rutas_legado(frozen=True, base=base) if legado is None else legado

    for candidata in candidatas:
        if migrar_config(candidata, ruta):
            break

    return ruta


def ruta_config() -> Path:
    """Ruta activa de config.json según el entorno de ejecución."""

    return resolver_ruta_config(frozen=bool(getattr(sys, "frozen", False)))
