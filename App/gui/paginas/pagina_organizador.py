# Página «Organizador»: selección de carpetas, vista previa y ejecución.

# Contenido trasladado desde la antigua VentanaPrincipal sin reescribir
# su lógica: los métodos de análisis, tabla y ejecución funcionan igual.
# Los textos visibles se resuelven con tr() para la internacionalización.

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gui.hilos.ejecutor import EjecutorEjecucion
from gui.i18n import tr
from gui.rutas import ruta_config
from organizador import config, core
from organizador.models import EstadoPlan, PlanArchivo

# Archivo de configuración centralizado: App/config.json en desarrollo
# y %APPDATA%\OrganizadorArchivos\config.json en la app empaquetada.
RUTA_CONFIG = ruta_config()

# Cabeceras de la tabla: claves de traducción.
CLAVES_COLUMNAS = (
    "org.columna_mover",
    "org.columna_nombre",
    "org.columna_extension",
    "org.columna_categoria",
    "org.columna_destino",
    "org.columna_estado",
)

# Texto legible de cada estado del plan: clave de traducción por estado.
CLAVES_ESTADO = {
    EstadoPlan.LISTO: "estado.listo",
    EstadoPlan.CONFLICTO: "estado.conflicto",
    EstadoPlan.ADVERTIDO: "estado.advertido",
    EstadoPlan.OMITIDO: "estado.omitido",
    EstadoPlan.IGNORADO: "estado.ignorado",
}

# Colores apagados, acordes con el tema grafito.
COLORES_ESTADO = {
    EstadoPlan.LISTO: "#8fae8f",
    EstadoPlan.CONFLICTO: "#d0a35c",
    EstadoPlan.ADVERTIDO: "#a48ac2",
    EstadoPlan.OMITIDO: "#6b7076",
    EstadoPlan.IGNORADO: "#6b7076",
}

ESTADOS_SIN_CASILLA = (EstadoPlan.OMITIDO, EstadoPlan.IGNORADO)


class PaginaOrganizador(QWidget):
    """Página principal: selección de carpetas, plan y ejecución."""

    def __init__(self):
        super().__init__()

        self.ruta_config = RUTA_CONFIG
        self.ruta_origen: Path | None = None
        self.ruta_destino: Path | None = None

        self.plan: list[PlanArchivo] = []
        self._cargando_tabla = False

        # Último mensaje de estado (clave de traducción + parámetros):
        # se vuelve a aplicar al retraducir.
        self._ultimo_mensaje = ("org.estado_inicial", {})

        # Hilo de ejecución en curso (None si no hay ninguno).
        self._ejecutor: EjecutorEjecucion | None = None
        self._bloqueables: list = []

        self.campo_origen: QLineEdit | None = None
        self.campo_destino: QLineEdit | None = None
        self.boton_organizar: QPushButton | None = None
        self.texto_estado: QLabel | None = None
        self.tabla: QTableWidget | None = None
        self.barra_progreso: QProgressBar | None = None
        self.texto_progreso: QLabel | None = None

        self._construir_interfaz()
        self._registrar_bloqueables()

    # --- Construcción de la interfaz -----------------------------------

    def _construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        layout.addLayout(self._construir_seleccion_carpetas())
        layout.addWidget(self._construir_marco_vista_previa(), stretch=1)
        layout.addLayout(self._construir_barra_acciones())

    def _construir_seleccion_carpetas(self) -> QHBoxLayout:
        fila = QHBoxLayout()
        fila.setSpacing(14)

        fila.addWidget(
            self._construir_panel_carpeta(
                "org.origen",
                "org.origen_desc",
                self._seleccionar_origen,
                es_origen=True,
            )
        )
        fila.addWidget(
            self._construir_panel_carpeta(
                "org.destino",
                "org.destino_desc",
                self._seleccionar_destino,
                es_origen=False,
            )
        )

        return fila

    def _construir_panel_carpeta(
        self, clave_titulo: str, clave_desc: str, slot_seleccion, es_origen: bool
    ) -> QGroupBox:
        panel = QGroupBox(tr(clave_titulo))

        layout = QVBoxLayout(panel)
        layout.setSpacing(8)

        descripcion = QLabel(tr(clave_desc), objectName="descripcion_panel")
        layout.addWidget(descripcion)

        fila = QHBoxLayout()
        fila.setSpacing(8)

        campo = QLineEdit()
        campo.setReadOnly(True)
        campo.setPlaceholderText(tr("org.sin_seleccionar"))

        boton = QPushButton(tr("org.examinar"))
        boton.clicked.connect(slot_seleccion)

        fila.addWidget(campo, stretch=1)
        fila.addWidget(boton)
        layout.addLayout(fila)

        # Referencias para retraducir y para actualizar el campo.
        if es_origen:
            self.campo_origen = campo
            self.panel_origen = panel
            self.descripcion_origen = descripcion
            self.boton_examinar_origen = boton
        else:
            self.campo_destino = campo
            self.panel_destino = panel
            self.descripcion_destino = descripcion
            self.boton_examinar_destino = boton

        return panel

    def _construir_marco_vista_previa(self) -> QFrame:
        marco = QFrame(objectName="marco_vista_previa")

        layout = QVBoxLayout(marco)
        layout.setContentsMargins(6, 6, 6, 6)

        self.tabla = QTableWidget(0, len(CLAVES_COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(
            [tr(clave) for clave in CLAVES_COLUMNAS]
        )
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setShowGrid(False)

        # Anchos de columna fijos, excepto Nombre y Destino que se estiran.
        cabecera = self.tabla.horizontalHeader()
        cabecera.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        cabecera.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        cabecera.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        cabecera.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        cabecera.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        cabecera.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        cabecera.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(0, 60)
        self.tabla.setColumnWidth(2, 80)
        self.tabla.setColumnWidth(3, 140)
        self.tabla.setColumnWidth(5, 110)

        self.tabla.itemChanged.connect(self._cambiar_casilla)

        layout.addWidget(self.tabla)

        return marco

    def _construir_barra_acciones(self) -> QHBoxLayout:
        barra = QHBoxLayout()
        barra.setSpacing(10)

        self.texto_estado = QLabel(tr("org.estado_inicial"), objectName="texto_estado")
        barra.addWidget(self.texto_estado, stretch=1)

        barra.addWidget(self._construir_zona_progreso())

        self.boton_organizar = QPushButton(tr("org.organizar"))
        self.boton_organizar.setEnabled(False)
        self.boton_organizar.clicked.connect(self._organizar)

        boton_analizar = QPushButton(tr("org.analizar"))
        boton_analizar.setObjectName("boton_primario")
        boton_analizar.clicked.connect(self._analizar)
        self.boton_analizar = boton_analizar

        barra.addWidget(self.boton_organizar)
        barra.addWidget(boton_analizar)

        return barra

    def _construir_zona_progreso(self) -> QFrame:
        """Barra de progreso y contadores, ocultos fuera de la ejecución."""

        marco = QFrame(objectName="marco_progreso")

        layout = QHBoxLayout(marco)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.barra_progreso = QProgressBar(objectName="barra_progreso")
        self.barra_progreso.setRange(0, 1)
        self.barra_progreso.setValue(0)
        self.barra_progreso.setFixedWidth(180)

        self.texto_progreso = QLabel("", objectName="texto_progreso")

        layout.addWidget(self.barra_progreso)
        layout.addWidget(self.texto_progreso)

        marco.setVisible(False)

        return marco

    # --- Textos de estado ---------------------------------------------------

    def _mensaje(self, clave: str, **parametros):
        """Fija el texto de estado y lo recuerda para retraducir."""

        self._ultimo_mensaje = (clave, parametros)

        if self.texto_estado is not None:
            self.texto_estado.setText(tr(clave, **parametros))

    def retraducir(self):
        """Reaplica cabeceras de tabla, estados visibles y el mensaje."""

        self.tabla.setHorizontalHeaderLabels(
            [tr(clave) for clave in CLAVES_COLUMNAS]
        )

        # Paneles de carpeta.
        self.panel_origen.setTitle(tr("org.origen"))
        self.panel_destino.setTitle(tr("org.destino"))
        self.descripcion_origen.setText(tr("org.origen_desc"))
        self.descripcion_destino.setText(tr("org.destino_desc"))
        self.campo_origen.setPlaceholderText(tr("org.sin_seleccionar"))
        self.campo_destino.setPlaceholderText(tr("org.sin_seleccionar"))
        self.boton_examinar_origen.setText(tr("org.examinar"))
        self.boton_examinar_destino.setText(tr("org.examinar"))

        # Botones de acción.
        self.boton_analizar.setText(tr("org.analizar"))
        self.boton_organizar.setText(tr("org.organizar"))

        if self.plan:
            self._mostrar_plan()

        clave, parametros = self._ultimo_mensaje
        if self.texto_estado is not None:
            self.texto_estado.setText(tr(clave, **parametros))

    # --- Selección de carpetas ------------------------------------------

    def _seleccionar_origen(self):
        self._seleccionar_carpeta(tr("org.dialogo_origen"), self.campo_origen)

    def _seleccionar_destino(self):
        self._seleccionar_carpeta(tr("org.dialogo_destino"), self.campo_destino)

    def _seleccionar_carpeta(self, titulo: str, campo: QLineEdit):
        carpeta = QFileDialog.getExistingDirectory(self, titulo)

        if not carpeta:
            return

        ruta = Path(carpeta)

        # Origen y destino deben ser carpetas distintas.
        if campo is self.campo_destino and ruta == self.ruta_origen:
            QMessageBox.warning(
                self,
                tr("org.carpeta_invalida"),
                tr("org.mismo_destino"),
            )
            return

        if campo is self.campo_origen and ruta == self.ruta_destino:
            QMessageBox.warning(
                self,
                tr("org.carpeta_invalida"),
                tr("org.mismo_origen"),
            )
            return

        campo.setText(str(ruta))

        if campo is self.campo_origen:
            self.ruta_origen = ruta
        else:
            self.ruta_destino = ruta

        self._limpiar_plan()
        self._actualizar_estado()

    def _carpetas_validas(self) -> tuple[bool, tuple]:
        """Comprueba que origen y destino estén elegidos y sean válidos.

        Devuelve (válido, (clave, parámetros)) para mensajes traducibles.
        """

        if self.ruta_origen is None or self.ruta_destino is None:
            return False, ("org.faltan_carpetas", {})

        if not self.ruta_origen.is_dir():
            return False, ("org.origen_no_existe", {"ruta": self.ruta_origen})

        if not self.ruta_destino.is_dir():
            return False, ("org.destino_no_existe", {"ruta": self.ruta_destino})

        if self.ruta_origen == self.ruta_destino:
            return False, ("org.mismo_destino", {})

        return True, ("", {})

    # --- Análisis (planificar) -------------------------------------------

    def _analizar(self):
        """Construye el plan con el motor y lo muestra en la tabla."""

        valido, mensaje = self._carpetas_validas()

        if not valido:
            self._limpiar_plan()
            self._mensaje(mensaje[0], **mensaje[1])
            return

        try:
            ajustes = config.cargar_config(self.ruta_config)
            self.plan = core.planificar(self.ruta_origen, self.ruta_destino, ajustes)

        except OSError as error:
            QMessageBox.critical(
                self,
                tr("org.error_analizar_titulo"),
                tr("org.error_analizar", detalle=error),
            )
            return

        self._mostrar_plan()

        if not self.plan:
            self._mensaje("org.sin_archivos")
            return

        incluidos = sum(1 for entrada in self.plan if entrada.incluir)
        conflictos = sum(
            1 for entrada in self.plan if entrada.estado is EstadoPlan.CONFLICTO
        )

        self._mensaje(
            "org.analizado",
            total=len(self.plan),
            incluidos=incluidos,
            conflictos=conflictos,
        )

    def _mostrar_plan(self):
        """Vuelca el plan actual en la tabla de vista previa."""

        self._cargando_tabla = True
        self.tabla.setRowCount(0)

        for entrada in self.plan:
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)

            self.tabla.setItem(fila, 0, self._item_casilla(entrada))
            self.tabla.setItem(fila, 1, self._item_texto(entrada.origen.name))
            self.tabla.setItem(fila, 2, self._item_texto(self._extension(entrada)))
            self.tabla.setItem(fila, 3, self._item_texto(self._categoria(entrada)))
            self.tabla.setItem(fila, 4, self._item_destino(entrada))
            self.tabla.setItem(fila, 5, self._item_estado(entrada))

        self._cargando_tabla = False
        self._actualizar_boton_organizar()

    def _item_casilla(self, entrada: PlanArchivo) -> QTableWidgetItem:
        """Casilla «Mover» sincronizada con PlanArchivo.incluir."""

        item = QTableWidgetItem()
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        if entrada.estado in ESTADOS_SIN_CASILLA or entrada.destino_resuelto is None:
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            item.setCheckState(Qt.CheckState.Unchecked)
            return item

        item.setFlags(
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsUserCheckable
            | Qt.ItemFlag.ItemIsSelectable
        )
        item.setCheckState(
            Qt.CheckState.Checked if entrada.incluir else Qt.CheckState.Unchecked
        )

        return item

    def _item_texto(self, texto: str) -> QTableWidgetItem:
        item = QTableWidgetItem(texto)
        item.setFlags(
            Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        )
        return item

    def _item_destino(self, entrada: PlanArchivo) -> QTableWidgetItem:
        if entrada.destino_resuelto is None:
            return self._item_texto("—")

        texto = str(
            entrada.destino_resuelto.relative_to(self.ruta_destino)
        )
        item = self._item_texto(texto)
        item.setToolTip(str(entrada.destino_resuelto))

        return item

    def _item_estado(self, entrada: PlanArchivo) -> QTableWidgetItem:
        item = self._item_texto(tr(CLAVES_ESTADO[entrada.estado]))
        item.setForeground(QColor(COLORES_ESTADO[entrada.estado]))

        return item

    def _extension(self, entrada: PlanArchivo) -> str:
        return entrada.origen.suffix or "—"

    def _categoria(self, entrada: PlanArchivo) -> str:
        return entrada.categoria or tr("org.sin_categoria")

    def _cambiar_casilla(self, item: QTableWidgetItem):
        """Sincroniza la casilla «Mover» con el campo incluir del plan."""

        if self._cargando_tabla or item.column() != 0:
            return

        entrada = self.plan[item.row()]
        entrada.incluir = item.checkState() == Qt.CheckState.Checked
        self._actualizar_boton_organizar()

    # --- Ejecución (ejecutar_plan) ----------------------------------------

    def _organizar(self):
        """Pide confirmación y ejecuta el plan con el motor."""

        incluidos = [
            entrada
            for entrada in self.plan
            if entrada.incluir and entrada.destino_resuelto is not None
        ]

        if not incluidos:
            return

        respuesta = QMessageBox.question(
            self,
            tr("org.confirmar_titulo"),
            tr(
                "org.confirmar",
                total=len(incluidos),
                origen=self.ruta_origen,
                destino=self.ruta_destino,
            ),
        )

        if respuesta != QMessageBox.StandardButton.Yes:
            self._mensaje("org.cancelada")
            return

        self._iniciar_ejecucion()

    # --- Ejecución en segundo plano -----------------------------------------

    def _registrar_bloqueables(self):
        """Widgets interactivos que se deshabilitan durante la ejecución.

        Ningún widget se toca desde el hilo secundario: el bloqueo se
        aplica (y revierte) en el hilo de la interfaz.
        """

        self._bloqueables = [
            self.tabla,
            self.boton_organizar,
            self.campo_origen,
            self.campo_destino,
        ]
        self._bloqueables.extend(
            boton for boton in self.findChildren(QPushButton)
        )
        self._bloqueables = list(dict.fromkeys(self._bloqueables))

    def _bloquear_interfaz(self):
        for widget in self._bloqueables:
            if widget is not None:
                widget.setEnabled(False)

    def _desbloquear_interfaz(self):
        for widget in self._bloqueables:
            if widget is not None:
                widget.setEnabled(True)

        # El botón de organizar depende del plan, no del desbloqueo.
        self._actualizar_boton_organizar()

    def _iniciar_ejecucion(self):
        """Arranca el hilo que ejecuta el plan y bloquea la página."""

        if self._ejecutor is not None and self._ejecutor.isRunning():
            return

        self._bloquear_interfaz()

        marco_progreso = self.barra_progreso.parentWidget()
        marco_progreso.setVisible(True)
        self.barra_progreso.setRange(0, max(1, len(self.plan)))
        self.barra_progreso.setValue(0)
        self.texto_progreso.setText(
            tr(
                "org.progreso",
                procesados=0,
                pendientes=len(self.plan),
                fallidos=0,
            )
        )
        self._ejecutor = EjecutorEjecucion(self.plan, self)
        self._ejecutor.progreso.connect(self._al_progreso)
        self._ejecutor.terminado.connect(self._al_terminado)
        self._ejecutor.fallo.connect(self._al_fallo)
        self._ejecutor.finished.connect(self._al_hilo_terminado)
        self._ejecutor.start()

    def _al_progreso(self, procesados: int, total: int, fallidos: int):
        """Progreso en vivo (señal entregada en el hilo de la interfaz)."""

        # Defensa: cualquier progreso implica progreso visible.
        self.barra_progreso.parentWidget().setVisible(True)
        self.barra_progreso.setRange(0, max(1, total))
        self.barra_progreso.setValue(procesados)
        self.texto_progreso.setText(
            tr(
                "org.progreso",
                procesados=procesados,
                pendientes=max(0, total - procesados),
                fallidos=fallidos,
            )
        )

    def _al_terminado(self, resumen):
        """Fin correcto: resumen, mensajes y re-análisis (como antes)."""

        self._desbloquear_interfaz()

        if resumen.fallidos:
            detalle = "\n".join(
                f"· {nombre}: {error}" for nombre, error in resumen.errores
            )
            QMessageBox.warning(
                self,
                tr("org.errores_titulo"),
                tr("org.errores_cuerpo", total=resumen.fallidos, detalle=detalle),
            )

        self.texto_resumen = tr(
            "org.completada",
            movidos=resumen.movidos,
            omitidos=resumen.omitidos,
            fallidos=resumen.fallidos,
        )

        # La carpeta de origen cambió: recalculamos el plan antes de
        # mostrar el resumen (el análisis refresca la tabla).
        self._analizar()
        self._mensaje("org.completada",
                      movidos=resumen.movidos,
                      omitidos=resumen.omitidos,
                      fallidos=resumen.fallidos)

    def _al_fallo(self, mensaje: str):
        """La ejecución se interrumpió: la interfaz se recupera igual."""

        self._desbloquear_interfaz()

        QMessageBox.critical(
            self,
            tr("org.error_hilo_titulo"),
            tr("org.error_hilo", detalle=mensaje),
        )

        self._mensaje("org.interrumpida")

    def _al_hilo_terminado(self):
        """El hilo concluyó (bien o mal): se libera su referencia."""

        self._ocultar_progreso()

        if self._ejecutor is not None:
            self._ejecutor.deleteLater()
            self._ejecutor = None

    def _ocultar_progreso(self):
        self.barra_progreso.parentWidget().setVisible(False)
        self.barra_progreso.setValue(0)
        self.texto_progreso.setText("")

    # --- Estado de la interfaz ---------------------------------------------

    def config_actualizada(self):
        """Hook para el editor de categorías y preferencias.

        Se llama cuando otra página modifica config.json, para que la
        vista previa no siga mostrando un plan calculado con datos
        desactualizados. Solo invalida el plan: el mensaje de estado
        describe la selección de carpetas, que no ha cambiado, y se
        conserva tal cual para que retraducir() lo reaplique.
        """

        self._limpiar_plan()

    def _limpiar_plan(self):
        self.plan = []
        self._mostrar_plan()
        self._actualizar_boton_organizar()

    def _actualizar_boton_organizar(self):
        """El botón se habilita solo si hay archivos marcados para mover."""

        if self.boton_organizar is None:
            return

        hay_archivos = any(
            entrada.incluir and entrada.destino_resuelto is not None
            for entrada in self.plan
        )
        self.boton_organizar.setEnabled(hay_archivos)

    def _actualizar_estado(self):
        if self.texto_estado is None:
            return

        if self.ruta_origen and self.ruta_destino:
            self._mensaje("org.estado_ambas")
        elif self.ruta_origen:
            self._mensaje("org.estado_solo_origen")
        elif self.ruta_destino:
            self._mensaje("org.estado_solo_destino")
        else:
            self._mensaje("org.estado_inicial")
