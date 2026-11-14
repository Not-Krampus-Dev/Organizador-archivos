# Modelos de datos del motor de organización.

# No contienen lógica de movimiento de archivos: solo describen
# categorías, ajustes, entradas del plan y el resumen de ejecución.

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ComportamientoDesconocidos(str, Enum):
    """Qué hacer con los archivos cuya extensión no pertenece a ninguna categoría."""

    OTROS = "otros"        # Enviarlos a la carpeta "Otros" del destino.
    IGNORAR = "ignorar"    # No tocarlos.
    ADVERTIR = "advertir"  # Marcarlos en el plan para que el usuario decida.


class EstadoPlan(str, Enum):
    """Estado de cada archivo dentro del plan de organización."""

    LISTO = "listo"          # Puede moverse al destino propuesto.
    CONFLICTO = "conflicto"  # El nombre está ocupado; se propuso un alternativo.
    ADVERTIDO = "advertido"  # Extensión desconocida; requiere decisión del usuario.
    OMITIDO = "omitido"      # Desconocido en modo "ignorar"; no se toca.
    IGNORADO = "ignorado"    # Está en la lista de archivos ignorados.


@dataclass
class Categoria:
    """Categoría de archivos: nombre, extensiones y subcarpeta de destino.

    `destino` es una subcarpeta relativa dentro de la carpeta de destino
    general elegida por el usuario (por ejemplo "Imágenes").
    """

    nombre: str
    extensiones: list[str]
    destino: str = ""

    def __post_init__(self):
        if not self.destino:
            self.destino = self.nombre

        self.extensiones = [ext.lower() for ext in self.extensiones]


@dataclass
class Ajustes:
    """Configuración completa de la aplicación, cargada desde config.json."""

    categorias: list[Categoria] = field(default_factory=list)
    unknown_files: ComportamientoDesconocidos = ComportamientoDesconocidos.OTROS
    archivos_ignorados: list[str] = field(default_factory=list)

    # Preferencias de la navegación lateral.
    navegacion_automatica: bool = True
    retardo_navegacion_ms: int = 400

    # Código de idioma de la interfaz (es/en/ja).
    idioma: str = "es"


@dataclass
class PlanArchivo:
    """Entrada del plan para un único archivo.

    - `destino` es el destino "natural" (carpeta de la categoría + nombre).
    - `destino_resuelto` es el destino final propuesto, tras resolver
      conflictos de nombre (puede ser `origen.name` con sufijo `_1`, `_2`...).
      Es `None` cuando el archivo no se va a mover (omitido o ignorado).
    - `incluir` indica si el archivo se moverá al ejecutar el plan. El
      usuario puede cambiarlo archivo por archivo antes de ejecutar.
    """

    origen: Path
    categoria: str | None
    estado: EstadoPlan
    destino: Path | None = None
    destino_resuelto: Path | None = None
    incluir: bool = False


@dataclass
class ResumenEjecucion:
    """Resultado de ejecutar un plan completo."""

    movidos: int = 0
    omitidos: int = 0
    fallidos: int = 0
    errores: list[tuple[str, str]] = field(default_factory=list)
