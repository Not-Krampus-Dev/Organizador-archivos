# Página «Preferencias»: navegación lateral, comportamiento general
# e idioma de la interfaz.

# Tres bloques:
#
#   · Navegación lateral: modo automático y retardo de ocultamiento.
#     El shell aplica estos valores en vivo cuando se guardan, pero el
#     botón de la barra solo cambia el modo de la sesión actual: aquí es
#     donde se persiste la preferencia en config.json.
#
#   · Organización: comportamiento de los archivos desconocidos y lista
#     de archivos ignorados (nombres, no extensiones).
#
#   · Idioma: se aplica en vivo al guardar (el shell retraduce todas
#     las páginas sin reiniciar).
#
# Modelo de trabajo: copia en memoria de la configuración, «Guardar
# cambios» valida con config.validar_config() y escribe con
# config.guardar_config(). Al guardar se emite config_actualizada con
# los ajustes nuevos.

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from gui.rutas import ruta_config
from gui.i18n import IDIOMAS, tr
from organizador import config
from organizador.models import ComportamientoDesconocidos

# Configuración centralizada: App/config.json en desarrollo y
# %APPDATA%\OrganizadorArchivos\config.json en la app empaquetada.
RUTA_CONFIG = ruta_config()

# Etiqueta traducible de cada comportamiento.
CLAVES_DESCONOCIDOS = {
    ComportamientoDesconocidos.OTROS: "pref.combo_otros",
    ComportamientoDesconocidos.IGNORAR: "pref.combo_ignorar",
    ComportamientoDesconocidos.ADVERTIR: "pref.combo_advertir",
}


class PaginaPreferencias(QWidget):
    """Preferencias de navegación, organización e idioma."""

    # Señal emitida tras guardar: lleva los ajustes ya validados.
    config_actualizada = Signal(object)

    def __init__(self):
        super().__init__()

        self.ruta_config = RUTA_CONFIG
        self.ajustes = None
        self._cambios_pendientes = False
        self._sincronizando = False

        # Estado de navegación de la sesión actual, empujado por el
        # shell al entrar en la página: (automatica, retardo_ms) o None.
        self._navegacion_sesion = None

        # Último mensaje de estado (clave + parámetros) para retraducir.
        self._ultimo_mensaje = ("pref.sin_cambios", {})

        self.casilla_navegacion = None
        self.campo_retardo = None
        self.combo_desconocidos = None
        self.lista_ignorados = None
        self.campo_ignorado = None
        self.boton_guardar = None
        self.texto_estado = None
        self.combo_idioma = None

        # Referencias para retraducir.
        self.grupo_navegacion = None
        self.grupo_organizacion = None
        self.grupo_idioma = None
        self.etiqueta_retardo = None
        self.etiqueta_desconocidos = None
        self.etiqueta_ignorados = None
        self.etiqueta_idioma = None
        self.boton_anadir = None
        self.boton_eliminar = None

        self._construir_interfaz()

    def showEvent(self, evento):
        """Carga la configuración del disco la primera vez que la
        página se muestra (si no se había cargado ya)."""

        super().showEvent(evento)

        if self.ajustes is None:
            self._cargar_config()

    # --- Carga y sincronización ------------------------------------------

    def _cargar_config(self):
        """Carga la configuración desde config.json y llena los controles."""

        self.ajustes = config.cargar_config(self.ruta_config)
        self._cambios_pendientes = False

        # El estado de sesión del shell manda sobre los valores del
        # disco (el botón de la barra cambia el modo sin escribir).
        if self._navegacion_sesion is not None:
            automatica, retardo = self._navegacion_sesion
            if (
                automatica != self.ajustes.navegacion_automatica
                or retardo != self.ajustes.retardo_navegacion_ms
            ):
                self.ajustes.navegacion_automatica = automatica
                self.ajustes.retardo_navegacion_ms = retardo
                self._cambios_pendientes = True

        self._volcar_ajustes_a_controles()
        self._actualizar_boton_guardar()
        self._mostrar_aviso(
            "pref.con_cambios" if self._cambios_pendientes else "pref.sin_cambios"
        )

    def sincronizar_navegacion(self, automatica: bool, retardo_ms: int):
        """Recibe el modo y retardo de navegación de la sesión actual.

        Si la sesión cambió desde la última sincronización (p. ej. el
        usuario pulsó el botón de modo de la barra) y difiere de la
        copia en memoria, la actualiza y marca cambios pendientes. Si
        la sesión no cambió, no se toca nada: las ediciones pendientes
        del usuario sobreviven al cambio de página.
        """

        nueva_sesion = (automatica, retardo_ms)
        sesion_anterior = self._navegacion_sesion
        self._navegacion_sesion = nueva_sesion

        if self.ajustes is None:
            return

        if sesion_anterior is not None and nueva_sesion == sesion_anterior:
            return

        if (
            automatica != self.ajustes.navegacion_automatica
            or retardo_ms != self.ajustes.retardo_navegacion_ms
        ):
            self.ajustes.navegacion_automatica = automatica
            self.ajustes.retardo_navegacion_ms = retardo_ms
            self._volcar_ajustes_a_controles()
            self._cambios_pendientes_marcar()

    def _cambios_pendientes_marcar(self):
        self._cambios_pendientes = True
        self._actualizar_boton_guardar()
        self._mostrar_aviso("pref.con_cambios")

    def _actualizar_boton_guardar(self):
        if self.boton_guardar is not None:
            self.boton_guardar.setEnabled(
                self._cambios_pendientes and self.ajustes is not None
            )

    def _volcar_ajustes_a_controles(self):
        """Muestra los ajustes en memoria en los controles de la página."""

        self._sincronizando = True

        if self.casilla_navegacion is not None:
            self.casilla_navegacion.setChecked(self.ajustes.navegacion_automatica)
            self.campo_retardo.setValue(self.ajustes.retardo_navegacion_ms)
            self.campo_retardo.setEnabled(self.ajustes.navegacion_automatica)

        indice = self.combo_desconocidos.findData(self.ajustes.unknown_files.value)
        if indice >= 0:
            self.combo_desconocidos.setCurrentIndex(indice)

        indice_idioma = self.combo_idioma.findData(self.ajustes.idioma)
        if indice_idioma >= 0:
            self.combo_idioma.setCurrentIndex(indice_idioma)

        self.lista_ignorados.clear()
        for nombre in self.ajustes.archivos_ignorados:
            self.lista_ignorados.addItem(nombre)

        self._sincronizando = False

    # --- Retraducción -------------------------------------------------------

    def retraducir(self):
        """Reaplica todos los textos de la página (cambio de idioma)."""

        self.grupo_navegacion.setTitle(tr("pref.grupo_navegacion"))
        self.casilla_navegacion.setText(tr("pref.casilla_navegacion"))
        self.etiqueta_retardo.setText(tr("pref.retardo"))

        self.grupo_organizacion.setTitle(tr("pref.grupo_organizacion"))
        self.etiqueta_desconocidos.setText(tr("pref.desconocidos"))
        for indice, comportamiento in enumerate(ComportamientoDesconocidos):
            self.combo_desconocidos.setItemText(
                indice, tr(CLAVES_DESCONOCIDOS[comportamiento])
            )
        self.etiqueta_ignorados.setText(tr("pref.ignorados"))
        self.boton_anadir.setText(tr("pref.anadir"))
        self.boton_eliminar.setText(tr("pref.eliminar"))

        self.grupo_idioma.setTitle(tr("pref.grupo_idioma"))
        self.etiqueta_idioma.setText(tr("pref.idioma"))

        self.boton_guardar.setText(tr("pref.guardar"))

        clave, parametros = self._ultimo_mensaje
        self.texto_estado.setText(tr(clave, **parametros))

    # --- Construcción de la interfaz --------------------------------------

    def _construir_interfaz(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(20, 16, 20, 16)
        raiz.setSpacing(10)

        raiz.addWidget(self._construir_grupo_navegacion())
        raiz.addWidget(self._construir_grupo_organizacion(), stretch=1)
        raiz.addWidget(self._construir_grupo_idioma())
        raiz.addWidget(self._construir_fila_guardar())
        raiz.addWidget(self._construir_barra_estado())

    def _construir_fila_guardar(self) -> QWidget:
        fila = QWidget()
        layout = QHBoxLayout(fila)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()

        self.boton_guardar = QPushButton(
            tr("pref.guardar"), objectName="boton_primario"
        )
        self.boton_guardar.setEnabled(False)
        self.boton_guardar.clicked.connect(self._guardar)

        layout.addWidget(self.boton_guardar)

        return fila

    def _construir_grupo_navegacion(self) -> QGroupBox:
        grupo = QGroupBox(tr("pref.grupo_navegacion"))
        self.grupo_navegacion = grupo

        layout = QVBoxLayout(grupo)
        layout.setSpacing(8)

        self.casilla_navegacion = QCheckBox(
            tr("pref.casilla_navegacion"), objectName="casilla_navegacion"
        )
        self.casilla_navegacion.toggled.connect(self._navegacion_cambiada)
        layout.addWidget(self.casilla_navegacion)

        formulario = QFormLayout()
        formulario.setSpacing(8)

        self.campo_retardo = QSpinBox(objectName="campo_retardo")
        self.campo_retardo.setRange(
            config.RETARDO_MINIMO_MS, config.RETARDO_MAXIMO_MS
        )
        self.campo_retardo.setSingleStep(50)
        self.campo_retardo.setSuffix(" ms")
        self.campo_retardo.valueChanged.connect(self._retardo_cambiado)

        self.etiqueta_retardo = QLabel(tr("pref.retardo"))
        formulario.addRow(self.etiqueta_retardo, self.campo_retardo)
        layout.addLayout(formulario)

        return grupo

    def _construir_grupo_organizacion(self) -> QGroupBox:
        grupo = QGroupBox(tr("pref.grupo_organizacion"))
        self.grupo_organizacion = grupo

        layout = QVBoxLayout(grupo)
        layout.setSpacing(10)

        formulario = QFormLayout()
        formulario.setSpacing(8)

        self.combo_desconocidos = QComboBox(objectName="combo_desconocidos")
        for comportamiento in ComportamientoDesconocidos:
            # userData: el valor textual del enum (PySide convierte los
            # enums derivados de str a str plano en los userData).
            self.combo_desconocidos.addItem(
                tr(CLAVES_DESCONOCIDOS[comportamiento]), comportamiento.value
            )
        self.combo_desconocidos.currentIndexChanged.connect(
            self._desconocidos_cambiado
        )

        self.etiqueta_desconocidos = QLabel(tr("pref.desconocidos"))
        formulario.addRow(self.etiqueta_desconocidos, self.combo_desconocidos)
        layout.addLayout(formulario)

        self.etiqueta_ignorados = QLabel(tr("pref.ignorados"))
        layout.addWidget(self.etiqueta_ignorados)

        self.lista_ignorados = QListWidget(objectName="lista_ignorados")
        layout.addWidget(self.lista_ignorados, stretch=1)

        fila = QHBoxLayout()
        fila.setSpacing(8)

        self.campo_ignorado = QLineEdit(objectName="campo_ignorado")
        self.campo_ignorado.setPlaceholderText("desktop.ini")

        self.boton_anadir = QPushButton(
            tr("pref.anadir"), objectName="boton_anadir_ignorado"
        )
        self.boton_anadir.clicked.connect(self._anadir_ignorado)

        self.boton_eliminar = QPushButton(
            tr("pref.eliminar"), objectName="boton_eliminar_ignorado"
        )
        self.boton_eliminar.clicked.connect(self._eliminar_ignorado)

        fila.addWidget(self.campo_ignorado, stretch=1)
        fila.addWidget(self.boton_anadir)
        fila.addWidget(self.boton_eliminar)
        layout.addLayout(fila)

        return grupo

    def _construir_grupo_idioma(self) -> QGroupBox:
        grupo = QGroupBox(tr("pref.grupo_idioma"))
        self.grupo_idioma = grupo

        formulario = QFormLayout(grupo)
        formulario.setSpacing(8)

        self.combo_idioma = QComboBox(objectName="combo_idioma")
        # Etiquetas en el idioma propio (no se traducen).
        for codigo, etiqueta in IDIOMAS.items():
            self.combo_idioma.addItem(etiqueta, codigo)
        self.combo_idioma.currentIndexChanged.connect(self._idioma_cambiado)

        self.etiqueta_idioma = QLabel(tr("pref.idioma"))
        formulario.addRow(self.etiqueta_idioma, self.combo_idioma)

        return grupo

    def _construir_barra_estado(self) -> QLabel:
        self.texto_estado = QLabel(
            tr("pref.sin_cambios"), objectName="texto_estado"
        )
        return self.texto_estado

    # --- Edición de la navegación ------------------------------------------

    def _navegacion_cambiada(self, automatica: bool):
        if self._sincronizando or self.ajustes is None:
            return

        self.ajustes.navegacion_automatica = automatica
        self.campo_retardo.setEnabled(automatica)
        self._cambios_pendientes_marcar()

    def _retardo_cambiado(self, valor: int):
        if self._sincronizando or self.ajustes is None:
            return

        self.ajustes.retardo_navegacion_ms = valor
        self._cambios_pendientes_marcar()

    # --- Edición de la organización ------------------------------------------

    def _desconocidos_cambiado(self, indice: int):
        if self._sincronizando or self.ajustes is None:
            return

        comportamiento = self.combo_desconocidos.itemData(indice)
        if comportamiento is not None:
            self.ajustes.unknown_files = ComportamientoDesconocidos(
                comportamiento
            )
            self._cambios_pendientes_marcar()

    def _idioma_cambiado(self, indice: int):
        if self._sincronizando or self.ajustes is None:
            return

        codigo = self.combo_idioma.itemData(indice)
        if codigo is not None:
            self.ajustes.idioma = codigo
            self._cambios_pendientes_marcar()

    def _anadir_ignorado(self):
        texto = self.campo_ignorado.text().strip().lower()

        if self.ajustes is None or not texto:
            return

        if texto in self.ajustes.archivos_ignorados:
            self._mostrar_error("pref.ignorado_duplicado", nombre=texto)
            return

        self.ajustes.archivos_ignorados.append(texto)
        self.campo_ignorado.clear()
        self._refrescar_ignorados()
        self._cambios_pendientes_marcar()

    def _eliminar_ignorado(self):
        if self.ajustes is None:
            return

        fila = self.lista_ignorados.currentRow()
        if fila < 0:
            return

        del self.ajustes.archivos_ignorados[fila]
        self._refrescar_ignorados()
        self._cambios_pendientes_marcar()

    def _refrescar_ignorados(self):
        self.lista_ignorados.clear()

        if self.ajustes is None:
            return

        for nombre in self.ajustes.archivos_ignorados:
            self.lista_ignorados.addItem(nombre)

    # --- Guardar ------------------------------------------------------------

    def _guardar(self):
        """Valida la configuración en memoria y la escribe en disco."""

        if self.ajustes is None or not self._cambios_pendientes:
            return

        try:
            self.ajustes = config.validar_config(self.ajustes)

        except ValueError as error:
            self._mostrar_error("pref.error_guardar", detalle=error)
            return

        try:
            config.guardar_config(self.ruta_config, self.ajustes)

        except OSError as error:
            self._mostrar_error("pref.error_escritura", detalle=error)
            return

        self._cambios_pendientes = False
        self._actualizar_boton_guardar()
        self._volcar_ajustes_a_controles()
        self._mostrar_aviso("pref.guardada")
        self.config_actualizada.emit(self.ajustes)

    # --- Mensajes de estado ---------------------------------------------------

    def _mostrar_aviso(self, clave: str, **parametros):
        """Fija el mensaje de estado (se recuerda para retraducir)."""

        self._ultimo_mensaje = (clave, parametros)
        self.texto_estado.setText(tr(clave, **parametros))

    def _mostrar_error(self, clave: str, **parametros):
        self._mostrar_aviso(clave, **parametros)
