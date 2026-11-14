# Carga y guardado de la configuración en config.json.

# La configuración describe las categorías, sus extensiones, la subcarpeta
# de destino de cada una y las preferencias generales. Si el archivo no
# existe, se genera uno con los valores por defecto en la primera ejecución.

import json
from pathlib import Path

from .excepciones import ErrorConfiguracion
from .models import Ajustes, Categoria, ComportamientoDesconocidos

# Nombre reservado: lo gestiona el motor para los archivos sin categoría.
CATEGORIA_RESERVADA = "Otros"

# Idiomas admitidos por la interfaz (clave en config.json "idioma").
IDIOMAS_VALIDOS = ("es", "en", "ja")
IDIOMA_POR_DEFECTO = "es"

# Categorías iniciales, tomadas del script original (Organizador/main.py).
CATEGORIAS_POR_DEFECTO = [
    {
        "nombre": "Imagenes",
        "extensiones": [".jpg", ".jpeg", ".png", ".webp", ".gif"],
    },
    {
        "nombre": "Documentos",
        "extensiones": [".pdf", ".txt", ".docx", ".csv"],
    },
    {
        "nombre": "Música",
        "extensiones": [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"],
    },
    {
        "nombre": "Vídeos",
        "extensiones": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm"],
    },
    {
        "nombre": "Comprimidos",
        "extensiones": [".zip", ".rar", ".7z", ".tar", ".gz"],
    },
    {
        "nombre": "Programación",
        "extensiones": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".cs", ".php"],
    },
    {
        "nombre": "Ejecutables",
        "extensiones": [".exe", ".msi", ".msix", ".bat", ".cmd"],
    },
    {
        "nombre": "Fuentes",
        "extensiones": [".ttf", ".otf", ".woff", ".woff2"],
    },
    {
        "nombre": "Datos",
        "extensiones": [".sql", ".xml", ".yaml", ".yml", ".log", ".json"],
    },
    {
        "nombre": "Presentaciones",
        "extensiones": [".ppt", ".pptx", ".odp"],
    },
    {
        "nombre": "Hojas de cálculo",
        "extensiones": [".xls", ".xlsx", ".ods"],
    },
]

ARCHIVOS_IGNORADOS_POR_DEFECTO = ["desktop.ini", "Thumbs.db"]

# Preferencias de la navegación lateral.
NAVEGACION_AUTOMATICA_POR_DEFECTO = True
RETARDO_MINIMO_MS = 100
RETARDO_MAXIMO_MS = 2000
RETARDO_POR_DEFECTO_MS = 400


def ajustes_por_defecto() -> Ajustes:
    """Devuelve la configuración por defecto de la aplicación."""

    return Ajustes(
        categorias=[Categoria(**datos) for datos in CATEGORIAS_POR_DEFECTO],
        unknown_files=ComportamientoDesconocidos.OTROS,
        archivos_ignorados=list(ARCHIVOS_IGNORADOS_POR_DEFECTO),
        navegacion_automatica=NAVEGACION_AUTOMATICA_POR_DEFECTO,
        retardo_navegacion_ms=RETARDO_POR_DEFECTO_MS,
        idioma=IDIOMA_POR_DEFECTO,
    )


def cargar_config(ruta) -> Ajustes:
    """Carga la configuración desde `ruta` (config.json).

    Si el archivo no existe, se crea con los valores por defecto y se
    devuelve esa configuración.
    """

    ruta = Path(ruta)

    if not ruta.exists():
        ajustes = ajustes_por_defecto()
        guardar_config(ruta, ajustes)
        return ajustes

    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ErrorConfiguracion(
            "config.lectura",
            "No se pudo leer la configuración {ruta}: {detalle}",
            ruta=ruta,
            detalle=error,
        ) from error

    return _config_desde_dict(datos)


def _config_a_dict(ajustes: Ajustes) -> dict:
    """Convierte una configuración en memoria a su forma de diccionario."""

    return {
        "categorias": [
            {
                "nombre": categoria.nombre,
                "extensiones": list(categoria.extensiones),
                "destino": categoria.destino,
            }
            for categoria in ajustes.categorias
        ],
        "preferencias": {
            "unknown_files": ajustes.unknown_files.value,
            "archivos_ignorados": list(ajustes.archivos_ignorados),
            "navegacion_automatica": ajustes.navegacion_automatica,
            "retardo_navegacion_ms": ajustes.retardo_navegacion_ms,
            "idioma": ajustes.idioma,
        },
    }


def validar_config(ajustes: Ajustes) -> Ajustes:
    """Valida una configuración en memoria sin leer ni escribir el disco.

    Aplica exactamente las mismas reglas que la carga (nombres y
    extensiones únicos, nombre «Otros» reservado, preferencias válidas)
    y devuelve la configuración normalizada. Lanza ValueError si es
    inválida.
    """

    return _config_desde_dict(_config_a_dict(ajustes))


def guardar_config(ruta, ajustes: Ajustes) -> None:
    """Guarda la configuración en `ruta` con formato legible."""

    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    ruta.write_text(
        json.dumps(_config_a_dict(ajustes), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _config_desde_dict(datos) -> Ajustes:
    """Valida un diccionario leído de config.json y lo convierte en Ajustes.

    Los errores se lanzan como ErrorConfiguracion (subclase de
    ValueError) con la clave de traducción del mensaje y sus
    parámetros: str(error) mantiene el texto en español de siempre.
    """

    if not isinstance(datos, dict):
        raise ErrorConfiguracion(
            "config.no_objeto", "La configuración debe ser un objeto JSON."
        )

    categorias_datos = datos.get("categorias")
    if not isinstance(categorias_datos, list):
        raise ErrorConfiguracion(
            "config.categorias_no_lista",
            "La clave 'categorias' debe ser una lista.",
        )

    preferencias = datos.get("preferencias", {})
    if not isinstance(preferencias, dict):
        raise ErrorConfiguracion(
            "config.preferencias_no_objeto",
            "La clave 'preferencias' debe ser un objeto JSON.",
        )

    valor_desconocidos = preferencias.get(
        "unknown_files", ComportamientoDesconocidos.OTROS.value
    )

    try:
        desconocidos = ComportamientoDesconocidos(valor_desconocidos)
    except ValueError:
        valores_validos = ", ".join(item.value for item in ComportamientoDesconocidos)
        raise ErrorConfiguracion(
            "config.desconocidos_invalido",
            "'unknown_files' no es válido: {valor!r}. "
            "Valores admitidos: {valores}.",
            valor=valor_desconocidos,
            valores=valores_validos,
        ) from None

    archivos_ignorados = preferencias.get("archivos_ignorados", [])
    if not isinstance(archivos_ignorados, list) or not all(
        isinstance(nombre, str) for nombre in archivos_ignorados
    ):
        raise ErrorConfiguracion(
            "config.ignorados_no_lista",
            "'archivos_ignorados' debe ser una lista de textos.",
        )

    navegacion_automatica = preferencias.get(
        "navegacion_automatica", NAVEGACION_AUTOMATICA_POR_DEFECTO
    )
    if not isinstance(navegacion_automatica, bool):
        raise ErrorConfiguracion(
            "config.navegacion_no_bool",
            "'navegacion_automatica' debe ser un booleano: {valor!r}.",
            valor=navegacion_automatica,
        )

    retardo_navegacion_ms = preferencias.get(
        "retardo_navegacion_ms", RETARDO_POR_DEFECTO_MS
    )
    if not isinstance(retardo_navegacion_ms, int) or isinstance(
        retardo_navegacion_ms, bool
    ):
        raise ErrorConfiguracion(
            "config.retardo_no_entero",
            "'retardo_navegacion_ms' debe ser un número entero: {valor!r}.",
            valor=retardo_navegacion_ms,
        )

    if not RETARDO_MINIMO_MS <= retardo_navegacion_ms <= RETARDO_MAXIMO_MS:
        raise ErrorConfiguracion(
            "config.retardo_fuera_rango",
            "'retardo_navegacion_ms' fuera de rango: {valor}. "
            "Debe estar entre {minimo} y {maximo} ms.",
            valor=retardo_navegacion_ms,
            minimo=RETARDO_MINIMO_MS,
            maximo=RETARDO_MAXIMO_MS,
        )

    idioma = preferencias.get("idioma", IDIOMA_POR_DEFECTO)
    if idioma not in IDIOMAS_VALIDOS:
        raise ErrorConfiguracion(
            "config.idioma_invalido",
            "'idioma' no es válido: {valor!r}. Valores admitidos: {valores}.",
            valor=idioma,
            valores=", ".join(IDIOMAS_VALIDOS),
        )

    categorias: list[Categoria] = []
    nombres_vistos = set()
    extensiones_vistas = set()

    for datos_categoria in categorias_datos:
        if not isinstance(datos_categoria, dict):
            raise ErrorConfiguracion(
                "config.categoria_no_objeto",
                "Cada categoría debe ser un objeto JSON.",
            )

        nombre = datos_categoria.get("nombre")
        extensiones = datos_categoria.get("extensiones")

        if not isinstance(nombre, str) or not nombre.strip():
            raise ErrorConfiguracion(
                "config.nombre_vacio", "Toda categoría necesita un nombre."
            )

        nombre = nombre.strip()

        if not isinstance(extensiones, list) or not all(
            isinstance(ext, str) for ext in extensiones
        ):
            raise ErrorConfiguracion(
                "config.extensiones_no_lista",
                "Las extensiones de '{nombre}' deben ser una lista de textos.",
                nombre=nombre,
            )

        if nombre == CATEGORIA_RESERVADA:
            raise ErrorConfiguracion(
                "config.nombre_reservado",
                "El nombre '{nombre}' está reservado para los archivos "
                "sin categoría. No puede usarse en la configuración.",
                nombre=CATEGORIA_RESERVADA,
            )

        if nombre.lower() in nombres_vistos:
            raise ErrorConfiguracion(
                "config.categoria_duplicada",
                "Categoría duplicada: '{nombre}'.",
                nombre=nombre,
            )

        destino = datos_categoria.get("destino", "")
        if not isinstance(destino, str):
            raise ErrorConfiguracion(
                "config.destino_no_texto",
                "El destino de '{nombre}' debe ser un texto.",
                nombre=nombre,
            )

        categoria = Categoria(
            nombre=nombre,
            extensiones=[ext.strip() for ext in extensiones if ext.strip()],
            destino=destino.strip(),
        )

        duplicadas = [
            ext for ext in categoria.extensiones if ext in extensiones_vistas
        ]
        if duplicadas:
            raise ErrorConfiguracion(
                "config.extensiones_repetidas",
                "Extensiones repetidas en '{nombre}': {extensiones}.",
                nombre=nombre,
                extensiones=", ".join(duplicadas),
            )

        nombres_vistos.add(nombre.lower())
        extensiones_vistas.update(categoria.extensiones)
        categorias.append(categoria)

    return Ajustes(
        categorias=categorias,
        unknown_files=desconocidos,
        archivos_ignorados=[nombre for nombre in archivos_ignorados if nombre],
        navegacion_automatica=navegacion_automatica,
        retardo_navegacion_ms=retardo_navegacion_ms,
        idioma=idioma,
    )
