# Punto de entrada de la aplicación de escritorio.

# Ejecutar con el entorno virtual del proyecto:
#   App\.venv\Scripts\python.exe App\main.py

import sys

from PySide6.QtWidgets import QApplication

from gui.main_window import VentanaPrincipal
from gui.theme import aplicar_tema

TITULO_APP = "Organizador de archivos"


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(TITULO_APP)

    aplicar_tema(app)

    ventana = VentanaPrincipal()
    ventana.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
