# Tema oscuro de la aplicación (hoja de estilos Qt).

# Paleta grafito / gris carbón, sobria y de alto contraste:
#   #1e1f22  fondo principal
#   #26282c  paneles y barra superior
#   #1a1b1e  campos y marco de vista previa
#   #e8eaed  texto principal
#   #8a8f98  texto secundario
#   #3b6ea5  acento apagado (botón principal)

import re
from PySide6.QtWidgets import QApplication


HOJA_ESTILOS = """
* {
    font-family: "Segoe UI", "Segoe UI Variable", Arial, sans-serif;
    font-size: 10pt;
    color: #e8eaed;
}

QMainWindow, QWidget#fondo {
    background-color: #1e1f22;
}

/* --- Barra lateral --- */

QFrame#barra_lateral {
    background-color: #26282c;
    border-right: 1px solid #32353a;
}

QLabel#titulo_app {
    font-size: 12pt;
    font-weight: 600;
    letter-spacing: 0.5px;
}

QLabel#subtitulo_app {
    color: #8a8f98;
    font-size: 9pt;
}

QPushButton#boton_navegacion {
    background-color: transparent;
    color: #9aa0a6;
    text-align: left;
    padding: 10px 14px;
    border-radius: 6px;
    border: none;
    font-weight: 600;
}

QPushButton#boton_navegacion:hover {
    background-color: #2b2e33;
    color: #e8eaed;
}

QPushButton#boton_navegacion:checked {
    background-color: #32353a;
    color: #e8eaed;
    border-left: 2px solid #4c8bf5;
    padding-left: 12px;
}

/* Elemento seleccionado en las listas (categorías, ignorados). */
QListWidget::item:selected {
    background-color: #32353a;
    color: #e8eaed;
    border-left: 2px solid #4c8bf5;
}

/* Modo contraído: icono centrado, sin asimetrías de texto */
QFrame#barra_lateral[contraida="true"] QPushButton#boton_navegacion {
    padding: 10px 0;
    text-align: center;
}

QFrame#barra_lateral[contraida="true"] QPushButton#boton_navegacion:checked {
    padding: 10px 0;
}

QPushButton#boton_alternador {
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 6px 8px;
}

QPushButton#boton_alternador:hover {
    background-color: #2b2e33;
}

QPushButton#boton_modo {
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 6px;
}

QPushButton#boton_modo:hover {
    background-color: #2b2e33;
}

QPushButton#boton_modo:checked {
    background-color: #32353a;
}

/* --- Tooltips --- */

QToolTip {
    background-color: #32353a;
    color: #e8eaed;
    border: 1px solid #3b3f45;
    padding: 4px 8px;
    border-radius: 4px;
}

/* --- Páginas --- */

QLabel#titulo_pagina {
    font-size: 12pt;
    font-weight: 600;
}

QLabel#texto_pagina {
    color: #6b7076;
}

/* --- Paneles (selección de carpetas) --- */

QGroupBox {
    background-color: #26282c;
    border: 1px solid #32353a;
    border-radius: 8px;
    margin-top: 12px;
    padding: 12px 12px 10px 12px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 4px;
    color: #9aa0a6;
    font-weight: 600;
}

QLabel#descripcion_panel {
    color: #8a8f98;
    font-size: 9pt;
}

/* --- Campo de ruta --- */

QLineEdit {
    background-color: #1a1b1e;
    border: 1px solid #32353a;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e8eaed;
}

QLineEdit[readOnly="true"] {
    color: #c4c8cd;
}

QLineEdit:focus {
    border-color: #3b6ea5;
}

/* --- Botones --- */

QPushButton {
    background-color: #32353a;
    color: #e8eaed;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
}

QPushButton:hover {
    background-color: #3b3f45;
}

QPushButton:pressed {
    background-color: #2b2e33;
}

QPushButton:focus {
    border: 1px solid #3b6ea5;
}

QPushButton:disabled {
    background-color: #2a2c2f;
    color: #5c6167;
}

QPushButton#boton_primario {
    background-color: #3b6ea5;
    color: #ffffff;
}

QPushButton#boton_primario:hover {
    background-color: #477cb5;
}

QPushButton#boton_primario:pressed {
    background-color: #33608f;
}

/* Deshabilitado: apagado y con borde visible, sin parecerse al
   estado activo (la regla del ID ganaría a la genérica :disabled). */

QPushButton#boton_primario:disabled {
    background-color: #26282c;
    color: #6b7178;
    border: 1px solid #33363c;
}

/* --- Listas (editor de categorías) --- */

QListWidget {
    background-color: #1a1b1e;
    border: 1px solid #32353a;
    border-radius: 6px;
    padding: 4px;
    color: #e8eaed;
}

QListWidget::item {
    padding: 6px 8px;
    border-radius: 4px;
}

QListWidget::item:hover {
    background-color: #2b2e33;
}

QListWidget::item:selected {
    background-color: #32353a;
    color: #e8eaed;
}

/* --- Controles (página Preferencias) --- */

QCheckBox {
    color: #e8eaed;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #3a3d43;
    border-radius: 4px;
    background-color: #1a1b1e;
}

QCheckBox::indicator:hover {
    border-color: #4a4e55;
}

QCheckBox::indicator:checked {
    background-color: #4c8bf5;
    border-color: #4c8bf5;
}

QComboBox {
    background-color: #1a1b1e;
    border: 1px solid #32353a;
    border-radius: 6px;
    padding: 5px 10px;
    color: #e8eaed;
}

QComboBox:hover {
    border-color: #4a4e55;
}

QComboBox::drop-down {
    border: none;
    width: 22px;
}

QComboBox QAbstractItemView {
    background-color: #1a1b1e;
    border: 1px solid #3a3d43;
    selection-background-color: #32353a;
    selection-color: #e8eaed;
    color: #e8eaed;
}

QSpinBox {
    background-color: #1a1b1e;
    border: 1px solid #32353a;
    border-radius: 6px;
    padding: 5px 8px;
    color: #e8eaed;
    selection-background-color: #3a3d43;
}

QSpinBox:hover {
    border-color: #4a4e55;
}

QSpinBox::up-button,
QSpinBox::down-button {
    background-color: #2b2e33;
    border: none;
    border-radius: 3px;
    width: 16px;
}

QSpinBox::up-button:hover,
QSpinBox::down-button:hover {
    background-color: #3a3d43;
}

QSpinBox:disabled {
    color: #6f747c;
    border-color: #2b2e33;
}

/* --- Chips de extensiones (editor de categorías) --- */

#panel_chips {
    background-color: transparent;
}

#chip_extension {
    background-color: #2b2e33;
    border: 1px solid #3a3d43;
    border-radius: 11px;
}

#chip_extension QLabel {
    color: #e8eaed;
    background: transparent;
}

#boton_cerrar_etiqueta {
    background-color: transparent;
    border: none;
    border-radius: 9px;
    color: #9aa0a6;
    font-size: 12px;
    padding: 0;
}

#boton_cerrar_etiqueta:hover {
    background-color: #3a3d43;
    color: #f28b82;
}

/* --- Progreso (organizador) --- */

#marco_progreso {
    background-color: transparent;
}

#barra_progreso {
    background-color: #1a1b1e;
    border: 1px solid #32353a;
    border-radius: 6px;
    text-align: center;
    color: #e8eaed;
}

#barra_progreso::chunk {
    background-color: #4c8bf5;
    border-radius: 5px;
}

#texto_progreso {
    color: #9aa0a6;
}

/* --- Sección central (vista previa) --- */

QFrame#marco_vista_previa {
    background-color: #1a1b1e;
    border: 1px solid #32353a;
    border-radius: 8px;
}

/* --- Tabla de vista previa --- */

QTableWidget {
    background-color: #1a1b1e;
    alternate-background-color: #202226;
    border: none;
    gridline-color: #26282c;
    selection-background-color: #2f3a44;
    selection-color: #e8eaed;
}

QHeaderView::section {
    background-color: #26282c;
    color: #9aa0a6;
    border: none;
    border-right: 1px solid #32353a;
    padding: 6px 8px;
    font-weight: 600;
}

QTableCornerButton::section {
    background-color: #26282c;
    border: none;
}

/* --- Barra inferior --- */

QLabel#texto_estado {
    color: #8a8f98;
}
"""


def aplicar_tema(app: QApplication) -> None:
    """Aplica el tema oscuro a la aplicación."""

    app.setStyleSheet(_sin_advertencias(HOJA_ESTILOS))


def _sin_advertencias(hoja: str) -> str:
    """Normaliza la hoja de estilos (por ahora, solo recorta espacios)."""

    return hoja.strip()
