# Pruebas de la interfaz gráfica (Etapa: conexión con el motor).

# Se ejecutan con la plataforma "offscreen" de Qt, sin abrir ventanas:
#   App\.venv\Scripts\python.exe -m unittest discover -s tests -v
#
# Usan carpetas temporales y no mueven archivos reales del proyecto.

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# La plataforma debe fijarse antes de importar PySide6.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QPushButton

from gui.i18n import tr
from gui.main_window import PAGINAS, VentanaPrincipal
from organizador import config
from organizador.models import ComportamientoDesconocidos, EstadoPlan

APP = QApplication.instance() or QApplication(sys.argv)

CONFIRMAR_SI = QMessageBox.StandardButton.Yes
CONFIRMAR_NO = QMessageBox.StandardButton.No


class PruebaGUI(unittest.TestCase):
    """Base: ventana con carpetas temporales de origen y destino.

    `self.ventana` apunta directamente a la página «Organizador»,
    donde vive toda la lógica funcional.
    """

    def setUp(self):
        self.carpeta_temporal = tempfile.TemporaryDirectory()
        self.raiz = Path(self.carpeta_temporal.name)
        self.origen = self.raiz / "origen"
        self.destino = self.raiz / "destino"
        self.origen.mkdir()
        self.destino.mkdir()

        self.config_temporal = self.raiz / "config.json"

        self.shell = VentanaPrincipal()
        self.ventana = self.shell.pagina_organizador
        self.ventana.ruta_config = self.config_temporal
        self.ventana.ruta_origen = self.origen
        self.ventana.ruta_destino = self.destino

    def tearDown(self):
        self.carpeta_temporal.cleanup()

    def crear_archivo(self, nombre, contenido="prueba"):
        ruta = self.origen / nombre
        ruta.write_text(contenido, encoding="utf-8")
        return ruta

    def analizar(self):
        self.ventana._analizar()


class TestAnalisis(PruebaGUI):

    def test_llena_la_tabla_sin_mover_archivos(self):
        self.crear_archivo("foto.png")
        self.crear_archivo("datos.json")
        self.crear_archivo("desktop.ini")

        self.analizar()

        tabla = self.ventana.tabla
        self.assertEqual(tabla.rowCount(), 3)

        # Ningún archivo se movió durante el análisis.
        self.assertEqual(
            {ruta.name for ruta in self.origen.iterdir()},
            {"foto.png", "datos.json", "desktop.ini"},
        )
        self.assertFalse(self.destino.exists() and any(self.destino.iterdir()))

    def test_columnas_con_datos_correctos(self):
        self.crear_archivo("foto.png")

        self.analizar()

        self.assertEqual(self.ventana.tabla.item(0, 1).text(), "foto.png")
        self.assertEqual(self.ventana.tabla.item(0, 2).text(), ".png")
        self.assertEqual(self.ventana.tabla.item(0, 3).text(), "Imagenes")
        self.assertEqual(self.ventana.tabla.item(0, 5).text(), "Listo")

    def test_estados_en_la_tabla(self):
        self.crear_archivo("foto.png")        # Listo
        self.crear_archivo("raro.xyz")        # Advertido (config por defecto: otros)
        self.crear_archivo("desktop.ini")     # Ignorado

        self.analizar()

        estados = {
            self.ventana.tabla.item(fila, 1).text(): self.ventana.tabla.item(fila, 5).text()
            for fila in range(self.ventana.tabla.rowCount())
        }

        self.assertEqual(estados["foto.png"], "Listo")
        self.assertEqual(estados["desktop.ini"], "Ignorado")
        self.assertIn(estados["raro.xyz"], {"Listo", "Advertido"})

    def test_conflicto_detectado_cuando_el_destino_esta_ocupado(self):
        self.crear_archivo("foto.png")
        ocupado = self.destino / "Imagenes" / "foto.png"
        ocupado.parent.mkdir(parents=True)
        ocupado.write_text("existe", encoding="utf-8")

        self.analizar()

        self.assertEqual(self.ventana.tabla.item(0, 5).text(), "Conflicto")

    def test_sin_carpetas_muestra_mensaje_y_no_analiza(self):
        self.ventana.ruta_destino = None

        self.analizar()

        self.assertEqual(self.ventana.tabla.rowCount(), 0)
        self.assertIn("destino", self.ventana.texto_estado.text().lower())

    def test_carpetas_iguales_rechazadas_por_la_validacion(self):
        self.ventana.ruta_destino = self.origen

        valida, (clave, parametros) = self.ventana._carpetas_validas()

        self.assertFalse(valida)
        self.assertIn("misma", tr(clave, **parametros).lower())


class TestCasillas(PruebaGUI):

    def test_casillas_sincronizadas_con_incluir(self):
        self.crear_archivo("foto.png")
        self.crear_archivo("datos.json")

        self.analizar()

        self.assertTrue(self.ventana.plan[0].incluir)
        self.assertTrue(self.ventana.boton_organizar.isEnabled())

        item = self.ventana.tabla.item(0, 0)
        item.setCheckState(Qt.CheckState.Unchecked)

        self.assertFalse(self.ventana.plan[0].incluir)
        self.assertTrue(self.ventana.boton_organizar.isEnabled())

        item2 = self.ventana.tabla.item(1, 0)
        item2.setCheckState(Qt.CheckState.Unchecked)

        self.assertFalse(self.ventana.plan[1].incluir)
        self.assertFalse(self.ventana.boton_organizar.isEnabled())

    def test_archivo_ignorado_no_tiene_casilla(self):
        self.crear_archivo("desktop.ini")

        self.analizar()

        item = self.ventana.tabla.item(0, 0)
        self.assertFalse(bool(item.flags() & Qt.ItemFlag.ItemIsUserCheckable))
        self.assertFalse(self.ventana.plan[0].incluir)


class TestEjecucion(PruebaGUI):

    def terminar_ejecucion(self):
        """Espera al hilo de ejecución y procesa las señales pendientes."""

        if self.ventana._ejecutor is not None:
            self.ventana._ejecutor.wait()

        QApplication.processEvents()

    def test_organizar_mueve_tras_confirmacion(self):
        self.crear_archivo("foto.png")
        self.crear_archivo("datos.json")

        self.analizar()

        with patch(
            "gui.paginas.pagina_organizador.QMessageBox.question",
            staticmethod(lambda *args, **kwargs: CONFIRMAR_SI),
        ):
            self.ventana._organizar()
        self.terminar_ejecucion()

        self.assertTrue((self.destino / "Imagenes" / "foto.png").is_file())
        self.assertTrue((self.destino / "Datos" / "datos.json").is_file())
        self.assertIn("2 movidos", self.ventana.texto_estado.text())

    def test_cancelacion_no_mueve_nada(self):
        self.crear_archivo("foto.png")

        self.analizar()

        with patch(
            "gui.paginas.pagina_organizador.QMessageBox.question",
            staticmethod(lambda *args, **kwargs: CONFIRMAR_NO),
        ):
            self.ventana._organizar()

        self.assertTrue((self.origen / "foto.png").is_file())
        self.assertIn("cancelada", self.ventana.texto_estado.text().lower())

    def test_tabla_refrescada_despues_de_organizar(self):
        self.crear_archivo("foto.png")

        self.analizar()

        with patch(
            "gui.paginas.pagina_organizador.QMessageBox.question",
            staticmethod(lambda *args, **kwargs: CONFIRMAR_SI),
        ):
            self.ventana._organizar()
        self.terminar_ejecucion()

        # Tras mover todo, el plan recalculado queda vacío y el botón
        # de organización vuelve a deshabilitarse.
        self.assertEqual(self.ventana.tabla.rowCount(), 0)
        self.assertFalse(self.ventana.boton_organizar.isEnabled())
        self.assertEqual(list(self.origen.iterdir()), [])

    def test_sin_archivos_incluidos_no_hace_nada(self):
        self.crear_archivo("foto.png")

        self.analizar()

        for fila in range(self.ventana.tabla.rowCount()):
            self.ventana.tabla.item(fila, 0).setCheckState(Qt.CheckState.Unchecked)

        with patch(
            "gui.paginas.pagina_organizador.QMessageBox.question",
            MagicMock(return_value=CONFIRMAR_SI),
        ) as confirmacion:
            self.ventana._organizar()
            confirmacion.assert_not_called()

        self.assertTrue((self.origen / "foto.png").is_file())

    def test_progreso_actualiza_contadores_y_barra(self):
        from gui.hilos.ejecutor import EjecutorEjecucion

        self.crear_archivo("foto.png")
        self.crear_archivo("datos.json")
        self.crear_archivo("raro.xyz")
        self.analizar()

        worker = EjecutorEjecucion(self.ventana.plan)
        llamadas = []
        worker.progreso.connect(lambda p, t, f: llamadas.append((p, t, f)))
        # Los slots de la página solo se conectan en _iniciar_ejecucion;
        # aquí se conectan a mano para probar run() de forma síncrona.
        worker.progreso.connect(self.ventana._al_progreso)
        worker.terminado.connect(self.ventana._al_terminado)

        worker.run()  # señales directas: los slots de la página ya actúan

        self.assertEqual(llamadas, [(1, 3, 0), (2, 3, 0), (3, 3, 0)])
        self.assertFalse(self.ventana.barra_progreso.parentWidget().isHidden())
        self.assertEqual(self.ventana.barra_progreso.value(), 3)
        self.assertIn("Fallidos: 0", self.ventana.texto_progreso.text())
        self.assertIn("movidos", self.ventana.texto_estado.text())

        # run() directo no emite finished (solo start() lo hace): se
        # simula la entrega para comprobar el ocultado del progreso.
        self.ventana._al_hilo_terminado()
        self.assertTrue(self.ventana.barra_progreso.parentWidget().isHidden())

    def test_la_interfaz_se_bloquea_durante_la_ejecucion(self):
        import time
        from organizador.core import ResumenEjecucion

        def lento(plan, on_progreso=None):
            time.sleep(0.3)
            return ResumenEjecucion()

        self.crear_archivo("foto.png")
        self.analizar()

        with patch(
            "gui.hilos.ejecutor.core.ejecutar_plan",
            staticmethod(lento),
        ):
            self.ventana._iniciar_ejecucion()

            # Todavía corriendo: la página está bloqueada y el
            # progreso visible.
            self.assertFalse(self.ventana.tabla.isEnabled())
            self.assertFalse(
                self.ventana.barra_progreso.parentWidget().isHidden()
            )

            self.terminar_ejecucion()

        # Recuperación completa.
        self.assertTrue(self.ventana.tabla.isEnabled())
        self.assertTrue(self.ventana.barra_progreso.parentWidget().isHidden())
        self.assertIsNone(self.ventana._ejecutor)

    def test_la_interfaz_se_recupera_tras_un_error_del_hilo(self):
        self.crear_archivo("foto.png")
        self.analizar()

        def romper(plan, on_progreso=None):
            raise RuntimeError("boom")

        with patch(
            "gui.hilos.ejecutor.core.ejecutar_plan",
            staticmethod(romper),
        ), patch(
            "gui.paginas.pagina_organizador.QMessageBox.critical",
            staticmethod(lambda *args, **kwargs: None),
        ):
            self.ventana._iniciar_ejecucion()
            self.terminar_ejecucion()

        # Recuperación: controles de vuelta y aviso de interrupción.
        self.assertTrue(self.ventana.tabla.isEnabled())
        self.assertIsNone(self.ventana._ejecutor)
        self.assertIn(
            "interrumpió", self.ventana.texto_estado.text().lower()
        )


class TestNavegacion(unittest.TestCase):
    """Navegación lateral: cambio de página y conservación del estado."""

    def setUp(self):
        self.carpeta_temporal = tempfile.TemporaryDirectory()
        self.raiz = Path(self.carpeta_temporal.name)
        self.origen = self.raiz / "origen"
        self.destino = self.raiz / "destino"
        self.origen.mkdir()
        self.destino.mkdir()

        self.shell = VentanaPrincipal()
        self.pagina = self.shell.pagina_organizador
        self.pagina.ruta_config = self.raiz / "config.json"
        self.pagina.ruta_origen = self.origen
        self.pagina.ruta_destino = self.destino

        # La página Preferencias carga config.json al volverse visible:
        # apunta su ruta a un temporal para no leer la config real.
        self.shell.pagina_preferencias.ruta_config = self.raiz / "config.json"

    def tearDown(self):
        self.carpeta_temporal.cleanup()

    def cambiar_a(self, indice):
        self.shell.botones_navegacion.button(indice).click()

    def test_tres_paginas_registradas(self):
        self.assertEqual(self.shell.paginas.count(), 3)
        self.assertEqual(self.shell.paginas.currentIndex(), 0)

    def test_cambio_de_pagina_selecciona_la_pagina_correcta(self):
        self.cambiar_a(1)
        self.assertEqual(self.shell.paginas.currentIndex(), 1)

        self.cambiar_a(2)
        self.assertEqual(self.shell.paginas.currentIndex(), 2)

        self.cambiar_a(0)
        self.assertEqual(self.shell.paginas.currentIndex(), 0)

    def test_el_estado_del_analisis_se_conserva_al_cambiar_de_pagina(self):
        (self.origen / "foto.png").write_text("prueba", encoding="utf-8")
        self.pagina._analizar()

        filas_antes = self.pagina.tabla.rowCount()
        self.assertEqual(filas_antes, 1)

        self.cambiar_a(1)
        self.cambiar_a(0)

        self.assertEqual(self.shell.paginas.currentIndex(), 0)
        self.assertEqual(self.pagina.tabla.rowCount(), filas_antes)
        self.assertEqual(len(self.pagina.plan), 1)
        self.assertTrue(self.pagina.boton_organizar.isEnabled())

    def test_config_actualizada_limpia_el_plan(self):
        (self.origen / "foto.png").write_text("prueba", encoding="utf-8")
        self.pagina._analizar()
        self.assertEqual(self.pagina.tabla.rowCount(), 1)

        self.pagina.config_actualizada()

        self.assertEqual(self.pagina.tabla.rowCount(), 0)
        self.assertEqual(self.pagina.plan, [])
        self.assertFalse(self.pagina.boton_organizar.isEnabled())

    def test_placeholders_existen_y_tienen_contenido(self):
        from gui.paginas.pagina_categorias import PaginaCategorias
        from gui.paginas.pagina_preferencias import PaginaPreferencias

        for clase in (PaginaCategorias, PaginaPreferencias):
            pagina = clase()
            etiquetas = pagina.findChildren(QLabel)
            self.assertTrue(etiquetas)
            self.assertTrue(
                all(etiqueta.text() for etiqueta in etiquetas)
            )


class TestBarraLateral(unittest.TestCase):
    """Barra lateral contraíble: estados, tooltips y alternancia."""

    ANCHOS = (64, 220)

    def setUp(self):
        self.carpeta_temporal = tempfile.TemporaryDirectory()

        self.shell = VentanaPrincipal()
        # El showEvent del shell lee las preferencias de navegación del
        # disco: apunta la ruta a un temporal para no depender de la
        # config real del usuario.
        self.shell.pagina_preferencias.ruta_config = (
            Path(self.carpeta_temporal.name) / "config.json"
        )

    def tearDown(self):
        self.carpeta_temporal.cleanup()

    def terminar_animacion(self):
        if self.shell._animacion_barra is not None:
            self.shell._animacion_barra.setCurrentTime(1000)

    def test_estado_inicial_expandido(self):
        barra = self.shell.barra_lateral

        self.assertTrue(self.shell.barra_expandida)
        self.assertEqual(barra.minimumWidth(), 220)
        self.assertEqual(barra.maximumWidth(), 220)

        boton = self.shell.botones_navegacion.buttons()[0]
        self.assertEqual(boton.text(), "Organizador")
        self.assertEqual(boton.toolTip(), "")
        self.assertFalse(self.shell.titulo_barra.isHidden())
        self.assertEqual(self.shell.boton_alternador.toolTip(), "Contraer barra")

    def test_estado_contraido_muestra_solo_iconos_con_tooltips(self):
        self.shell._aplicar_estado_barra(False)

        barra = self.shell.barra_lateral
        self.assertEqual(barra.minimumWidth(), 64)
        self.assertEqual(barra.maximumWidth(), 64)

        self.assertTrue(self.shell.titulo_barra.isHidden())
        self.assertTrue(self.shell.subtitulo_barra.isHidden())

        for indice, boton in enumerate(self.shell.botones_navegacion.buttons()):
            nombre = tr(PAGINAS[indice][0])
            self.assertEqual(boton.text(), "")
            self.assertEqual(boton.toolTip(), nombre)

        self.assertEqual(self.shell.boton_alternador.toolTip(), "Expandir barra")

    def test_volver_a_expandir_restaura_textos(self):
        self.shell._aplicar_estado_barra(False)
        self.shell._aplicar_estado_barra(True)

        self.assertTrue(self.shell.barra_expandida)
        self.assertEqual(self.shell.barra_lateral.maximumWidth(), 220)

        boton = self.shell.botones_navegacion.buttons()[0]
        self.assertEqual(boton.text(), "Organizador")
        self.assertEqual(boton.toolTip(), "")
        self.assertFalse(self.shell.titulo_barra.isHidden())

    def test_alternar_invierte_estado_y_aplica_el_ancho_final(self):
        self.shell._alternar_barra()

        self.assertFalse(self.shell.barra_expandida)
        self.terminar_animacion()

        # El estado final se aplica al terminar la animación.
        self.assertEqual(self.shell.barra_lateral.maximumWidth(), 64)
        self.assertEqual(
            self.shell.botones_navegacion.buttons()[0].toolTip(), "Organizador"
        )

    def test_alternar_dos_veces_vuelve_al_estado_inicial(self):
        self.shell._alternar_barra()
        self.terminar_animacion()
        self.shell._alternar_barra()
        self.terminar_animacion()

        self.assertTrue(self.shell.barra_expandida)
        self.assertEqual(self.shell.barra_lateral.maximumWidth(), 220)

    def test_pagina_activa_se_conserva_al_alternar(self):
        self.shell.botones_navegacion.button(1).click()
        self.assertEqual(self.shell.paginas.currentIndex(), 1)

        self.shell._alternar_barra()
        self.terminar_animacion()
        self.assertEqual(self.shell.paginas.currentIndex(), 1)

        self.shell._alternar_barra()
        self.terminar_animacion()
        self.assertEqual(self.shell.paginas.currentIndex(), 1)

    def test_iconos_cargan_desde_recursos(self):
        for _, _, nombre in PAGINAS:
            icono = self.shell._icono(nombre)
            self.assertFalse(icono.isNull(), f"No se cargó {nombre}.svg")


class TestModoAutomatico(unittest.TestCase):
    """Modo automático: hover, retardo de ocultamiento y cambio de modo.

    Los eventos reales del ratón no se simulan bien en offscreen: las
    pruebas llaman directamente a los manejadores (_al_entrar_barra,
    _al_salir_barra, _ocultar_barra_automatica).
    """

    def setUp(self):
        self.carpeta_temporal = tempfile.TemporaryDirectory()

        self.shell = VentanaPrincipal()
        # El showEvent del shell lee las preferencias de navegación del
        # disco: apunta la ruta a un temporal para no depender de la
        # config real del usuario.
        self.shell.pagina_preferencias.ruta_config = (
            Path(self.carpeta_temporal.name) / "config.json"
        )

    def tearDown(self):
        self.carpeta_temporal.cleanup()

    def terminar_animacion(self):
        if self.shell._animacion_barra is not None:
            self.shell._animacion_barra.setCurrentTime(1000)

    def poner_en_reposo(self):
        self.shell._aplicar_estado_barra(False)

    def poner_expandida(self):
        self.shell._aplicar_estado_barra(True)

    def test_arranque_en_modo_automatico(self):
        self.assertTrue(self.shell.modo_automatico)
        self.assertTrue(self.shell.boton_modo.isChecked())
        self.assertFalse(self.shell._timer_ocultar.isActive())

    def test_mostrar_la_ventana_deja_la_barra_en_reposo(self):
        self.shell.show()

        self.assertFalse(self.shell.barra_expandida)
        self.assertEqual(self.shell.barra_lateral.maximumWidth(), 64)
        self.assertEqual(
            self.shell.botones_navegacion.buttons()[0].toolTip(), "Organizador"
        )

    def test_entrar_cancela_el_timer_y_expande(self):
        self.poner_en_reposo()
        self.shell._timer_ocultar.start()  # ocultamiento pendiente

        self.shell._al_entrar_barra()
        self.terminar_animacion()

        self.assertFalse(self.shell._timer_ocultar.isActive())
        self.assertTrue(self.shell.barra_expandida)
        self.assertEqual(self.shell.barra_lateral.maximumWidth(), 220)

    def test_salir_programa_el_retardo_de_400ms(self):
        self.poner_expandida()

        self.shell._al_salir_barra()

        self.assertTrue(self.shell._timer_ocultar.isActive())
        self.assertEqual(self.shell._timer_ocultar.interval(), 400)

    def test_reentrada_durante_la_espera_cancela_el_ocultamiento(self):
        self.poner_expandida()
        self.shell._al_salir_barra()
        self.assertTrue(self.shell._timer_ocultar.isActive())

        self.shell._al_entrar_barra()

        self.assertFalse(self.shell._timer_ocultar.isActive())
        self.assertTrue(self.shell.barra_expandida)
        self.assertEqual(self.shell.barra_lateral.maximumWidth(), 220)

    def test_disparo_del_timer_oculta_la_barra(self):
        self.poner_expandida()
        self.shell._al_salir_barra()

        self.shell._ocultar_barra_automatica()
        self.terminar_animacion()

        self.assertFalse(self.shell.barra_expandida)
        self.assertEqual(self.shell.barra_lateral.maximumWidth(), 64)
        self.assertEqual(
            self.shell.botones_navegacion.buttons()[0].toolTip(), "Organizador"
        )

    def test_cursor_dentro_no_deberia_dejar_la_barra_pendiente(self):
        # La barra contraída sigue visible (64 px): el cursor sobre ella
        # no dispara Leave, y si estuviera pendiente, entrar lo cancela.
        self.poner_en_reposo()
        self.shell._al_entrar_barra()
        self.terminar_animacion()

        self.assertFalse(self.shell._timer_ocultar.isActive())
        self.assertTrue(self.shell.barra_expandida)

    def test_paso_a_manual_cancela_el_ocultamiento_pendiente(self):
        self.poner_expandida()
        self.shell._al_salir_barra()
        self.assertTrue(self.shell._timer_ocultar.isActive())

        self.shell._cambiar_modo_barra(False)

        self.assertFalse(self.shell.modo_automatico)
        self.assertFalse(self.shell.boton_modo.isChecked())
        self.assertFalse(self.shell._timer_ocultar.isActive())

    def test_cambio_de_modo_conserva_el_ancho_actual(self):
        self.poner_expandida()
        self.shell._cambiar_modo_barra(False)

        self.assertEqual(self.shell.barra_lateral.maximumWidth(), 220)

        self.shell._cambiar_modo_barra(True)

        self.assertEqual(self.shell.barra_lateral.maximumWidth(), 220)

    def test_la_pagina_activa_se_conserva_con_el_modo_automatico(self):
        self.shell.botones_navegacion.button(1).click()

        self.poner_expandida()
        self.shell._al_salir_barra()
        self.shell._ocultar_barra_automatica()
        self.terminar_animacion()
        self.shell._al_entrar_barra()
        self.terminar_animacion()

        self.assertEqual(self.shell.paginas.currentIndex(), 1)


class TestEditorCategorias(unittest.TestCase):
    """Editor de categorías: carga, edición, validaciones y guardado.

    Usa config.json temporal; nunca toca la configuración real de App.
    """

    def setUp(self):
        self.carpeta_temporal = tempfile.TemporaryDirectory()
        self.raiz = Path(self.carpeta_temporal.name)
        self.ruta_config = self.raiz / "config.json"

        self.shell = VentanaPrincipal()
        self.pagina = self.shell.pagina_categorias
        self.pagina.ruta_config = self.ruta_config
        self.pagina._cargar_config()

    def tearDown(self):
        self.carpeta_temporal.cleanup()

    def seleccionar(self, indice):
        self.pagina.lista_categorias.setCurrentRow(indice)

    def categoria_actual(self):
        return self.pagina.ajustes.categorias[self.pagina.lista_categorias.currentRow()]

    def crear_modelos_3d(self):
        """Crea una categoría con extensión .blend y la selecciona."""

        self.pagina._crear_categoria()
        self.pagina.campo_nombre.setText("Modelos 3D")
        self.pagina.campo_extension.setText(".blend")
        self.pagina._anadir_extension()

    def contenido_config(self) -> str:
        return self.ruta_config.read_text(encoding="utf-8")

    # --- Carga inicial ---------------------------------------------------

    def test_carga_inicial_muestra_las_once_categorias(self):
        self.assertEqual(self.pagina.lista_categorias.count(), 11)

    def test_carga_inicial_muestra_extensiones_y_subcarpeta(self):
        self.seleccionar(0)  # Imagenes

        self.assertEqual(
            self.pagina.extensiones_en_pantalla(),
            [".jpg", ".jpeg", ".png", ".webp", ".gif"],
        )
        self.assertEqual(self.pagina.campo_nombre.text(), "Imagenes")
        self.assertEqual(self.pagina.campo_destino.text(), "Imagenes")

    # --- Crear y editar ---------------------------------------------------

    def test_crear_categoria_con_nombre_provisional_unico(self):
        self.pagina._crear_categoria()
        self.seleccionar(self.pagina.lista_categorias.count() - 1)

        self.assertEqual(self.pagina.campo_nombre.text(), "Nueva categoría")
        self.assertEqual(self.pagina.lista_categorias.count(), 12)

    def test_renombrar_se_refleja_en_memoria_y_en_la_lista(self):
        self.pagina._crear_categoria()
        self.pagina.campo_nombre.setText("Modelos 3D")

        self.assertEqual(self.categoria_actual().nombre, "Modelos 3D")
        fila = self.pagina.lista_categorias.count() - 1
        self.assertEqual(self.pagina.lista_categorias.item(fila).text(), "Modelos 3D")

    def test_subcarpeta_sigue_al_nombre_mientras_usa_el_valor_por_defecto(self):
        self.pagina._crear_categoria()
        self.pagina.campo_nombre.setText("Modelos 3D")

        self.assertEqual(self.categoria_actual().destino, "Modelos 3D")
        self.assertEqual(self.pagina.campo_destino.text(), "Modelos 3D")

    def test_subcarpeta_editable_independiente(self):
        self.crear_modelos_3d()
        self.pagina.campo_destino.setText("Modelos")

        self.assertEqual(self.categoria_actual().destino, "Modelos")
        self.assertEqual(self.pagina.campo_destino.text(), "Modelos")

    # --- Normalización -----------------------------------------------------

    def test_extensiones_se_normalizan(self):
        # .png, .jpg y .webp pertenecen a Imagenes en la config por
        # defecto: la retiramos en memoria para poder añadirlos aquí.
        self.seleccionar(0)
        self.pagina._eliminar_categoria()

        self.pagina._crear_categoria()
        self.pagina.campo_nombre.setText("Normalizada")

        for texto, esperada in ((" PNG ", ".png"), ("JPG", ".jpg"), (".WEBP", ".webp")):
            self.pagina.campo_extension.setText(texto)
            self.pagina._anadir_extension()

            visibles = self.pagina.extensiones_en_pantalla()
            self.assertEqual(visibles[-1], esperada)

    # --- Validaciones ---------------------------------------------------------

    def test_extension_duplicada_en_la_misma_categoria_rechazada(self):
        self.crear_modelos_3d()

        self.pagina.campo_extension.setText(".blend")
        self.pagina._anadir_extension()

        self.assertIn("ya está", self.pagina.texto_estado.text())
        self.assertEqual(len(self.pagina.extensiones_en_pantalla()), 1)

    def test_extension_de_otra_categoria_rechazada(self):
        self.seleccionar(1)  # Documentos: .pdf, .txt, .docx, .csv

        self.pagina.campo_extension.setText(".jpg")  # pertenece a Imagenes
        self.pagina._anadir_extension()

        self.assertIn("otra categoría", self.pagina.texto_estado.text())
        self.assertEqual(len(self.pagina.extensiones_en_pantalla()), 4)

    def test_guardar_sin_nombre_rechazado_y_no_escribe_disco(self):
        contenido_antes = self.contenido_config()
        self.pagina._crear_categoria()
        self.pagina.campo_nombre.setText("")

        self.pagina._guardar()

        self.assertIn("No se pudo guardar", self.pagina.texto_estado.text())
        self.assertEqual(self.contenido_config(), contenido_antes)

    def test_nombre_reservado_otros_rechazado(self):
        contenido_antes = self.contenido_config()
        self.pagina._crear_categoria()
        self.pagina.campo_nombre.setText("Otros")

        self.pagina._guardar()

        self.assertIn("No se pudo guardar", self.pagina.texto_estado.text())
        self.assertEqual(self.contenido_config(), contenido_antes)

    def test_chip_con_boton_cerrar_elimina_su_extension(self):
        from gui.paginas.pagina_categorias import ChipExtension

        self.crear_modelos_3d()  # .blend
        self.assertEqual(self.pagina.extensiones_en_pantalla(), [".blend"])

        chip = self.pagina.panel_chips.findChildren(ChipExtension)[0]
        chip.findChildren(QPushButton)[0].click()

        self.assertEqual(self.pagina.extensiones_en_pantalla(), [])
        self.assertNotIn(".blend", self.categoria_actual().extensiones)
        self.assertTrue(self.pagina._cambios_pendientes)

    # --- Guardar y eliminar ------------------------------------------------------

    def test_guardar_persiste_y_deshabilita_el_boton(self):
        self.crear_modelos_3d()
        self.assertTrue(self.pagina.boton_guardar.isEnabled())

        self.pagina._guardar()

        self.assertFalse(self.pagina.boton_guardar.isEnabled())
        self.assertFalse(self.pagina._cambios_pendientes)

        ajustes = config.cargar_config(self.ruta_config)
        nombres = [categoria.nombre for categoria in ajustes.categorias]
        self.assertIn("Modelos 3D", nombres)

        modelos = ajustes.categorias[nombres.index("Modelos 3D")]
        self.assertEqual(modelos.extensiones, [".blend"])
        self.assertEqual(modelos.destino, "Modelos 3D")

    def test_eliminar_categoria_desaparece_al_guardar(self):
        self.seleccionar(0)  # Imagenes
        self.pagina._eliminar_categoria()

        self.assertEqual(self.pagina.lista_categorias.count(), 10)

        self.pagina._guardar()

        ajustes = config.cargar_config(self.ruta_config)
        self.assertNotIn(
            "Imagenes", [categoria.nombre for categoria in ajustes.categorias]
        )
        self.assertEqual(len(ajustes.categorias), 10)

    def test_boton_guardar_deshabilitado_sin_cambios(self):
        self.assertFalse(self.pagina.boton_guardar.isEnabled())

        self.pagina._crear_categoria()
        self.assertTrue(self.pagina.boton_guardar.isEnabled())

        self.pagina._guardar()
        self.assertFalse(self.pagina.boton_guardar.isEnabled())

    # --- Integración con el organizador ---------------------------------------------

    def test_guardar_emite_senal_y_invalida_el_plan_del_organizador(self):
        shell = VentanaPrincipal()
        organizador = shell.pagina_organizador
        editor = shell.pagina_categorias

        ruta_config = self.raiz / "config.json"
        editor.ruta_config = ruta_config
        editor._cargar_config()

        organizador.ruta_config = ruta_config
        organizador.ruta_origen = self.raiz / "origen"
        organizador.ruta_destino = self.raiz / "destino"
        organizador.ruta_origen.mkdir()
        organizador.ruta_destino.mkdir()

        (organizador.ruta_origen / "foto.png").write_text("prueba", encoding="utf-8")
        organizador._analizar()
        self.assertEqual(organizador.tabla.rowCount(), 1)

        senales = []
        editor.config_actualizada.connect(lambda: senales.append(True))

        editor._crear_categoria()
        editor.campo_nombre.setText("Modelos 3D")
        editor.campo_extension.setText(".blend")
        editor._anadir_extension()
        editor._guardar()

        self.assertEqual(senales, [True])
        # El organizador invalidó su plan al guardar.
        self.assertEqual(organizador.tabla.rowCount(), 0)
        self.assertEqual(organizador.plan, [])

        # Un análisis nuevo usa la configuración actualizada: ahora
        # también está modelo.blend, junto con foto.png que sigue ahí.
        (organizador.ruta_origen / "modelo.blend").write_text("x", encoding="utf-8")
        organizador._analizar()

        self.assertEqual(organizador.tabla.rowCount(), 2)
        entrada_blend = [
            entrada
            for entrada in organizador.plan
            if entrada.origen.name == "modelo.blend"
        ][0]
        self.assertEqual(entrada_blend.categoria, "Modelos 3D")


class TestPreferencias(unittest.TestCase):
    """Página Preferencias: navegación, desconocidos e ignorados.

    Usa config.json temporal; nunca toca la configuración real de App.
    """

    def setUp(self):
        self.carpeta_temporal = tempfile.TemporaryDirectory()
        self.raiz = Path(self.carpeta_temporal.name)
        self.ruta_config = self.raiz / "config.json"

        self.shell = VentanaPrincipal()
        self.pagina = self.shell.pagina_preferencias
        self.pagina.ruta_config = self.ruta_config
        self.pagina._cargar_config()

        self.organizador = self.shell.pagina_organizador
        self.organizador.ruta_config = self.ruta_config
        self.origen = self.raiz / "origen"
        self.destino = self.raiz / "destino"
        self.origen.mkdir()
        self.destino.mkdir()
        self.organizador.ruta_origen = self.origen
        self.organizador.ruta_destino = self.destino

    def tearDown(self):
        self.carpeta_temporal.cleanup()

    def escribir_config(self, **preferencias):
        """Escribe una config temporal con las preferencias dadas."""

        datos = config._config_a_dict(config.ajustes_por_defecto())
        datos["preferencias"].update(preferencias)
        self.ruta_config.write_text(
            json.dumps(datos, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def contenido_config(self) -> str:
        return self.ruta_config.read_text(encoding="utf-8")

    def seleccionar_combo(self, comportamiento):
        indice = self.pagina.combo_desconocidos.findData(comportamiento.value)
        self.pagina.combo_desconocidos.setCurrentIndex(indice)

    # --- Carga y sincronización -----------------------------------------

    def test_carga_inicial_refleja_los_valores_del_disco(self):
        self.escribir_config(
            navegacion_automatica=False, retardo_navegacion_ms=600
        )
        self.pagina._cargar_config()

        self.assertFalse(self.pagina.casilla_navegacion.isChecked())
        self.assertEqual(self.pagina.campo_retardo.value(), 600)
        # Sin modo automático el retardo no es editable.
        self.assertFalse(self.pagina.campo_retardo.isEnabled())

        self.assertEqual(
            self.pagina.combo_desconocidos.currentData(),
            ComportamientoDesconocidos.OTROS.value,
        )
        nombres = [
            self.pagina.lista_ignorados.item(fila).text()
            for fila in range(self.pagina.lista_ignorados.count())
        ]
        self.assertEqual(nombres, ["desktop.ini", "Thumbs.db"])

    def test_entrar_en_la_pagina_sincroniza_el_estado_de_sesion(self):
        # El usuario cambió el modo con el botón de la barra lateral.
        self.shell.aplicar_navegacion(False, 400)

        self.shell.botones_navegacion.button(2).click()

        self.assertFalse(self.pagina.casilla_navegacion.isChecked())
        self.assertTrue(self.pagina._cambios_pendientes)
        self.assertTrue(self.pagina.boton_guardar.isEnabled())

    def test_cambios_pendientes_sobreviven_al_cambiar_de_pagina(self):
        # Primera entrada en la página: sincroniza el estado de sesión.
        self.shell.botones_navegacion.button(2).click()
        self.assertFalse(self.pagina._cambios_pendientes)

        # El usuario edita el retardo (cambio pendiente).
        self.pagina.campo_retardo.setValue(600)
        self.assertTrue(self.pagina._cambios_pendientes)

        self.shell.botones_navegacion.button(0).click()
        self.shell.botones_navegacion.button(2).click()

        # La sesión no cambió: la edición pendiente del usuario se
        # conserva (no se pisa con el valor de la sesión).
        self.assertTrue(self.pagina._cambios_pendientes)
        self.assertEqual(self.pagina.campo_retardo.value(), 600)

    # --- Guardar: navegación en vivo + persistencia ------------------------

    def test_guardar_aplica_la_navegacion_en_vivo_y_persiste(self):
        (self.origen / "foto.png").write_text("prueba", encoding="utf-8")
        self.organizador._analizar()
        self.assertEqual(self.organizador.tabla.rowCount(), 1)

        senales = []
        self.pagina.config_actualizada.connect(senales.append)

        self.pagina.casilla_navegacion.setChecked(False)
        self.pagina.campo_retardo.setValue(600)
        self.pagina._guardar()

        # Aplicado en vivo en el shell.
        self.assertFalse(self.shell.modo_automatico)
        self.assertFalse(self.shell.boton_modo.isChecked())
        self.assertEqual(self.shell._timer_ocultar.interval(), 600)
        self.assertFalse(self.shell._timer_ocultar.isActive())

        # Persistido en disco.
        cargados = config.cargar_config(self.ruta_config)
        self.assertFalse(cargados.navegacion_automatica)
        self.assertEqual(cargados.retardo_navegacion_ms, 600)

        # Señal emitida y plan del organizador invalidado.
        self.assertEqual(len(senales), 1)
        self.assertEqual(self.organizador.tabla.rowCount(), 0)
        self.assertEqual(self.organizador.plan, [])

    def test_retardo_invalido_rechazado_sin_escribir_disco(self):
        contenido_antes = self.contenido_config()
        self.pagina.ajustes.retardo_navegacion_ms = 50
        self.pagina._cambios_pendientes_marcar()

        self.pagina._guardar()

        self.assertIn("No se pudo guardar", self.pagina.texto_estado.text())
        self.assertEqual(self.contenido_config(), contenido_antes)

    # --- Comportamiento de desconocidos --------------------------------------

    def test_desconocidos_advertir_marca_en_el_plan(self):
        self.seleccionar_combo(ComportamientoDesconocidos.ADVERTIR)
        self.pagina._guardar()

        cargados = config.cargar_config(self.ruta_config)
        self.assertIs(
            cargados.unknown_files, ComportamientoDesconocidos.ADVERTIR
        )

        (self.origen / "raro.xyz").write_text("prueba", encoding="utf-8")
        self.organizador._analizar()

        estados = {
            entrada.origen.name: entrada.estado for entrada in self.organizador.plan
        }
        self.assertIs(estados["raro.xyz"], EstadoPlan.ADVERTIDO)
        self.assertEqual(
            self.organizador.tabla.item(0, 5).text(), "Advertido"
        )

    # --- Archivos ignorados ------------------------------------------------------

    def test_ignorados_anadir_normalizar_duplicado_y_eliminar(self):
        # Añadir con espacios y mayúsculas: se normaliza a minúsculas.
        self.pagina.campo_ignorado.setText("  MiArchivo.TXT  ")
        self.pagina._anadir_ignorado()

        self.assertIn("miarchivo.txt", self.pagina.ajustes.archivos_ignorados)
        self.assertEqual(self.pagina.campo_ignorado.text(), "")
        self.assertTrue(self.pagina._cambios_pendientes)

        # Duplicado rechazado con mensaje, sin añadir de nuevo.
        self.pagina.campo_ignorado.setText("MIARCHIVO.txt")
        self.pagina._anadir_ignorado()

        self.assertIn("ya está", self.pagina.texto_estado.text())
        self.assertEqual(
            self.pagina.lista_ignorados.count(), 3
        )  # 2 por defecto + 1

        # Vacío no se añade.
        self.pagina.campo_ignorado.setText("   ")
        self.pagina._anadir_ignorado()
        self.assertEqual(self.pagina.lista_ignorados.count(), 3)

        # Eliminar el primero (desktop.ini).
        self.pagina.lista_ignorados.setCurrentRow(0)
        self.pagina._eliminar_ignorado()

        self.assertNotIn(
            "desktop.ini", self.pagina.ajustes.archivos_ignorados
        )
        self.assertEqual(self.pagina.lista_ignorados.count(), 2)

    def test_ignorado_marca_en_el_plan(self):
        self.pagina.campo_ignorado.setText("prueba.xyz")
        self.pagina._anadir_ignorado()
        self.pagina._guardar()

        (self.origen / "prueba.xyz").write_text("prueba", encoding="utf-8")
        self.organizador._analizar()

        estados = {
            entrada.origen.name: entrada.estado for entrada in self.organizador.plan
        }
        self.assertIs(estados["prueba.xyz"], EstadoPlan.IGNORADO)
        self.assertEqual(self.organizador.tabla.item(0, 5).text(), "Ignorado")

    # --- Estado del botón y compatibilidad -----------------------------------

    def test_boton_guardar_deshabilitado_sin_cambios(self):
        self.assertFalse(self.pagina.boton_guardar.isEnabled())

        self.seleccionar_combo(ComportamientoDesconocidos.IGNORAR)
        self.assertTrue(self.pagina.boton_guardar.isEnabled())

        self.pagina._guardar()
        self.assertFalse(self.pagina.boton_guardar.isEnabled())
        self.assertIn("guardada", self.pagina.texto_estado.text())

    def test_config_antigua_muestra_los_defaults_de_navegacion(self):
        datos = config._config_a_dict(config.ajustes_por_defecto())
        del datos["preferencias"]["navegacion_automatica"]
        del datos["preferencias"]["retardo_navegacion_ms"]
        self.ruta_config.write_text(
            json.dumps(datos, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        self.pagina._cargar_config()

        self.assertTrue(self.pagina.casilla_navegacion.isChecked())
        self.assertEqual(self.pagina.campo_retardo.value(), 400)
        self.assertFalse(self.pagina._cambios_pendientes)

    def test_primera_muestra_aplica_las_preferencias_de_disco(self):
        self.escribir_config(
            navegacion_automatica=False, retardo_navegacion_ms=600
        )

        self.shell.show()

        self.assertFalse(self.shell.modo_automatico)
        self.assertEqual(self.shell._timer_ocultar.interval(), 600)
        self.assertFalse(self.shell.boton_modo.isChecked())


if __name__ == "__main__":
    unittest.main()
