# Internacionalización mediante diccionarios centralizados.
#
# Se descartó Qt Linguist/QTranslator: exige toolchain (lupdate/
# lrelease), archivos .qm binarios y complicaría el cambio de idioma
# en vivo. Con tres idiomas y un catálogo acotado, los diccionarios
# Python son más simples, testeables con unittest y permiten aplicar
# el idioma sin reiniciar.
#
# API:
#   tr(clave, **params) → texto traducido e interpolado
#   cambiar_idioma(codigo) → activa el idioma ("es"/"en"/"ja")
#   idioma_actual() → código activo
#   IDIOMAS → {"es": "Español", "en": "English", "ja": "日本語"}
#
# Reglas de traducción:
#   · Nombres de archivo, rutas, extensiones y texto del usuario NO
#     se traducen: los mensajes los interpolan sin alterarlos.
#   · Si una clave falta en el idioma activo, se usa el español
#     (la paridad de claves la exigen las pruebas, así que esto solo
#     protege ante errores de programación).
#   · Clave desconocida: KeyError claro, nunca texto mezclado.

from pathlib import Path

from organizador.config import IDIOMAS_VALIDOS

from gui.i18n import textos_es, textos_en, textos_ja

# Etiqueta visible de cada idioma, en su propio idioma (no se traduce).
IDIOMAS = {
    "es": "Español",
    "en": "English",
    "ja": "日本語",
}

IDIOMA_POR_DEFECTO = "es"

_DICCIONARIOS = {
    "es": textos_es.TEXTOS,
    "en": textos_en.TEXTOS,
    "ja": textos_ja.TEXTOS,
}

_idioma = IDIOMA_POR_DEFECTO


def idioma_actual() -> str:
    return _idioma


def cambiar_idioma(codigo: str):
    """Activa un idioma. Lanza ValueError si el código no es válido."""

    global _idioma

    if codigo not in IDIOMAS_VALIDOS:
        raise ValueError(
            f"Idioma no admitido: {codigo!r}. "
            f"Valores admitidos: {', '.join(IDIOMAS_VALIDOS)}."
        )

    _idioma = codigo


def textos_de_idioma(codigo: str) -> dict:
    """Diccionario de un idioma concreto (uso de pruebas y paridad)."""

    if codigo not in IDIOMAS_VALIDOS:
        raise ValueError(f"Idioma no admitido: {codigo!r}.")

    return _DICCIONARIOS[codigo]


def tr(clave: str, **parametros) -> str:
    """Traduce una clave y sustituye los parámetros {nombre}."""

    texto = _DICCIONARIOS[_idioma].get(clave)

    if texto is None:
        texto = textos_es.TEXTOS.get(clave)

    if texto is None:
        raise KeyError(
            f"Traducción desconocida: '{clave}' "
            f"(idioma: {_idioma})."
        )

    return texto.format(**parametros) if parametros else texto


def cargar_idioma_de_disco(ruta) -> str:
    """Lee solo el campo "idioma" de un config.json existente.

    Devuelve el código válido o el default sin lanzar errores ni
    crear el archivo (pensado para el arranque de la aplicación).
    """

    import json

    ruta = Path(ruta)

    if not ruta.exists():
        return IDIOMA_POR_DEFECTO

    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return IDIOMA_POR_DEFECTO

    if not isinstance(datos, dict):
        return IDIOMA_POR_DEFECTO

    preferencias = datos.get("preferencias")
    if not isinstance(preferencias, dict):
        return IDIOMA_POR_DEFECTO

    codigo = preferencias.get("idioma")
    if codigo in IDIOMAS_VALIDOS:
        return codigo

    return IDIOMA_POR_DEFECTO
