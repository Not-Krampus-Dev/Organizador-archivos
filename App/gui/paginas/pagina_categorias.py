# Página «Categorías»: editor maestro-detalle.

# Lista de categorías a la izquierda; a la derecha, el nombre, la
# subcarpeta de destino y las extensiones de la categoría seleccionada.
#
# Las extensiones se muestran como etiquetas compactas («chips») en un
# FlowLayout; cada chip lleva un botón «×» para eliminarse. El resto del
# modelo no cambia: los cambios se aplican al vuelo sobre una copia en
# memoria de la configuración, «Guardar cambios» los valida con
# config.validar_config() y los escribe con config.guardar_config().
# Al guardar, se emite config_actualizada para que el organizador
# invalide cualquier plan calculado con datos obsoletos.

from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QLayout,
    QVBoxLayout,
    QWidget,
)

from gui.i18n import tr
from gui.rutas import ruta_config
from organizador import config
from organizador.models import Categoria

# Configuración centralizada: App/config.json en desarrollo y
# %APPDATA%\OrganizadorArchivos\config.json en la app empaquetada.
RUTA_CONFIG = ruta_config()

# Categorías predeterminadas: nombre canónico en config.json → clave de
# traducción del nombre visible. Solo afecta a la LISTA (visualización):
# el modelo y el campo de nombre siguen usando el nombre canónico, de
# modo que los nombres personalizados nunca se traducen.
NOMBRES_PREDETERMINADOS = {
    "Imagenes": "cat.imagenes",
    "Documentos": "cat.documentos",
    "Música": "cat.musica",
    "Vídeos": "cat.videos",
    "Comprimidos": "cat.comprimidos",
    "Programación": "cat.programacion",
    "Ejecutables": "cat.ejecutables",
    "Fuentes": "cat.fuentes",
    "Datos": "cat.datos",
    "Presentaciones": "cat.presentaciones",
    "Hojas de cálculo": "cat.hojas_calculo",
}


class FlowLayout(QLayout):
    """Layout que apila widgets en filas y pasa a la siguiente cuando
    se agota el ancho disponible (para los chips de extensiones)."""

    def __init__(self, parent=None, espaciado=8):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self._elementos: list = []
        self._espaciado = espaciado

    def addItem(self, item):
        self._elementos.append(item)

    def count(self) -> int:
        return len(self._elementos)

    def itemAt(self, indice):
        if 0 <= indice < len(self._elementos):
            return self._elementos[indice]
        return None

    def takeAt(self, indice):
        if 0 <= indice < len(self._elementos):
            return self._elementos.pop(indice)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, ancho) -> int:
        altura = self._calcular_distribucion(QRect(0, 0, ancho, 0))
        return altura

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._calcular_distribucion(rect, aplicar=True)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        tamaño = QSize()

        for item in self._elementos:
            sugerido = item.sizeHint()
            tamaño = tamaño.expandedTo(sugerido)

        margenes = self.contentsMargins()
        tamaño += QSize(margenes.left() + margenes.right(), margenes.top() + margenes.bottom())
        return tamaño

    def _calcular_distribucion(self, rect: QRect, aplicar=False) -> int:
        """Distribuye los elementos en filas dentro de `rect`.

        Si `aplicar` es True, mueve cada elemento a su posición final.
        Devuelve la altura total usada.
        """

        margenes = self.contentsMargins()
        x = rect.x() + margenes.left()
        y = rect.y() + margenes.top()
        borde_derecho = rect.right() - margenes.right()
        altura_linea = 0

        for item in self._elementos:
            sugerido = item.sizeHint()
            ancho = sugerido.width()
            alto = sugerido.height()

            siguiente = x + ancho + self._espaciado
            if siguiente > borde_derecho and altura_linea > 0:
                # Nueva fila.
                x = rect.x() + margenes.left()
                y = y + altura_linea + self._espaciado
                altura_linea = 0

            if aplicar:
                item.setGeometry(QRect(QPoint(x, y), sugerido))

            x = x + ancho + self._espaciado
            altura_linea = max(altura_linea, alto)

        return y + altura_linea - rect.y() + margenes.bottom()


class ChipExtension(QFrame):
    """Etiqueta compacta de una extensión con botón «×» para eliminarla."""

    def __init__(self, texto: str, al_eliminar):
        super().__init__(objectName="chip_extension")
        self.texto = texto

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 3, 5, 3)
        layout.setSpacing(6)

        layout.addWidget(QLabel(texto))

        boton = QPushButton("×", objectName="boton_cerrar_etiqueta")
        boton.setFixedSize(18, 18)
        boton.setCursor(Qt.CursorShape.PointingHandCursor)
        boton.clicked.connect(lambda: al_eliminar(texto))
        layout.addWidget(boton)


class PaginaCategorias(QWidget):
    """Editor de categorías, extensiones y subcarpetas de destino."""

    # Señal emitida tras guardar la configuración en disco.
    config_actualizada = Signal()

    def __init__(self):
        super().__init__()

        self.ruta_config = RUTA_CONFIG
        self.ajustes = None
        self._cambios_pendientes = False
        self._sincronizando = False

        # Último mensaje de estado (clave + parámetros) para retraducir.
        self._ultimo_mensaje = ("ed.sin_seleccion", {})

        self.lista_categorias = None
        self.campo_nombre = None
        self.campo_destino = None
        self.panel_chips = None
        self.campo_extension = None
        self.boton_guardar = None
        self.texto_estado = None
        self.panel_edicion = None

        # Referencias para retraducir.
        self.panel_lista = None
        self.boton_nueva = None
        self.boton_eliminar = None
        self.etiqueta_nombre = None
        self.etiqueta_destino = None
        self.etiqueta_extensiones = None
        self.boton_anadir = None

        self._construir_interfaz()

    def showEvent(self, evento):
        """Carga la configuración del disco la primera vez que la
        página se muestra (si no se había cargado ya)."""

        super().showEvent(evento)

        if self.ajustes is None:
            self._cargar_config()

    # --- Carga y estado ---------------------------------------------------

    def _cargar_config(self):
        """Carga la configuración desde config.json y llena la lista."""

        self.ajustes = config.cargar_config(self.ruta_config)
        self._cambios_pendientes = False
        self._actualizar_boton_guardar()
        self._recargar_lista(seleccionar=0)

    def _cambios_pendientes_marcar(self):
        self._cambios_pendientes = True
        self._actualizar_boton_guardar()
        self._mostrar_aviso("ed.con_cambios")

    def _actualizar_boton_guardar(self):
        if self.boton_guardar is not None:
            self.boton_guardar.setEnabled(
                self._cambios_pendientes and self.ajustes is not None
            )

    # --- Retraducción -------------------------------------------------------

    def retraducir(self):
        """Reaplica todos los textos de la página (cambio de idioma)."""

        self.panel_lista.setTitle(tr("ed.grupo_categorias"))
        self.panel_edicion.setTitle(tr("ed.grupo_edicion"))
        self.boton_nueva.setText(tr("ed.nueva"))
        self.boton_eliminar.setText(tr("ed.eliminar"))
        self.etiqueta_nombre.setText(tr("ed.nombre"))
        self.etiqueta_destino.setText(tr("ed.destino"))
        self.etiqueta_extensiones.setText(tr("ed.extensiones"))
        self.campo_extension.setPlaceholderText(".ext")
        self.boton_anadir.setText(tr("ed.anadir"))
        self.boton_guardar.setText(tr("ed.guardar"))

        clave, parametros = self._ultimo_mensaje

        # El mensaje de selección muestra el nombre visible: se recalcula
        # en el idioma nuevo (el resto de mensajes no lleva nombres).
        if clave == "ed.seleccionada" and self._categoria_actual() is not None:
            parametros = {"nombre": self._nombre_visible(self._categoria_actual())}

        self.texto_estado.setText(tr(clave, **parametros))

        # Nombres visibles de la lista, actualizados en el sitio para
        # conservar la selección y los cambios pendientes (que viven en
        # self.ajustes, no en los widgets).
        if self.ajustes is not None:
            for fila, categoria in enumerate(self.ajustes.categorias):
                item = self.lista_categorias.item(fila)
                if item is not None:
                    item.setText(
                        self._nombre_visible(categoria) or tr("ed.sin_nombre")
                    )

    # --- Construcción de la interfaz ---------------------------------------

    def _construir_interfaz(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(20, 16, 20, 16)
        raiz.setSpacing(10)

        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(14)

        cuerpo.addWidget(self._construir_panel_lista())
        cuerpo.addWidget(self._construir_panel_edicion(), stretch=1)

        raiz.addLayout(cuerpo, stretch=1)
        raiz.addWidget(self._construir_barra_estado())

    def _construir_panel_lista(self) -> QGroupBox:
        panel = QGroupBox(tr("ed.grupo_categorias"))
        self.panel_lista = panel

        layout = QVBoxLayout(panel)
        layout.setSpacing(8)

        self.lista_categorias = QListWidget(objectName="lista_categorias")
        self.lista_categorias.currentRowChanged.connect(
            self._al_seleccionar_categoria
        )
        layout.addWidget(self.lista_categorias)

        fila = QHBoxLayout()
        fila.setSpacing(8)

        self.boton_nueva = QPushButton(tr("ed.nueva"), objectName="boton_nueva")
        self.boton_nueva.clicked.connect(self._crear_categoria)

        self.boton_eliminar = QPushButton(
            tr("ed.eliminar"), objectName="boton_eliminar"
        )
        self.boton_eliminar.clicked.connect(self._eliminar_categoria)

        fila.addWidget(self.boton_nueva)
        fila.addWidget(self.boton_eliminar)
        layout.addLayout(fila)

        return panel

    def _construir_panel_edicion(self) -> QGroupBox:
        panel = QGroupBox(tr("ed.grupo_edicion"))
        self.panel_edicion = panel

        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        formulario = QFormLayout()
        formulario.setSpacing(8)

        self.campo_nombre = QLineEdit(objectName="campo_nombre")
        self.campo_nombre.textChanged.connect(self._nombre_editado)

        self.campo_destino = QLineEdit(objectName="campo_destino")
        self.campo_destino.textChanged.connect(self._destino_editado)

        self.etiqueta_nombre = QLabel(tr("ed.nombre"))
        self.etiqueta_destino = QLabel(tr("ed.destino"))

        formulario.addRow(self.etiqueta_nombre, self.campo_nombre)
        formulario.addRow(self.etiqueta_destino, self.campo_destino)
        layout.addLayout(formulario)

        self.etiqueta_extensiones = QLabel(tr("ed.extensiones"))
        layout.addWidget(self.etiqueta_extensiones)

        # Contenedor de chips con FlowLayout: aprovecha el ancho
        # disponible apilando filas.
        self.panel_chips = QWidget(objectName="panel_chips")
        self.layout_chips = FlowLayout(self.panel_chips, espaciado=6)
        self.layout_chips.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)

        fila_extensiones = QHBoxLayout()
        fila_extensiones.setSpacing(8)

        self.campo_extension = QLineEdit(objectName="campo_extension")
        self.campo_extension.setPlaceholderText(".ext")

        self.boton_anadir = QPushButton(tr("ed.anadir"), objectName="boton_anadir")
        self.boton_anadir.clicked.connect(self._anadir_extension)

        fila_extensiones.addWidget(self.campo_extension, stretch=1)
        fila_extensiones.addWidget(self.boton_anadir)
        layout.addWidget(self.panel_chips, stretch=1)
        layout.addLayout(fila_extensiones)

        fila_guardar = QHBoxLayout()
        fila_guardar.addStretch()

        self.boton_guardar = QPushButton(
            tr("ed.guardar"), objectName="boton_primario"
        )
        self.boton_guardar.setEnabled(False)
        self.boton_guardar.clicked.connect(self._guardar)

        fila_guardar.addWidget(self.boton_guardar)
        layout.addLayout(fila_guardar)

        return panel

    def _construir_barra_estado(self) -> QLabel:
        self.texto_estado = QLabel(
            tr("ed.sin_seleccion"), objectName="texto_estado"
        )
        return self.texto_estado

    # --- Listado de categorías ----------------------------------------------

    def _recargar_lista(self, seleccionar=None):
        """Reconstruye la lista a partir de la configuración en memoria."""

        self._sincronizando = True

        self.lista_categorias.blockSignals(True)
        self.lista_categorias.clear()

        for categoria in self.ajustes.categorias:
            self.lista_categorias.addItem(
                self._nombre_visible(categoria) or tr("ed.sin_nombre")
            )

        self.lista_categorias.blockSignals(False)
        self._sincronizando = False

        if seleccionar is None:
            seleccionar = self.lista_categorias.currentRow()

        if self.lista_categorias.count() > 0:
            fila = max(0, min(seleccionar, self.lista_categorias.count() - 1))
            self.lista_categorias.setCurrentRow(fila)
        else:
            self._al_seleccionar_categoria(-1)

    def _al_seleccionar_categoria(self, fila: int):
        """Muestra la categoría elegida en el panel de edición."""

        if self._sincronizando:
            return

        categoria = self._categoria_en(fila)

        if categoria is None:
            self.panel_edicion.setEnabled(False)
            self.campo_nombre.clear()
            self.campo_destino.clear()
            self._refrescar_extensiones()
            self._mostrar_aviso("ed.sin_seleccion")
            return

        self.panel_edicion.setEnabled(True)

        self._sincronizando = True
        self.campo_nombre.setText(categoria.nombre)
        self.campo_destino.setText(categoria.destino)
        self._sincronizando = False

        self._refrescar_extensiones()
        self._mostrar_aviso(
            "ed.seleccionada", nombre=self._nombre_visible(categoria)
        )

    def _categoria_en(self, fila: int) -> Categoria | None:
        if self.ajustes is None or not 0 <= fila < len(self.ajustes.categorias):
            return None

        return self.ajustes.categorias[fila]

    def _categoria_actual(self) -> Categoria | None:
        if self.lista_categorias is None:
            return None

        return self._categoria_en(self.lista_categorias.currentRow())

    def _nombre_visible(self, categoria: Categoria) -> str:
        """Nombre mostrado en la lista: traducido si es predeterminada,
        tal cual si es personalizada."""

        clave = NOMBRES_PREDETERMINADOS.get(categoria.nombre)
        return tr(clave) if clave is not None else categoria.nombre

    def extensiones_en_pantalla(self) -> list[str]:
        """Textos de los chips visibles, en su orden (uso de pruebas)."""

        return [
            chip.texto
            for chip in self.panel_chips.findChildren(ChipExtension)
        ]

    # --- Edición ------------------------------------------------------------

    def _nombre_editado(self, texto: str):
        if self._sincronizando:
            return

        categoria = self._categoria_actual()
        if categoria is None:
            return

        nombre_anterior = categoria.nombre
        categoria.nombre = texto

        # Si la subcarpeta seguía el patrón por defecto (igual al nombre),
        # la actualizamos junto con el nombre.
        if self.campo_destino.text() == nombre_anterior:
            self.campo_destino.blockSignals(True)
            self.campo_destino.setText(texto)
            self.campo_destino.blockSignals(False)
            categoria.destino = texto

        item = self.lista_categorias.currentItem()
        if item is not None:
            item.setText(
                self._nombre_visible(categoria) or tr("ed.sin_nombre")
            )

        self._cambios_pendientes_marcar()

    def _destino_editado(self, texto: str):
        if self._sincronizando:
            return

        categoria = self._categoria_actual()
        if categoria is None:
            return

        categoria.destino = texto.strip()
        self._cambios_pendientes_marcar()

    def _anadir_extension(self):
        texto = self.campo_extension.text().strip()

        categoria = self._categoria_actual()
        if categoria is None or not texto:
            return

        extension = texto.lower()
        if not extension.startswith("."):
            extension = "." + extension

        if extension in categoria.extensiones:
            self._mostrar_error(
                "ed.ext_duplicada", extension=extension, nombre=categoria.nombre
            )
            return

        otras = {
            extension_otra
            for otra in self.ajustes.categorias
            if otra is not categoria
            for extension_otra in otra.extensiones
        }

        if extension in otras:
            self._mostrar_error("ed.ext_otra", extension=extension)
            return

        categoria.extensiones.append(extension)
        self.campo_extension.clear()
        self._refrescar_extensiones()
        self._cambios_pendientes_marcar()

    def _eliminar_extension(self, texto: str):
        """Elimina la extensión cuyo chip «×» fue pulsado."""

        categoria = self._categoria_actual()
        if categoria is None or texto not in categoria.extensiones:
            return

        categoria.extensiones.remove(texto)
        self._refrescar_extensiones()
        self._cambios_pendientes_marcar()

    def _refrescar_extensiones(self):
        """Reconstruye los chips de la categoría seleccionada."""

        while self.layout_chips.count():
            item = self.layout_chips.takeAt(0)
            widget = item.widget()
            if widget is not None:
                # Se retira del panel ya (deleteLater se completa luego
                # con el bucle de eventos).
                widget.setParent(None)
                widget.deleteLater()

        categoria = self._categoria_actual()
        if categoria is None:
            return

        for extension in categoria.extensiones:
            self.layout_chips.addWidget(ChipExtension(extension, self._eliminar_extension))

        self.layout_chips.invalidate()
        self.panel_chips.setMinimumSize(QSize(0, 0))
        self.layout_chips.activate()

    # --- Crear y eliminar categorías ----------------------------------------

    def _crear_categoria(self):
        if self.ajustes is None:
            return

        nombre = tr("ed.nueva_categoria")
        contador = 2

        while any(
            categoria.nombre.lower() == nombre.lower()
            for categoria in self.ajustes.categorias
        ):
            nombre = f"{tr('ed.nueva_categoria')} {contador}"
            contador += 1

        categoria = Categoria(nombre=nombre, extensiones=[], destino="")
        self.ajustes.categorias.append(categoria)

        self._cambios_pendientes_marcar()
        self._recargar_lista(seleccionar=len(self.ajustes.categorias) - 1)

    def _eliminar_categoria(self):
        if self.ajustes is None:
            return

        fila = self.lista_categorias.currentRow()
        if fila < 0:
            return

        del self.ajustes.categorias[fila]

        self._cambios_pendientes_marcar()
        self._recargar_lista(seleccionar=min(fila, len(self.ajustes.categorias) - 1))

    # --- Guardar ---------------------------------------------------------------

    def _guardar(self):
        """Valida la configuración en memoria y la escribe en disco."""

        if self.ajustes is None or not self._cambios_pendientes:
            return

        try:
            self.ajustes = config.validar_config(self.ajustes)

        except ValueError as error:
            self._mostrar_error("ed.error_guardar", detalle=error)
            return

        try:
            config.guardar_config(self.ruta_config, self.ajustes)

        except OSError as error:
            self._mostrar_error("ed.error_escritura", detalle=error)
            return

        self._cambios_pendientes = False
        self._actualizar_boton_guardar()
        self._recargar_lista()
        self._mostrar_aviso("ed.guardada")
        self.config_actualizada.emit()

    # --- Mensajes de estado ------------------------------------------------------

    def _mostrar_aviso(self, clave: str, **parametros):
        """Fija el mensaje de estado (se recuerda para retraducir)."""

        self._ultimo_mensaje = (clave, parametros)
        self.texto_estado.setText(tr(clave, **parametros))

    def _mostrar_error(self, clave: str, **parametros):
        self._mostrar_aviso(clave, **parametros)
