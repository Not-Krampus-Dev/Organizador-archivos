# Ventana principal: shell de la navegación lateral contraíble.

# Estructura:
#
#   ┌──────────┬──────────────────────────┐
#   │ Título   │                          │
#   │──────────│                          │
#   │ Organi…  │   QStackedWidget         │
#   │ Categ.   │   · PaginaOrganizador    │
#   │ Prefe.   │   · PaginaCategorias     │
#   │       ◄  │   · PaginaPreferencias   │
#   └──────────┴──────────────────────────┘
#
# La barra alterna entre 220 px (iconos + nombres) y 64 px (solo
# iconos, con tooltips) mediante un botón alternador y una animación
# de 150 ms. Las páginas viven en un QStackedWidget: conservan su
# estado al cambiar de página o de ancho de barra.

from pathlib import Path

from PySide6.QtCore import (
    Qt,
    QEvent,
    QEasingCurve,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QSize,
    QTimer,
)
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from gui.i18n import cambiar_idioma, idioma_actual, tr
from gui.paginas.pagina_categorias import PaginaCategorias
from gui.paginas.pagina_organizador import PaginaOrganizador
from gui.paginas.pagina_preferencias import PaginaPreferencias
from organizador import config

# El título y el subtítulo de la aplicación se resuelven con tr().
ANCHO_EXPANDIDA = 220
ANCHO_CONTRAIDA = 64
DURACION_ANIMACION = 150  # ms

# Navegación automática: aparece al acercar el cursor y se oculta
# tras un retardo al retirarlo. Se persiste desde la página
# Preferencias; estas constantes son el punto de partida de sesión.
MODO_AUTOMATICO_POR_DEFECTO = True
RETARDO_OCULTAMIENTO_MS = 400

# (clave de nombre de la página, fábrica de la página, icono)
# El nombre visible se resuelve con tr(clave) en cada idioma.
PAGINAS = (
    ("nav.organizador", PaginaOrganizador, "organizador"),
    ("nav.categorias", PaginaCategorias, "categorias"),
    ("nav.preferencias", PaginaPreferencias, "preferencias"),
)

# Posición de Preferencias en PAGINAS (coincide con el índice del
# QStackedWidget y del botón de navegación).
INDICE_PREFERENCIAS = 2

CARPETA_RECURSOS = Path(__file__).resolve().parent / "recursos"

# Icono de la aplicación. Si aún no existe el archivo, la ventana
# arranca sin icono y sin errores: basta con colocar el .ico en
# gui/recursos/icono_app.ico para activarlo (la spec de PyInstaller
# usa el mismo archivo como icono del ejecutable).
NOMBRE_ICONO_APP = "icono_app.ico"


class VentanaPrincipal(QMainWindow):
    """Shell de la aplicación: barra lateral contraíble + páginas."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("app.titulo"))
        self.resize(900, 620)
        self._aplicar_icono_ventana()

        self.paginas = QStackedWidget()
        self.botones_navegacion = QButtonGroup(self)
        self.botones_navegacion.setExclusive(True)

        self.barra_expandida = True
        self._animacion_barra = None

        # Modo de navegación: automático (hover) o manual (botón ◄/►).
        self.modo_automatico = MODO_AUTOMATICO_POR_DEFECTO

        self._timer_ocultar = QTimer(self)
        self._timer_ocultar.setSingleShot(True)
        self._timer_ocultar.setInterval(RETARDO_OCULTAMIENTO_MS)
        self._timer_ocultar.timeout.connect(self._ocultar_barra_automatica)

        self.barra_lateral: QFrame | None = None
        self.titulo_barra: QLabel | None = None
        self.subtitulo_barra: QLabel | None = None
        self.boton_alternador: QPushButton | None = None
        self.boton_modo: QPushButton | None = None
        self.pagina_organizador: PaginaOrganizador | None = None
        self.pagina_categorias: PaginaCategorias | None = None
        self.pagina_preferencias: PaginaPreferencias | None = None

        # La primera vez que se muestra la ventana se leen las
        # preferencias de navegación del disco (una sola vez).
        self._preferencias_cargadas = False

        self._construir_interfaz()
        self.barra_lateral.installEventFilter(self)
        self._aplicar_estado_barra(expandida=True)

    def _aplicar_icono_ventana(self):
        """Icono de la ventana Qt (y heredado por la app).

        No hace nada si gui/recursos/icono_app.ico aún no existe.
        """

        ruta_icono = CARPETA_RECURSOS / NOMBRE_ICONO_APP

        if ruta_icono.exists():
            self.setWindowIcon(QIcon(str(ruta_icono)))

    def showEvent(self, evento):
        """Al mostrar la ventana en modo automático, la barra descansa
        contraída (64 px); se expande al acercar el cursor. En el primer
        show se leen las preferencias de navegación del disco."""

        super().showEvent(evento)

        if not self._preferencias_cargadas:
            self._preferencias_cargadas = True
            self._cargar_navegacion_de_disco()

        if self.modo_automatico and self.barra_expandida:
            self._aplicar_estado_barra(expandida=False)

    def _cargar_navegacion_de_disco(self):
        """Aplica las preferencias guardadas en config.json.

        Solo lectura: si el archivo no existe no se crea (sin efectos
        secundarios) y si está corrupto se usan los valores de sesión.
        También activa el idioma guardado.
        """

        ruta = self.pagina_preferencias.ruta_config

        if not Path(ruta).exists():
            return

        try:
            ajustes = config.cargar_config(ruta)
        except (ValueError, OSError):
            return

        self.aplicar_navegacion(
            ajustes.navegacion_automatica, ajustes.retardo_navegacion_ms
        )

        if ajustes.idioma != idioma_actual():
            cambiar_idioma(ajustes.idioma)
            self.retraducir()

    # --- Construcción de la interfaz -----------------------------------

    def _construir_interfaz(self):
        fondo = QWidget(objectName="fondo")
        layout = QHBoxLayout(fondo)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._construir_barra_lateral())
        layout.addWidget(self.paginas, stretch=1)

        self.setCentralWidget(fondo)

    def _construir_barra_lateral(self) -> QFrame:
        barra = QFrame(objectName="barra_lateral")
        self.barra_lateral = barra

        layout = QVBoxLayout(barra)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(6)

        self.titulo_barra = QLabel(tr("app.titulo"), objectName="titulo_app")
        self.titulo_barra.setWordWrap(True)

        self.subtitulo_barra = QLabel(
            tr("app.subtitulo"), objectName="subtitulo_app"
        )
        self.subtitulo_barra.setWordWrap(True)

        self.titulo_barra.setVisible(True)
        layout.addWidget(self.titulo_barra)
        layout.addWidget(self.subtitulo_barra)
        layout.addSpacing(16)

        for indice, (clave, fabrica, icono) in enumerate(PAGINAS):
            boton = QPushButton(tr(clave), objectName="boton_navegacion")
            boton.setIcon(self._icono(icono))
            boton.setIconSize(QSize(20, 20))
            boton.setCheckable(True)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.clicked.connect(self._cambiar_pagina)

            pagina = fabrica()
            self.paginas.addWidget(pagina)

            if fabrica is PaginaOrganizador:
                self.pagina_organizador = pagina
            elif fabrica is PaginaCategorias:
                self.pagina_categorias = pagina
            elif fabrica is PaginaPreferencias:
                self.pagina_preferencias = pagina

            self.botones_navegacion.addButton(boton, indice)
            layout.addWidget(boton)

        # Al guardar el editor de categorías, el organizador invalida
        # cualquier plan calculado con la configuración anterior.
        self.pagina_categorias.config_actualizada.connect(
            self.pagina_organizador.config_actualizada
        )

        # Al guardar Preferencias: navegación en vivo + plan invalidado.
        self.pagina_preferencias.config_actualizada.connect(
            self._config_guardada
        )

        layout.addStretch()

        boton_modo = QPushButton(objectName="boton_modo")
        boton_modo.setIcon(self._icono("automatico"))
        boton_modo.setIconSize(QSize(16, 16))
        boton_modo.setCheckable(True)
        boton_modo.setCursor(Qt.CursorShape.PointingHandCursor)
        boton_modo.clicked.connect(self._cambiar_modo_barra)
        self.boton_modo = boton_modo
        self._actualizar_boton_modo()

        alternador = QPushButton(objectName="boton_alternador")
        alternador.setIconSize(QSize(16, 16))
        alternador.setCursor(Qt.CursorShape.PointingHandCursor)
        alternador.clicked.connect(self._alternar_barra)
        self.boton_alternador = alternador

        fila_inferior = QHBoxLayout()
        fila_inferior.setSpacing(2)
        fila_inferior.addStretch()
        fila_inferior.addWidget(boton_modo)
        fila_inferior.addWidget(alternador)
        fila_inferior.addStretch()
        layout.addLayout(fila_inferior)

        return barra

    # --- Iconos ----------------------------------------------------------

    def _icono(self, nombre: str) -> QIcon:
        """Carga un icono SVG de gui/recursos/."""

        return QIcon(str(CARPETA_RECURSOS / f"{nombre}.svg"))

    # --- Navegación ------------------------------------------------------

    def _cambiar_pagina(self, *_):
        boton = self.botones_navegacion.checkedButton()

        if boton is not None:
            indice = self.botones_navegacion.id(boton)
            self.paginas.setCurrentIndex(indice)

            # Al entrar en Preferencias se le entrega el estado de
            # navegación de la sesión (el botón de la barra cambia el
            # modo sin escribir en disco).
            if indice == INDICE_PREFERENCIAS and self.pagina_preferencias:
                self.pagina_preferencias.sincronizar_navegacion(
                    self.modo_automatico, self._timer_ocultar.interval()
                )

    # --- Preferencias de navegación -----------------------------------------

    def aplicar_navegacion(self, automatica: bool, retardo_ms: int):
        """Aplica modo y retardo de navegación en vivo.

        Lo usan la carga inicial del disco y el guardado de la página
        Preferencias: cambia el modo de la sesión y el intervalo del
        timer de ocultamiento sin reiniciar la aplicación.
        """

        self.modo_automatico = automatica
        self._timer_ocultar.setInterval(retardo_ms)
        self._timer_ocultar.stop()
        self._actualizar_boton_modo()

    def _config_guardada(self, ajustes):
        """Slot de `pagina_preferencias.config_actualizada`."""

        self.aplicar_navegacion(
            ajustes.navegacion_automatica, ajustes.retardo_navegacion_ms
        )

        if ajustes.idioma != idioma_actual():
            cambiar_idioma(ajustes.idioma)
            self.retraducir()

        # El plan del organizador quedó calculado con la configuración
        # anterior: se invalida.
        self.pagina_organizador.config_actualizada()

    # --- Barra lateral: estados y animación -------------------------------

    def _aplicar_estado_barra(self, expandida: bool):
        """Aplica un estado de la barra de forma inmediata.

        Cambia el ancho (220 px si expandida, 64 px si contraída), los
        textos de los botones, su visibilidad y los tooltips. Es la
        función que tests e interfaz usan como fuente de verdad; la
        animación solo orquesta cuándo se llama.
        """

        ancho = ANCHO_EXPANDIDA if expandida else ANCHO_CONTRAIDA

        self.barra_lateral.setMinimumWidth(ancho)
        self.barra_lateral.setMaximumWidth(ancho)
        self.barra_expandida = expandida

        self._actualizar_textos_barra(expandida)
        self._actualizar_icono_alternador(expandida)
        self._refrescar_estilo_barra()

    def _actualizar_textos_barra(self, expandida: bool):
        """Muestra u oculta textos y asigna tooltips de la barra.

        - Expandida: título, subtítulo y nombres visibles, sin tooltips.
        - Contraída: solo iconos; el nombre de cada página pasa al
          tooltip de su botón.
        """

        self.titulo_barra.setVisible(expandida)
        self.subtitulo_barra.setVisible(expandida)

        for indice, boton in enumerate(self.botones_navegacion.buttons()):
            clave = PAGINAS[indice][0]

            if expandida:
                boton.setText(tr(clave))
                boton.setToolTip("")
            else:
                boton.setText("")
                boton.setToolTip(tr(clave))

        # Propiedad dinámica: la hoja de estilos centra los iconos
        # cuando la barra está contraída.
        self.barra_lateral.setProperty("contraida", not expandida)

    def _actualizar_icono_alternador(self, expandida: bool):
        """Chevron «◄» si está expandida (para contraer) y «►» al contrario."""

        self.boton_alternador.setIcon(
            self._icono("contraer" if expandida else "expandir")
        )
        self.boton_alternador.setToolTip(
            tr("nav.contraer") if expandida else tr("nav.expandir")
        )

    def _refrescar_estilo_barra(self):
        """Reaplica la hoja de estilos tras cambiar la propiedad dinámica."""

        widgets = [self.barra_lateral]
        widgets.extend(self.barra_lateral.findChildren(QPushButton))

        for widget in widgets:
            estilo = widget.style()
            estilo.unpolish(widget)
            estilo.polish(widget)

    def _alternar_barra(self):
        """Invierte el estado de la barra con una animación de 150 ms."""

        self.barra_expandida = not self.barra_expandida
        self._animar_barra(self.barra_expandida)

    def _animar_barra(self, expandida: bool):
        """Anima la barra hacia un estado concreto (150 ms, OutCubic).

        - Al contraer: los textos desaparecen al iniciar y el chevron
          cambia al terminar.
        - Al expandir: el chevron cambia al iniciar y los textos
          aparecen al terminar.
        """

        self.barra_expandida = expandida

        # Si había una animación en curso, se interrumpe sin aplicar
        # su estado final (el nuevo estado lo corrige al terminar).
        if self._animacion_barra is not None:
            try:
                self._animacion_barra.finished.disconnect()
            except (RuntimeError, TypeError):
                pass
            self._animacion_barra.stop()
            self._animacion_barra = None

        if not expandida:
            self._actualizar_textos_barra(False)
        else:
            self._actualizar_icono_alternador(True)

        ancho_final = ANCHO_EXPANDIDA if expandida else ANCHO_CONTRAIDA

        grupo = QParallelAnimationGroup(self)

        for propiedad in (b"minimumWidth", b"maximumWidth"):
            animacion = QPropertyAnimation(self.barra_lateral, propiedad, self)
            animacion.setDuration(DURACION_ANIMACION)
            animacion.setEasingCurve(QEasingCurve.Type.OutCubic)
            animacion.setStartValue(self.barra_lateral.width())
            animacion.setEndValue(ancho_final)
            grupo.addAnimation(animacion)

        grupo.finished.connect(lambda: self._aplicar_estado_barra(expandida))

        self._animacion_barra = grupo
        grupo.start()

    # --- Modo automático (auto-hide) ---------------------------------------

    def eventFilter(self, fuente, evento):
        """Observa la entrada y salida del cursor en la barra lateral.

        Los controles internos de la barra están dentro de su rectángulo:
        mover el cursor entre ellos no genera Leave, por lo que no hay
        parpadeos al pasar entre botones.
        """

        if self.modo_automatico and fuente is self.barra_lateral:
            tipo = evento.type()

            if tipo is QEvent.Type.Enter:
                self._al_entrar_barra()
            elif tipo is QEvent.Type.Leave:
                self._al_salir_barra()

        return super().eventFilter(fuente, evento)

    def _al_entrar_barra(self):
        """Cursor sobre la barra: cancela el ocultamiento pendiente y
        expande si la barra estaba en reposo."""

        self._timer_ocultar.stop()

        if not self.barra_expandida:
            self._animar_barra(expandida=True)

    def _al_salir_barra(self):
        """Cursor fuera de la barra: programa el ocultamiento (400 ms).

        Si el cursor vuelve a entrar durante la espera, el timer se
        cancela en _al_entrar_barra y la barra permanece expandida.
        """

        if self.modo_automatico and self.barra_expandida:
            self._timer_ocultar.start()

    def _ocultar_barra_automatica(self):
        """Disparo del timer: colapsa la barra a su estado de reposo."""

        if self.modo_automatico and self.barra_expandida:
            self._animar_barra(expandida=False)

    def _cambiar_modo_barra(self, activar=None):
        """Alterna entre modo automático (hover) y manual (botón ◄/►).

        Al pasar a manual se cancela cualquier ocultamiento pendiente;
        el ancho actual se conserva y el usuario decide con el botón.
        """

        if activar is None:
            activar = not self.modo_automatico

        self.modo_automatico = activar
        self._timer_ocultar.stop()
        self._actualizar_boton_modo()

    def _actualizar_boton_modo(self):
        """Sincroniza el estado visual y el tooltip del botón de modo."""

        if self.boton_modo is None:
            return

        self.boton_modo.setChecked(self.modo_automatico)
        self.boton_modo.setToolTip(
            tr("nav.modo_automatico")
            if self.modo_automatico
            else tr("nav.modo_manual")
        )

    # --- Retraducción -------------------------------------------------------

    def retraducir(self):
        """Reaplica todos los textos del shell y de las páginas.

        Llamado al cambiar de idioma (arranque o Preferencias): sin
        reiniciar la aplicación.
        """

        self.setWindowTitle(tr("app.titulo"))
        self.titulo_barra.setText(tr("app.titulo"))
        self.subtitulo_barra.setText(tr("app.subtitulo"))

        self._actualizar_textos_barra(self.barra_expandida)
        self._actualizar_icono_alternador(self.barra_expandida)
        self._actualizar_boton_modo()

        for pagina in (
            self.pagina_organizador,
            self.pagina_categorias,
            self.pagina_preferencias,
        ):
            pagina.retraducir()
