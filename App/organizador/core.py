# Motor de organización: planificación y ejecución de movimientos.

# Lógica migrada y adaptada desde Organizador/main.py (script original,
# que se conserva sin cambios). El motor no depende de la interfaz:
# solo trabaja con rutas y configuración.

from pathlib import Path
import shutil

from .models import (
    Ajustes,
    ComportamientoDesconocidos,
    EstadoPlan,
    PlanArchivo,
    ResumenEjecucion,
)

# Carpeta de destino para los archivos sin categoría conocida.
CARPETA_OTROS = "Otros"


def planificar(origen: Path, destino: Path, ajustes: Ajustes) -> list[PlanArchivo]:
    """Analiza la carpeta de origen y devuelve el plan de organización.

    No mueve ningún archivo: solo calcula, para cada archivo, su categoría,
    su estado y el destino propuesto. Conflitos de nombre se resuelven
    proponiendo un nombre alternativo (`nombre_1.ext`, `nombre_2.ext`...),
    igual que hacía el script original.

    - `origen`: carpeta cuyos archivos se van a organizar.
    - `destino`: carpeta raíz donde se crearán las subcarpetas de categoría.
    - `ajustes`: configuración (categorías, desconocidos, ignorados).
    """

    origen = Path(origen)
    destino = Path(destino)

    mapa_extensiones = _mapear_extensiones(ajustes)
    ignorados = {nombre.lower() for nombre in ajustes.archivos_ignorados}
    ocupados: set[Path] = set()

    plan: list[PlanArchivo] = []

    for elemento in sorted(origen.iterdir()):
        if not elemento.is_file():
            continue

        # Archivos en la lista de exclusión: aparecen en el plan como
        # ignorados para que el usuario vea que no se van a tocar.
        if elemento.name.lower() in ignorados:
            plan.append(
                PlanArchivo(
                    origen=elemento,
                    categoria=None,
                    estado=EstadoPlan.IGNORADO,
                    destino=None,
                    destino_resuelto=None,
                    incluir=False,
                )
            )
            continue

        categoria = mapa_extensiones.get(elemento.suffix.lower())

        if categoria is None:
            plan.append(
                _entrada_desconocido(elemento, destino, ajustes, ocupados)
            )
            continue

        nombre_categoria, subcarpeta = categoria

        plan.append(
            _entrada_con_categoria(
                elemento, destino, nombre_categoria, subcarpeta, ocupados
            )
        )

    return plan


def ejecutar_plan(
    plan: list[PlanArchivo], on_progreso=None
) -> ResumenEjecucion:
    """Ejecuta un plan: mueve los archivos marcados con `incluir=True`.

    - Los archivos OMITIDO e IGNORADO nunca se mueven.
    - Los ADVERTIDO solo se mueven si el usuario los incluyó a mano
      (`incluir=True`); por defecto quedan en su sitio.
    - Antes de mover, se vuelve a comprobar el destino: si entre la
      planificación y la ejecución apareció un archivo con el mismo nombre,
      se propone un alternativo en ese momento.
    - Nunca sobrescribe un archivo existente.

    `on_progreso`, si se indica, se llama tras procesar cada archivo con
    (procesados, total, fallidos). Es solo una notificación: el
    comportamiento del movimiento es idéntico con o sin callback.

    Devuelve un resumen con contadores y la lista de errores.
    """

    resumen = ResumenEjecucion()
    ocupados: set[Path] = set()
    total = len(plan)
    procesados = 0

    def _notificar():
        nonlocal procesados
        procesados += 1

        if on_progreso is not None:
            on_progreso(procesados, total, resumen.fallidos)

    for entrada in plan:

        if not entrada.incluir or entrada.estado in (
            EstadoPlan.OMITIDO,
            EstadoPlan.IGNORADO,
        ):
            resumen.omitidos += 1
            _notificar()
            continue

        if entrada.destino_resuelto is None:
            resumen.omitidos += 1
            _notificar()
            continue

        try:
            destino = _destino_disponible_ejecucion(
                entrada.destino_resuelto, ocupados
            )
            destino.parent.mkdir(parents=True, exist_ok=True)

            # shutil.move permite mover también entre unidades distintas.
            shutil.move(str(entrada.origen), str(destino))

        except (OSError, ValueError) as error:
            resumen.fallidos += 1
            resumen.errores.append((entrada.origen.name, str(error)))
            _notificar()
            continue

        ocupados.add(destino)
        resumen.movidos += 1
        _notificar()

    return resumen


# --- Funciones internas -----------------------------------------------------


def _mapear_extensiones(ajustes: Ajustes) -> dict[str, str]:
    """Crea el mapa extensión -> (nombre de categoría, subcarpeta de destino).

    Las extensiones ya están normalizadas en minúsculas al cargar la
    configuración (ver Categoria.__post_init__).
    """

    mapa: dict[str, tuple[str, str]] = {}

    for categoria in ajustes.categorias:
        for extension in categoria.extensiones:
            mapa[extension.lower()] = (categoria.nombre, categoria.destino)

    return mapa


def _entrada_con_categoria(
    elemento: Path,
    destino_raiz: Path,
    nombre_categoria: str,
    subcarpeta: str,
    ocupados: set[Path],
) -> PlanArchivo:
    """Prepara la entrada del plan para un archivo con categoría conocida."""

    carpeta_destino = destino_raiz / subcarpeta
    destino = carpeta_destino / elemento.name

    if destino.exists() or destino in ocupados:
        estado = EstadoPlan.CONFLICTO
        destino_resuelto = _nombre_alternativo(destino)
    else:
        estado = EstadoPlan.LISTO
        destino_resuelto = destino

    ocupados.add(destino_resuelto)

    return PlanArchivo(
        origen=elemento,
        categoria=nombre_categoria,
        estado=estado,
        destino=destino,
        destino_resuelto=destino_resuelto,
        incluir=True,
    )


def _entrada_desconocido(
    elemento: Path,
    destino_raiz: Path,
    ajustes: Ajustes,
    ocupados: set[Path],
) -> PlanArchivo:
    """Prepara la entrada del plan para un archivo con extensión desconocida.

    El comportamiento depende de la preferencia `unknown_files`:

    - OTROS: se envía a la carpeta "Otros" del destino (estado LISTO).
    - IGNORAR: no se toca (estado OMITIDO).
    - ADVERTIR: se marca en el plan sin incluirlo; el usuario decide
      archivo por archivo. Si el usuario lo incluye, irá a la carpeta
      "Otros" del destino.
    """

    carpeta_otros = destino_raiz / CARPETA_OTROS
    destino = carpeta_otros / elemento.name

    if ajustes.unknown_files is ComportamientoDesconocidos.IGNORAR:
        return PlanArchivo(
            origen=elemento,
            categoria=None,
            estado=EstadoPlan.OMITIDO,
            destino=None,
            destino_resuelto=None,
            incluir=False,
        )

    if ajustes.unknown_files is ComportamientoDesconocidos.ADVERTIR:
        estado = EstadoPlan.ADVERTIDO
        incluir = False
    else:
        estado = EstadoPlan.LISTO
        incluir = True

    if destino.exists() or destino in ocupados:
        if estado is EstadoPlan.LISTO:
            estado = EstadoPlan.CONFLICTO
        destino_resuelto = _nombre_alternativo(destino)
    else:
        destino_resuelto = destino

    ocupados.add(destino_resuelto)

    return PlanArchivo(
        origen=elemento,
        categoria=None,
        estado=estado,
        destino=destino,
        destino_resuelto=destino_resuelto,
        incluir=incluir,
    )


def _nombre_alternativo(destino: Path) -> Path:
    """Busca un nombre libre en la carpeta de destino (`nombre_1.ext`...)."""

    carpeta = destino.parent
    nombre = destino.stem
    extension = destino.suffix
    contador = 1

    while True:
        candidato = carpeta / f"{nombre}_{contador}{extension}"

        if not candidato.exists():
            return candidato

        contador += 1


def _destino_disponible_ejecucion(destino: Path, ocupados: set[Path]) -> Path:
    """Comprueba el destino justo antes de mover.

    Si el destino previsto está ocupado (por ejemplo, porque apareció un
    archivo nuevo entre la planificación y la ejecución), devuelve un
    nombre alternativo libre.
    """

    if destino.exists() or destino in ocupados:
        return _nombre_alternativo(destino)

    return destino
