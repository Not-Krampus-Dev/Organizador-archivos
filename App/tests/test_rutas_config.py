# Pruebas de la resolución centralizada de la ruta de config.json.
#
# Cubren: ruta de desarrollo (App/config.json), ruta de la app
# empaquetada (%APPDATA%\OrganizadorArchivos\config.json), creación del
# directorio de datos, migración de configuraciones antiguas (copiar
# sin borrar ni sobrescribir) y que las páginas usan la ruta central.

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# La plataforma debe fijarse antes de importar PySide6.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from gui import rutas
from gui.paginas.pagina_categorias import PaginaCategorias
from organizador import config

APP = QApplication.instance() or QApplication(sys.argv)


class TestResolucionRutaConfig(unittest.TestCase):
    """Resolución de la ruta según el entorno (desarrollo / empaquetada)."""

    def test_en_desarrollo_apunta_a_app_config_json(self):
        esperada = rutas.raiz_desarrollo() / "config.json"

        self.assertEqual(rutas.resolver_ruta_config(frozen=False), esperada)
        # En las pruebas no hay exe: la ruta activa es la de desarrollo.
        self.assertEqual(rutas.ruta_config(), esperada)

    def test_ruta_config_sigue_el_estado_frozen(self):
        self.assertEqual(rutas.ruta_config(), rutas.ruta_desarrollo())

    def test_empaquetada_usa_appdata_con_nombre_de_app(self):
        with tempfile.TemporaryDirectory() as carpeta:
            base = Path(carpeta)

            ruta = rutas.resolver_ruta_config(frozen=True, base=base, legado=[])

            self.assertEqual(
                ruta, base / "OrganizadorArchivos" / "config.json"
            )
            # El directorio de datos se crea al resolver.
            self.assertTrue(ruta.parent.is_dir())

    def test_ruta_empaquetada_respeta_la_base_inyectada(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = rutas.ruta_empaquetada(base=carpeta)

            self.assertEqual(ruta.name, "config.json")
            self.assertEqual(ruta.parent.name, "OrganizadorArchivos")

    def test_rutas_legado_en_desarrollo_solo_apunta_a_app(self):
        self.assertEqual(
            rutas.rutas_legado(frozen=False), [rutas.ruta_desarrollo()]
        )

    def test_rutas_legado_empaquetada_incluye_ejecutable_y_desarrollo(self):
        candidatas = rutas.rutas_legado(frozen=True)

        junto_al_exe = Path(sys.executable).resolve().parent / "config.json"

        self.assertEqual(candidatas[0], junto_al_exe)
        self.assertIn(rutas.ruta_desarrollo(), candidatas)


class TestMigracionConfig(unittest.TestCase):
    """Migración de configuraciones antiguas: copiar, nunca borrar."""

    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()
        self.base = Path(self.carpeta.name)
        self.antigua = self.base / "antigua"
        self.antigua.mkdir()

    def tearDown(self):
        self.carpeta.cleanup()

    def test_migra_la_configuracion_antigua_al_primer_arranque(self):
        ruta_antigua = self.antigua / "config.json"
        ruta_antigua.write_text(
            json.dumps(config._config_a_dict(config.ajustes_por_defecto())),
            encoding="utf-8",
        )

        ruta_nueva = rutas.resolver_ruta_config(
            frozen=True, base=self.base, legado=[ruta_antigua]
        )

        # Copiada y legible como configuración válida.
        self.assertTrue(ruta_nueva.exists())
        self.assertEqual(config.cargar_config(ruta_nueva).idioma, "es")

        # El original se conserva: migrar es copiar, no mover.
        self.assertTrue(ruta_antigua.exists())

    def test_no_sobrescribe_la_configuracion_nueva_existente(self):
        ruta_antigua = self.antigua / "config.json"
        ruta_antigua.write_text(
            json.dumps(config._config_a_dict(config.ajustes_por_defecto())),
            encoding="utf-8",
        )

        ruta_nueva = rutas.resolver_ruta_config(
            frozen=True, base=self.base, legado=[ruta_antigua]
        )
        self.assertTrue(ruta_nueva.exists())

        # La antigua cambia después: la nueva no se altera al resolver.
        contenido_antes = ruta_nueva.read_text(encoding="utf-8")
        ruta_antigua.write_text("{}", encoding="utf-8")

        rutas.resolver_ruta_config(
            frozen=True, base=self.base, legado=[ruta_antigua]
        )

        self.assertEqual(
            ruta_nueva.read_text(encoding="utf-8"), contenido_antes
        )

    def test_sin_configuracion_antigua_no_crea_el_archivo(self):
        ruta_nueva = rutas.resolver_ruta_config(
            frozen=True, base=self.base, legado=[]
        )

        # Se prepara el directorio, pero crear config.json es trabajo
        # de cargar_config, no de la resolución.
        self.assertTrue(ruta_nueva.parent.is_dir())
        self.assertFalse(ruta_nueva.exists())

    def test_configuracion_antigua_corrupta_se_copia_igual(self):
        """La migración preserva el archivo tal cual: nada se pierde."""

        ruta_antigua = self.antigua / "config.json"
        ruta_antigua.write_text("{json roto", encoding="utf-8")

        ruta_nueva = rutas.resolver_ruta_config(
            frozen=True, base=self.base, legado=[ruta_antigua]
        )

        self.assertEqual(ruta_nueva.read_text(encoding="utf-8"), "{json roto")
        self.assertTrue(ruta_antigua.exists())

    def test_fallo_de_disco_en_la_migracion_no_rompe_la_resolucion(self):
        # Una ruta antigua que no se puede copiar (directorio donde se
        # esperaba un archivo) no debe impedir resolver la ruta nueva.
        imposible = self.antigua  # es un directorio, no un archivo

        ruta_nueva = rutas.resolver_ruta_config(
            frozen=True, base=self.base, legado=[imposible]
        )

        self.assertEqual(
            ruta_nueva, self.base / "OrganizadorArchivos" / "config.json"
        )


class TestIntegracionPaginas(unittest.TestCase):
    """Las páginas obtienen la configuración del módulo central."""

    def test_las_paginas_usan_la_ruta_centralizada(self):
        pagina = PaginaCategorias()

        self.assertEqual(pagina.ruta_config, rutas.ruta_desarrollo())


if __name__ == "__main__":
    unittest.main()
