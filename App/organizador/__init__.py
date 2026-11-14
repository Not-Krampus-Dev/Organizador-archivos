"""Motor de organización de archivos.

Paquete independiente de la interfaz gráfica. Expone:

- `models`: modelos de datos (categorías, ajustes, plan, resumen).
- `config`: carga y guardado de `config.json` con valores por defecto.
- `core`: planificación de operaciones y ejecución del plan.
"""

from .models import (
    Ajustes,
    Categoria,
    ComportamientoDesconocidos,
    EstadoPlan,
    PlanArchivo,
    ResumenEjecucion,
)

__all__ = [
    "Ajustes",
    "Categoria",
    "ComportamientoDesconocidos",
    "EstadoPlan",
    "PlanArchivo",
    "ResumenEjecucion",
]
