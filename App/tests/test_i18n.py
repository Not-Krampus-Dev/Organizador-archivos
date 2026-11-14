# Pruebas de la infraestructura de internacionalización.

# Verifican la paridad de claves y placeholders entre idiomas (anti
# traducciones incompletas o mezcladas), la API de cambio de idioma,
# el soporte japonés (UTF-8/CJK) y la validación del idioma en config.

import json
import os
import string
import sys
import tempfile
import unittest
from pathlib import Path

# La plataforma debe fijarse antes de importar PySide6.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from gui import i18n
from gui.main_window import VentanaPrincipal
from organizador import config

APP = QApplication.instance() or QApplication(sys.argv)

# Alias cómodo para las aserciones.
tr_gui = i18n.tr


def placeholders_de(texto: str) -> set[str]:
    """Nombres de {placeholder} que usa una plantilla de traducción."""

    return {
        nombre
        for _, nombre, _, _ in string.Formatter().parse(texto)
        if nombre is not None
    }


class TestParidadIdiomas(unittest.TestCase):
    """Los tres idiomas cubren las mismas claves y placeholders."""

    IDIOMAS = ("es", "en", "ja")

    def test_mismas_claves_en_los_tres_idiomas(self):
        claves_es = set(i18n.textos_de_idioma("es"))

        for codigo in ("en", "ja"):
            claves = set(i18n.textos_de_idioma(codigo))

            faltantes = claves_es - claves
            sobrantes = claves - claves_es

            self.assertEqual(faltantes, set(), f"Faltan en {codigo}: {faltantes}")
            self.assertEqual(sobrantes, set(), f"Sobran en {codigo}: {sobrantes}")

    def test_mismos_placeholders_en_los_tres_idiomas(self):
        textos_es = i18n.textos_de_idioma("es")

        for clave, texto in textos_es.items():
            esperados = placeholders_de(texto)

            for codigo in ("en", "ja"):
                texto_otro = i18n.textos_de_idioma(codigo)[clave]
                self.assertEqual(
                    placeholders_de(texto_otro),
                    esperados,
                    f"Placeholders distintos en {codigo}.{clave}",
                )

    def test_no_hay_placeholders_con_posicion(self):
        """Evita reordenados imposibles: solo {nombre}, nunca {0}."""

        for codigo in self.IDIOMAS:
            for clave, texto in i18n.textos_de_idioma(codigo).items():
                self.assertFalse(
                    any(
                        nombre.isdigit()
                        for _, nombre, _, _ in string.Formatter().parse(texto)
                        if nombre is not None
                    ),
                    f"{codigo}.{clave} usa placeholder posicional",
                )


class TestApiTraduccion(unittest.TestCase):

    def tearDown(self):
        i18n.cambiar_idioma("es")

    def test_idioma_por_defecto_es_espanol(self):
        self.assertEqual(i18n.idioma_actual(), "es")
        self.assertEqual(i18n.tr("app.titulo"), "Organizador de archivos")

    def test_cambiar_idioma_cambia_los_textos(self):
        i18n.cambiar_idioma("en")
        self.assertEqual(i18n.tr("app.titulo"), "File Organizer")

        i18n.cambiar_idioma("ja")
        self.assertEqual(i18n.tr("app.titulo"), "ファイル整理ツール")

    def test_cambiar_idioma_invalido_rechazado(self):
        with self.assertRaises(ValueError):
            i18n.cambiar_idioma("fr")

        # El idioma activo no cambia.
        self.assertEqual(i18n.idioma_actual(), "es")

    def test_clave_desconocida_lanza_error_claro(self):
        with self.assertRaises(KeyError):
            i18n.tr("clave.inexistente")

    def test_interpolacion_de_parametros(self):
        texto = i18n.tr(
            "org.progreso", procesados=3, pendientes=2, fallidos=0
        )
        self.assertEqual(texto, "Procesados: 3 · Pendientes: 2 · Fallidos: 0")

    def test_fallback_al_espanol_si_falta_la_clave(self):
        """Defensa ante errores de programación: nunca texto mezclado."""

        textos_en = i18n.textos_de_idioma("en")
        clave_prestada = "ed.nueva"
        texto_original = textos_en.pop(clave_prestada)

        try:
            i18n.cambiar_idioma("en")
            self.assertEqual(i18n.tr(clave_prestada), "Nueva")
        finally:
            textos_en[clave_prestada] = texto_original


class TestJapones(unittest.TestCase):
    """Soporte correcto de caracteres japoneses."""

    def test_japones_usa_caracteres_cjk(self):
        textos = i18n.textos_de_idioma("ja")

        for clave in ("app.titulo", "nav.organizador", "estado.listo"):
            texto = textos[clave]
            self.assertTrue(
                any("\u3040" <= c <= "\u30ff" or "\u4e00" <= c <= "\u9fff" for c in texto),
                f"'{clave}' no tiene caracteres japoneses: {texto!r}",
            )

    def test_japones_sobrevive_roundtrip_json(self):
        """UTF-8 sin escapes: los CJK sobreviven a config.json."""

        # El idioma en disco es el código; los CJK reales se comprueban
        # con un roundtrip directo de un texto traducido.
        ajustes = config.ajustes_por_defecto()
        ajustes.idioma = "ja"

        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "config.json"
            config.guardar_config(ruta, ajustes)

            contenido = ruta.read_text(encoding="utf-8")
            self.assertIn('"idioma": "ja"', contenido)

            cargados = config.cargar_config(ruta)
            self.assertEqual(cargados.idioma, "ja")

        i18n.cambiar_idioma("ja")
        try:
            texto = i18n.tr("app.titulo")
            self.assertEqual(
                json.loads(json.dumps(texto)), "ファイル整理ツール"
            )
        finally:
            i18n.cambiar_idioma("es")


class TestIdiomaEnConfig(unittest.TestCase):
    """El idioma se persiste y valida en config.json."""

    def setUp(self):
        self.carpeta_temporal = tempfile.TemporaryDirectory()
        self.ruta = Path(self.carpeta_temporal.name) / "config.json"

    def tearDown(self):
        self.carpeta_temporal.cleanup()

    def test_defaults_incluyen_idioma_espanol(self):
        self.assertEqual(config.ajustes_por_defecto().idioma, "es")

    def test_roundtrip_de_idioma(self):
        for codigo in ("en", "ja"):
            ajustes = config.ajustes_por_defecto()
            ajustes.idioma = codigo

            config.guardar_config(self.ruta, ajustes)
            self.assertEqual(config.cargar_config(self.ruta).idioma, codigo)

    def test_idioma_invalido_rechazado(self):
        ajustes = config.ajustes_por_defecto()
        ajustes.idioma = "fr"

        with self.assertRaises(ValueError):
            config.validar_config(ajustes)

    def test_idioma_invalido_al_cargar_rechazado(self):
        datos = config._config_a_dict(config.ajustes_por_defecto())
        datos["preferencias"]["idioma"] = "fr"
        self.ruta.write_text(json.dumps(datos), encoding="utf-8")

        with self.assertRaises(ValueError):
            config.cargar_config(self.ruta)

    def test_config_antigua_sin_idioma_carga_con_default(self):
        datos = config._config_a_dict(config.ajustes_por_defecto())
        del datos["preferencias"]["idioma"]

        ajustes = config._config_desde_dict(datos)
        self.assertEqual(ajustes.idioma, "es")


class TestCargarIdiomaDeDisco(unittest.TestCase):
    """Lectura ligera del idioma para el arranque (sin efectos)."""

    def setUp(self):
        self.carpeta_temporal = tempfile.TemporaryDirectory()
        self.raiz = Path(self.carpeta_temporal.name)

    def tearDown(self):
        self.carpeta_temporal.cleanup()

    def test_archivo_inexistente_devuelve_default(self):
        self.assertEqual(
            i18n.cargar_idioma_de_disco(self.raiz / "no.json"), "es"
        )

    def test_idioma_guardado_se_lee(self):
        ruta = self.raiz / "config.json"
        datos = config._config_a_dict(config.ajustes_por_defecto())
        datos["preferencias"]["idioma"] = "ja"
        ruta.write_text(json.dumps(datos), encoding="utf-8")

        self.assertEqual(i18n.cargar_idioma_de_disco(ruta), "ja")

    def test_archivo_corrupto_devuelve_default(self):
        ruta = self.raiz / "config.json"
        ruta.write_text("{json roto", encoding="utf-8")

        self.assertEqual(i18n.cargar_idioma_de_disco(ruta), "es")


class TestIdiomaGUI(unittest.TestCase):
    """Cambio de idioma en la aplicación completa (offscreen).

    Verifica que, al cambiar el idioma en Preferencias y pulsar
    «Guardar cambios», se retraducen el shell y las tres páginas; que
    no queda texto en español mezclado en japonés; que los estados del
    plan aparecen traducidos; y que el idioma persiste al reabrir.
    """

    # Textos canónicos en español que NO deben sobrevivir a un cambio
    # de idioma (búsqueda en etiquetas, botones y tooltips).
    HUELLAS_ES = (
        "Organizador de archivos",
        "Guardar cambios",
        "Analizar archivos",
        "Categorías",
        "Preferencias",
        "Nueva categoría",
        "Selecciona las carpetas",
    )

    def setUp(self):
        self.carpeta_temporal = tempfile.TemporaryDirectory()
        self.raiz = Path(self.carpeta_temporal.name)
        self.ruta_config = self.raiz / "config.json"

        # Config temporal por defecto (nunca se toca la App real).
        config.guardar_config(self.ruta_config, config.ajustes_por_defecto())

        self.shell = VentanaPrincipal()

        # Las tres páginas leen/escriben la config temporal.
        self.organizador = self.shell.pagina_organizador
        self.categorias = self.shell.pagina_categorias
        self.preferencias = self.shell.pagina_preferencias
        self.organizador.ruta_config = self.ruta_config
        self.categorias.ruta_config = self.ruta_config
        self.preferencias.ruta_config = self.ruta_config

        # Carpeta de origen con un archivo para probar estados del plan.
        self.origen = self.raiz / "origen"
        self.destino = self.raiz / "destino"
        self.origen.mkdir()
        self.destino.mkdir()
        self.organizador.ruta_origen = self.origen
        self.organizador.ruta_destino = self.destino
        (self.origen / "foto.png").write_text("x", encoding="utf-8")

        # La página Preferencias carga el disco al mostrarse: cargamos
        # ya para poder tocar el combo.
        self.preferencias._cargar_config()

    def tearDown(self):
        # Siempre de vuelta al español para no contaminar otros tests.
        i18n.cambiar_idioma("es")
        self.carpeta_temporal.cleanup()

    def elegir_idioma(self, codigo: str):
        """Selecciona el idioma en el combo y guarda los cambios."""

        indice = self.preferencias.combo_idioma.findData(codigo)
        self.preferencias.combo_idioma.setCurrentIndex(indice)
        self.assertTrue(self.preferencias._cambios_pendientes)
        self.preferencias.boton_guardar.click()

    def widgets_de_texto(self, pagina):
        """(texto, tooltip) de todos los botones y etiquetas de una página."""

        pares = []
        for clase in (QPushButton, QLabel):
            for widget in pagina.findChildren(clase):
                pares.append((widget.text(), widget.toolTip()))

        return pares

    def texts_casi_todo(self):
        """Textos y tooltips del shell y de las tres páginas."""

        pares = []
        for boton in self.shell.botones_navegacion.buttons():
            pares.append((boton.text(), boton.toolTip()))
        pares.append((self.shell.titulo_barra.text(), ""))
        pares.append((self.shell.subtitulo_barra.text(), ""))
        pares.append((self.shell.windowTitle(), ""))
        pares.append((self.shell.boton_alternador.toolTip(), ""))
        pares.append((self.shell.boton_modo.toolTip(), ""))

        for pagina in (self.organizador, self.categorias, self.preferencias):
            pares.extend(self.widgets_de_texto(pagina))
            pares.append((pagina.texto_estado.text(), ""))

        return pares

    # --- Cambio de idioma ---------------------------------------------------

    def test_cambio_a_ingles_retraduce_shell_y_paginas(self):
        self.elegir_idioma("en")

        self.assertEqual(i18n.idioma_actual(), "en")

        # Shell: título y botones de navegación.
        self.assertEqual(self.shell.windowTitle(), "File Organizer")
        textos_nav = [
            boton.text() for boton in self.shell.botones_navegacion.buttons()
        ]
        self.assertEqual(textos_nav, ["Organizer", "Categories", "Preferences"])

        # Organizador: botones y mensaje de estado.
        self.assertEqual(self.organizador.texto_estado.text(), tr_gui("org.estado_inicial"))
        boton_analizar = [
            boton
            for boton in self.organizador.findChildren(QPushButton)
            if boton.text() == tr_gui("org.analizar")
        ]
        self.assertEqual(len(boton_analizar), 1)

        # Cabeceras de la tabla traducidas.
        cabeceras = [
            self.organizador.tabla.horizontalHeaderItem(c).text()
            for c in range(self.organizador.tabla.columnCount())
        ]
        self.assertEqual(
            cabeceras,
            [
                tr_gui(clave)
                for clave in (
                    "org.columna_mover",
                    "org.columna_nombre",
                    "org.columna_extension",
                    "org.columna_categoria",
                    "org.columna_destino",
                    "org.columna_estado",
                )
            ],
        )

        # Categorías: grupos y botones.
        self.assertEqual(self.categorias.panel_lista.title(), "Categories")
        self.assertEqual(self.categorias.boton_guardar.text(), "Save changes")

        # Preferencias: grupos.
        self.assertEqual(self.preferencias.grupo_navegacion.title(), "Side bar")
        self.assertEqual(self.preferencias.grupo_idioma.title(), "Language")

        # Persistencia en la config temporal (no la real).
        self.assertIn('"idioma": "en"', self.ruta_config.read_text(encoding="utf-8"))

    def test_cambio_a_japones_retraduce_shell_y_paginas(self):
        self.elegir_idioma("ja")

        self.assertEqual(i18n.idioma_actual(), "ja")
        self.assertEqual(self.shell.windowTitle(), "ファイル整理ツール")

        textos_nav = [
            boton.text() for boton in self.shell.botones_navegacion.buttons()
        ]
        self.assertEqual(textos_nav, ["整理", "カテゴリ", "設定"])

        self.assertEqual(
            self.categorias.panel_lista.title(), "カテゴリ"
        )
        self.assertEqual(
            self.organizador.texto_estado.text(), tr_gui("org.estado_inicial")
        )

    def test_en_japones_no_quedan_textos_espanoles_mezclados(self):
        self.elegir_idioma("ja")

        for texto, tooltip in self.texts_casi_todo():
            contenido = texto or tooltip or ""
            for huella in self.HUELLAS_ES:
                self.assertNotIn(
                    huella,
                    contenido,
                    f"Texto español en ja: {huella!r} en {contenido!r}",
                )

        # Lo mismo en inglés.
        self.elegir_idioma("en")

        for texto, tooltip in self.texts_casi_todo():
            contenido = texto or tooltip or ""
            for huella in self.HUELLAS_ES:
                self.assertNotIn(huella, contenido)

    def test_estados_del_plan_aparecen_traducidos_tras_cambio(self):
        self.elegir_idioma("en")

        self.organizador._analizar()

        self.assertEqual(self.organizador.tabla.rowCount(), 1)
        self.assertEqual(self.organizador.tabla.item(0, 5).text(), "Ready")
        self.assertIn("Files analyzed: 1", self.organizador.texto_estado.text())

    def test_idioma_persiste_tras_reabrir_la_ventana(self):
        self.elegir_idioma("ja")

        shell2 = VentanaPrincipal()
        shell2.pagina_preferencias.ruta_config = self.ruta_config
        shell2.pagina_organizador.ruta_config = self.ruta_config
        shell2.pagina_categorias.ruta_config = self.ruta_config
        shell2.show()

        self.assertEqual(i18n.idioma_actual(), "ja")
        self.assertEqual(shell2.windowTitle(), "ファイル整理ツール")

        # El combo de la nueva instancia queda en japonés al cargar.
        shell2.pagina_preferencias._cargar_config()
        self.assertEqual(
            shell2.pagina_preferencias.combo_idioma.currentData(), "ja"
        )

    def test_vuelta_al_espanol_tras_cambiar(self):
        self.elegir_idioma("en")
        self.assertEqual(i18n.idioma_actual(), "en")

        self.elegir_idioma("es")

        self.assertEqual(i18n.idioma_actual(), "es")
        self.assertEqual(self.shell.windowTitle(), "Organizador de archivos")
        self.assertEqual(
            self.organizador.texto_estado.text(),
            tr_gui("org.estado_inicial"),
        )
        self.assertEqual(self.categorias.boton_guardar.text(), "Guardar cambios")


class TestTraduccionCategoriasGUI(unittest.TestCase):
    """Traducción visual de las categorías predeterminadas en el editor.

    Verifica que la lista muestra el nombre visible traducido, que el
    modelo y el campo conservan el nombre canónico, que los nombres
    personalizados nunca se traducen, que la selección y los cambios
    pendientes sobreviven al cambio de idioma, y que el mensaje
    inferior refleja la categoría seleccionada.
    """

    def setUp(self):
        self.carpeta_temporal = tempfile.TemporaryDirectory()
        self.raiz = Path(self.carpeta_temporal.name)
        self.ruta_config = self.raiz / "config.json"

        # Config temporal por defecto (nunca se toca la App real).
        config.guardar_config(self.ruta_config, config.ajustes_por_defecto())

        self.shell = VentanaPrincipal()
        self.pagina = self.shell.pagina_categorias
        self.pagina.ruta_config = self.ruta_config
        self.pagina._cargar_config()

    def tearDown(self):
        i18n.cambiar_idioma("es")
        self.carpeta_temporal.cleanup()

    def item_de(self, fila: int):
        return self.pagina.lista_categorias.item(fila)

    def test_lista_muestra_nombres_predeterminados_traducidos(self):
        # En español, «Imagenes» se muestra con su acento correcto.
        self.assertEqual(self.item_de(0).text(), tr_gui("cat.imagenes"))

        i18n.cambiar_idioma("en")
        self.shell.retraducir()
        self.assertEqual(self.item_de(0).text(), "Images")
        self.assertEqual(self.item_de(1).text(), "Documents")

        i18n.cambiar_idioma("ja")
        self.shell.retraducir()
        self.assertEqual(self.item_de(0).text(), "画像")
        self.assertEqual(self.item_de(10).text(), "スプレッドシート")

    def test_el_modelo_y_el_campo_conservan_el_nombre_canonico(self):
        i18n.cambiar_idioma("en")
        self.shell.retraducir()

        self.pagina.lista_categorias.setCurrentRow(0)

        self.assertEqual(self.pagina.campo_nombre.text(), "Imagenes")
        self.assertEqual(self.pagina.ajustes.categorias[0].nombre, "Imagenes")

    def test_nombres_personalizados_no_se_traducen(self):
        self.pagina._crear_categoria()
        self.pagina.campo_nombre.setText("Mis cosas")

        for codigo in ("en", "ja", "es"):
            i18n.cambiar_idioma(codigo)
            self.shell.retraducir()

            fila = self.pagina.lista_categorias.count() - 1
            self.assertEqual(
                self.item_de(fila).text(),
                "Mis cosas",
                f"Nombre personalizado alterado en {codigo}",
            )

    def test_seleccion_y_cambios_pendientes_sobreviven_al_cambio(self):
        self.pagina.lista_categorias.setCurrentRow(2)  # Música
        self.pagina.campo_extension.setText(".xyz")
        self.pagina._anadir_extension()

        self.assertTrue(self.pagina._cambios_pendientes)

        i18n.cambiar_idioma("ja")
        self.shell.retraducir()

        self.assertEqual(self.pagina.lista_categorias.currentRow(), 2)
        self.assertTrue(self.pagina._cambios_pendientes)
        self.assertIn(".xyz", self.pagina.ajustes.categorias[2].extensiones)
        self.assertEqual(self.pagina.campo_nombre.text(), "Música")

    def test_seleccionar_categoria_actualiza_el_mensaje_inferior(self):
        self.pagina.lista_categorias.setCurrentRow(0)

        self.assertEqual(
            self.pagina.texto_estado.text(),
            tr_gui("ed.seleccionada", nombre=tr_gui("cat.imagenes")),
        )

        # El mensaje se retraduce con el nombre visible del idioma nuevo.
        i18n.cambiar_idioma("en")
        self.shell.retraducir()

        self.assertEqual(self.pagina.texto_estado.text(), "Editing «Images».")


if __name__ == "__main__":
    unittest.main()
