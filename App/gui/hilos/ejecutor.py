# Ejecución del plan de organización en un hilo secundario.

# El movimiento de archivos vive en organizador.core: este hilo solo
# lo ejecuta y notifica por señales. Reglas de seguridad:
#
#   · El hilo NO toca widgets: emite señales, que Qt entrega en el
#     hilo de la interfaz (conexión en cola automática entre hilos).
#   · La página deshabilita sus controles durante la ejecución, así
#     que el plan no puede mutar mientras se itera.
#   · Cualquier excepción del motor se convierte en la señal `fallo`;
#     la interfaz se recupera y queda usable en todos los casos.

from PySide6.QtCore import QThread, Signal

from organizador import core


class EjecutorEjecucion(QThread):
    """Ejecuta un plan en segundo plano y notifica el avance."""

    # (procesados, total, fallidos) tras cada archivo.
    progreso = Signal(int, int, int)

    # Resumen final correcto.
    terminado = Signal(object)

    # La ejecución se interrumpió por un error inesperado.
    fallo = Signal(str)

    def __init__(self, plan, padre=None):
        super().__init__(padre)
        self.plan = plan

    def run(self):
        try:
            resumen = core.ejecutar_plan(
                self.plan,
                on_progreso=lambda procesados, total, fallidos: self.progreso.emit(
                    procesados, total, fallidos
                ),
            )

        except Exception as error:  # noqa: BLE001: la UI debe recuperarse
            self.fallo.emit(str(error))
            return

        self.terminado.emit(resumen)
