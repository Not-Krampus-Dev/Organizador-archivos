# Pruebas del motor de organización (Etapa 1).

# Se ejecutan con la biblioteca estándar (unittest), sin dependencias:
#   App\.venv\Scripts\python.exe -m unittest discover -s tests -v
#
# No toca los archivos de Organizador/archivos_prueba: cuando los usa,
# trabaja sobre una copia en un directorio temporal.

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from organizador import config, core
from organizador.models import (
    Ajustes,
    Categoria,
    ComportamientoDesconocidos,
    EstadoPlan,
)


class PruebaTemporal(unittest.TestCase):
    """Base para las pruebas: crea carpetas temporales de origen y destino."""

    def setUp(self):
        self.carpeta_temporal = tempfile.TemporaryDirectory()
        self.raiz = Path(self.carpeta_temporal.name)
        self.origen = self.raiz / "origen"
        self.destino = self.raiz / "destino"
        self.origen.mkdir()

    def tearDown(self):
        self.carpeta_temporal.cleanup()

    def crear_archivo(self, nombre, contenido="prueba", carpeta=None):
        carpeta = carpeta if carpeta is not None else self.origen
        ruta = carpeta / nombre
        ruta.write_text(contenido, encoding="utf-8")
        return ruta

    def ajustes_minimos(self, desconocidos=ComportamientoDesconocidos.OTROS):
        """Configuración reducida para pruebas focalizadas."""

        return Ajustes(
            categorias=[
                Categoria(nombre="Imágenes", extensiones=[".png", ".jpg"]),
                Categoria(nombre="Datos", extensiones=[".json"], destino="Datos"),
            ],
            unknown_files=desconocidos,
            archivos_ignorados=["desktop.ini"],
        )


class TestConfig(PruebaTemporal):

    def test_config_inexistente_genera_valores_por_defecto(self):
        ruta_config = self.raiz / "config" / "config.json"

        ajustes = config.cargar_config(ruta_config)

        self.assertTrue(ruta_config.exists())
        self.assertEqual(len(ajustes.categorias), len(config.CATEGORIAS_POR_DEFECTO))
        self.assertEqual(
            ajustes.unknown_files, ComportamientoDesconocidos.OTROS
        )
        self.assertIn("desktop.ini", ajustes.archivos_ignorados)

    def test_config_por_defecto_reproduce_categorias_del_script_original(self):
        ajustes = config.ajustes_por_defecto()
        nombres = [categoria.nombre for categoria in ajustes.categorias]

        self.assertIn("Imagenes", nombres)
        self.assertIn("Música", nombres)
        self.assertIn("Hojas de cálculo", nombres)

    def test_guardar_y_cargar_mantiene_los_datos(self):
        ruta_config = self.raiz / "config.json"
        ajustes = self.ajustes_minimos(ComportamientoDesconocidos.ADVERTIR)

        config.guardar_config(ruta_config, ajustes)
        cargados = config.cargar_config(ruta_config)

        self.assertEqual(
            cargados.unknown_files, ComportamientoDesconocidos.ADVERTIR
        )
        self.assertEqual(len(cargados.categorias), 2)
        self.assertEqual(cargados.categorias[0].nombre, "Imágenes")
        self.assertEqual(cargados.categorias[0].destino, "Imágenes")
        self.assertEqual(cargados.categorias[1].destino, "Datos")

    def test_archivo_json_tiene_formato_legible(self):
        ruta_config = self.raiz / "config.json"

        config.guardar_config(ruta_config, config.ajustes_por_defecto())
        datos = json.loads(ruta_config.read_text(encoding="utf-8"))

        self.assertIn("categorias", datos)
        self.assertIn("preferencias", datos)
        self.assertIn("unknown_files", datos["preferencias"])

    def test_unknown_files_invalido_lanza_error(self):
        ruta_config = self.raiz / "config.json"
        ruta_config.write_text(
            json.dumps({"preferencias": {"unknown_files": "borrar"}}),
            encoding="utf-8",
        )

        with self.assertRaises(ValueError):
            config.cargar_config(ruta_config)

    def test_categoria_reservada_otros_lanza_error(self):
        ruta_config = self.raiz / "config.json"
        ruta_config.write_text(
            json.dumps({"categorias": [{"nombre": "Otros", "extensiones": [".x"]}]}),
            encoding="utf-8",
        )

        with self.assertRaises(ValueError):
            config.cargar_config(ruta_config)

    def test_extension_duplicada_lanza_error(self):
        ruta_config = self.raiz / "config.json"
        ruta_config.write_text(
            json.dumps(
                {
                    "categorias": [
                        {"nombre": "A", "extensiones": [".png"]},
                        {"nombre": "B", "extensiones": [".PNG"]},
                    ]
                }
            ),
            encoding="utf-8",
        )

        with self.assertRaises(ValueError):
            config.cargar_config(ruta_config)


class TestPlanificar(PruebaTemporal):

    def test_clasifica_por_extension_sin_distinguir_mayusculas(self):
        self.crear_archivo("foto.PNG")
        self.crear_archivo("datos.json")

        plan = core.planificar(self.origen, self.destino, self.ajustes_minimos())

        por_nombre = {entrada.origen.name: entrada for entrada in plan}
        self.assertEqual(por_nombre["foto.PNG"].categoria, "Imágenes")
        self.assertEqual(por_nombre["datos.json"].categoria, "Datos")
        self.assertEqual(
            por_nombre["foto.PNG"].destino, self.destino / "Imágenes" / "foto.PNG"
        )

    def test_todos_los_archivos_estan_listos_e_incluidos(self):
        self.crear_archivo("foto.png")
        self.crear_archivo("notas.txt")

        plan = core.planificar(self.origen, self.destino, self.ajustes_minimos())

        self.assertEqual(len(plan), 2)
        self.assertTrue(all(entrada.incluir for entrada in plan))
        self.assertTrue(
            all(entrada.estado is EstadoPlan.LISTO for entrada in plan)
        )

    def test_archivo_ignorado_aparece_en_el_plan_pero_no_se_incluye(self):
        self.crear_archivo("desktop.ini")
        self.crear_archivo("foto.png")

        plan = core.planificar(self.origen, self.destino, self.ajustes_minimos())

        ignorados = [
            entrada for entrada in plan if entrada.estado is EstadoPlan.IGNORADO
        ]
        self.assertEqual(len(ignorados), 1)
        self.assertEqual(ignorados[0].origen.name, "desktop.ini")
        self.assertFalse(ignorados[0].incluir)
        self.assertIsNone(ignorados[0].destino_resuelto)

    def test_desconocidos_modo_otros(self):
        self.crear_archivo("raro.xyz")

        plan = core.planificar(
            self.origen, self.destino, self.ajustes_minimos(ComportamientoDesconocidos.OTROS)
        )

        entrada = plan[0]
        self.assertEqual(entrada.estado, EstadoPlan.LISTO)
        self.assertTrue(entrada.incluir)
        self.assertEqual(
            entrada.destino_resuelto, self.destino / "Otros" / "raro.xyz"
        )

    def test_desconocidos_modo_ignorar(self):
        self.crear_archivo("raro.xyz")

        plan = core.planificar(
            self.origen, self.destino, self.ajustes_minimos(ComportamientoDesconocidos.IGNORAR)
        )

        entrada = plan[0]
        self.assertEqual(entrada.estado, EstadoPlan.OMITIDO)
        self.assertFalse(entrada.incluir)
        self.assertIsNone(entrada.destino_resuelto)

    def test_desconocidos_modo_advertir(self):
        self.crear_archivo("raro.xyz")

        plan = core.planificar(
            self.origen, self.destino, self.ajustes_minimos(ComportamientoDesconocidos.ADVERTIR)
        )

        entrada = plan[0]
        self.assertEqual(entrada.estado, EstadoPlan.ADVERTIDO)
        self.assertFalse(entrada.incluir)
        self.assertEqual(
            entrada.destino_resuelto, self.destino / "Otros" / "raro.xyz"
        )

    def test_archivo_sin_extension_es_desconocido(self):
        self.crear_archivo("sin_extension")

        plan = core.planificar(
            self.origen, self.destino, self.ajustes_minimos(ComportamientoDesconocidos.IGNORAR)
        )

        self.assertEqual(plan[0].estado, EstadoPlan.OMITIDO)

    def test_conflicto_con_archivo_existente_en_destino(self):
        self.crear_archivo("foto.png")
        ocupado = self.destino / "Imágenes" / "foto.png"
        ocupado.parent.mkdir(parents=True)
        ocupado.write_text("ya existe", encoding="utf-8")

        plan = core.planificar(self.origen, self.destino, self.ajustes_minimos())

        entrada = plan[0]
        self.assertEqual(entrada.estado, EstadoPlan.CONFLICTO)
        self.assertEqual(entrada.destino, ocupado)
        self.assertEqual(entrada.destino_resuelto.name, "foto_1.png")
        self.assertTrue(entrada.incluir)

    def test_no_modifica_la_carpeta_de_origen(self):
        self.crear_archivo("foto.png")
        self.crear_archivo("datos.json")

        core.planificar(self.origen, self.destino, self.ajustes_minimos())

        self.assertEqual(
            {ruta.name for ruta in self.origen.iterdir()},
            {"foto.png", "datos.json"},
        )
        self.assertFalse(self.destino.exists())


class TestEjecutarPlan(PruebaTemporal):

    def test_mueve_los_archivos_y_crea_las_subcarpetas(self):
        self.crear_archivo("foto.png")
        self.crear_archivo("datos.json")
        plan = core.planificar(self.origen, self.destino, self.ajustes_minimos())

        resumen = core.ejecutar_plan(plan)

        self.assertEqual(resumen.movidos, 2)
        self.assertEqual(resumen.fallidos, 0)
        self.assertTrue(
            (self.destino / "Imágenes" / "foto.png").is_file()
        )
        self.assertTrue((self.destino / "Datos" / "datos.json").is_file())
        self.assertEqual(list(self.origen.iterdir()), [])

    def test_resuelve_conflictos_en_la_ejecucion(self):
        self.crear_archivo("foto.png")
        plan = core.planificar(self.origen, self.destino, self.ajustes_minimos())

        # Aparece un archivo con el mismo nombre en el destino después
        # de haber planificado.
        conflicto = self.destino / "Imágenes" / "foto.png"
        conflicto.parent.mkdir(parents=True)
        conflicto.write_text("nuevo", encoding="utf-8")

        resumen = core.ejecutar_plan(plan)

        self.assertEqual(resumen.movidos, 1)
        self.assertFalse(conflicto.read_text(encoding="utf-8") == "prueba")
        self.assertTrue((self.destino / "Imágenes" / "foto_1.png").is_file())

    def test_omitidos_e_ignorados_no_se_mueven(self):
        self.crear_archivo("desktop.ini")
        self.crear_archivo("raro.xyz")
        plan = core.planificar(
            self.origen,
            self.destino,
            self.ajustes_minimos(ComportamientoDesconocidos.IGNORAR),
        )

        resumen = core.ejecutar_plan(plan)

        self.assertEqual(resumen.movidos, 0)
        self.assertEqual(resumen.omitidos, 2)
        self.assertTrue((self.origen / "desktop.ini").is_file())
        self.assertTrue((self.origen / "raro.xyz").is_file())

    def test_advertidos_no_se_mueven_por_defecto(self):
        self.crear_archivo("raro.xyz")
        plan = core.planificar(
            self.origen,
            self.destino,
            self.ajustes_minimos(ComportamientoDesconocidos.ADVERTIR),
        )

        resumen = core.ejecutar_plan(plan)

        self.assertEqual(resumen.movidos, 0)
        self.assertTrue((self.origen / "raro.xyz").is_file())

    def test_advertido_incluido_manualmente_se_mueve_a_otros(self):
        self.crear_archivo("raro.xyz")
        plan = core.planificar(
            self.origen,
            self.destino,
            self.ajustes_minimos(ComportamientoDesconocidos.ADVERTIR),
        )

        plan[0].incluir = True
        resumen = core.ejecutar_plan(plan)

        self.assertEqual(resumen.movidos, 1)
        self.assertTrue((self.destino / "Otros" / "raro.xyz").is_file())

    def test_no_sobrescribe_archivo_existente_con_el_mismo_nombre(self):
        self.crear_archivo("foto.png", contenido="original origen")
        plan = core.planificar(self.origen, self.destino, self.ajustes_minimos())

        conflicto = self.destino / "Imágenes" / "foto.png"
        conflicto.parent.mkdir(parents=True)
        conflicto.write_text("existente destino", encoding="utf-8")

        core.ejecutar_plan(plan)

        self.assertEqual(
            conflicto.read_text(encoding="utf-8"), "existente destino"
        )
        self.assertTrue((self.destino / "Imágenes" / "foto_1.png").is_file())


    def test_ejecutar_plan_notifica_progreso(self):
        self.crear_archivo("foto.png")
        self.crear_archivo("datos.json")
        self.crear_archivo("raro.xyz")  # desconocido → omitido (OTROS)

        ajustes = self.ajustes_minimos()
        ajustes.navegacion_automatica = True  # irrelevante aquí
        plan = core.planificar(self.origen, self.destino, ajustes)

        llamadas = []
        resumen = core.ejecutar_plan(
            plan,
            on_progreso=lambda p, t, f: llamadas.append((p, t, f)),
        )

        # (procesados, total, fallidos) tras cada archivo.
        # raro.xyz va a «Otros» (comportamiento por defecto) y también
        # se mueve: los tres archivos se procesan sin fallos.
        self.assertEqual(
            llamadas, [(1, 3, 0), (2, 3, 0), (3, 3, 0)]
        )
        self.assertEqual(resumen.movidos, 3)
        self.assertEqual(resumen.omitidos, 0)

    def test_ejecutar_plan_sin_callback_es_identico(self):
        self.crear_archivo("foto.png")

        ajustes = self.ajustes_minimos()
        plan = core.planificar(self.origen, self.destino, ajustes)

        resumen = core.ejecutar_plan(plan)

        self.assertEqual(resumen.movidos, 1)
        self.assertEqual(resumen.fallidos, 0)
        self.assertTrue(
            (self.destino / "Imágenes" / "foto.png").is_file()
        )


class TestIntegracionArchivosPrueba(PruebaTemporal):
    """Prueba de integración con una copia de Organizador/archivos_prueba."""

    RUTA_ARCHIVOS_PRUEBA = (
        Path(__file__).resolve().parent.parent.parent
        / "Organizador"
        / "archivos_prueba"
    )

    def setUp(self):
        super().setUp()

        if not self.RUTA_ARCHIVOS_PRUEBA.is_dir():
            self.skipTest("No existe Organizador/archivos_prueba")

        self.origen = self.raiz / "copia_prueba"
        shutil.copytree(self.RUTA_ARCHIVOS_PRUEBA, self.origen)

        # El motor procesa los archivos de la raíz de la carpeta de origen
        # (igual que el script original). Aplanamos la copia para simular
        # una carpeta real tipo "Descargas", sin tocar los originales.
        for ruta in list(self.origen.rglob("*")):
            if ruta.is_file() and ruta.parent != self.origen:
                shutil.move(str(ruta), str(self.origen / ruta.name))

    def test_plan_y_ejecucion_sobre_copia_completa(self):
        ajustes = config.ajustes_por_defecto()
        plan = core.planificar(self.origen, self.destino, ajustes)

        # La copia solo contiene archivos en la raíz de cada subcarpeta;
        # no debe haber estados de conflicto ni advertidos.
        self.assertTrue(
            all(entrada.estado is EstadoPlan.LISTO for entrada in plan)
        )

        resumen = core.ejecutar_plan(plan)

        self.assertEqual(resumen.movidos, len(plan))
        self.assertEqual(resumen.fallidos, 0)

        # La copia original queda vacía: todo se movió al destino.
        restantes = [
            ruta for ruta in self.origen.rglob("*") if ruta.is_file()
        ]
        self.assertEqual(restantes, [])

        # Cada archivo quedó en una subcarpeta de categoría del destino.
        categorias_creadas = {
            carpeta.name for carpeta in self.destino.iterdir() if carpeta.is_dir()
        }
        esperadas = {categoria.nombre for categoria in ajustes.categorias}
        self.assertTrue(categorias_creadas.issubset(esperadas | {"Otros"}))


class TestPreferenciasConfig(PruebaTemporal):
    """Claves nuevas de preferencias: defaults, validación y compatibilidad."""

    def test_defaults_incluyen_navegacion(self):
        ajustes = config.ajustes_por_defecto()

        self.assertTrue(ajustes.navegacion_automatica)
        self.assertEqual(ajustes.retardo_navegacion_ms, 400)

    def test_roundtrip_de_las_claves_nuevas(self):
        ajustes = config.ajustes_por_defecto()
        ajustes.navegacion_automatica = False
        ajustes.retardo_navegacion_ms = 600

        ruta = self.raiz / "config.json"
        config.guardar_config(ruta, ajustes)
        cargados = config.cargar_config(ruta)

        self.assertFalse(cargados.navegacion_automatica)
        self.assertEqual(cargados.retardo_navegacion_ms, 600)

    def test_retardo_no_entero_rechazado(self):
        ajustes = config.ajustes_por_defecto()
        ajustes.retardo_navegacion_ms = "600"

        with self.assertRaises(ValueError):
            config.validar_config(ajustes)

    def test_retardo_booleano_rechazado(self):
        ajustes = config.ajustes_por_defecto()
        ajustes.retardo_navegacion_ms = True

        with self.assertRaises(ValueError):
            config.validar_config(ajustes)

    def test_retardo_fuera_de_rango_rechazado(self):
        for valor in (50, 99, 2001, 5000):
            ajustes = config.ajustes_por_defecto()
            ajustes.retardo_navegacion_ms = valor

            with self.assertRaises(ValueError):
                config.validar_config(ajustes)

    def test_retardo_en_los_extremos_aceptado(self):
        for valor in (100, 2000):
            ajustes = config.ajustes_por_defecto()
            ajustes.retardo_navegacion_ms = valor
            validados = config.validar_config(ajustes)

            self.assertEqual(validados.retardo_navegacion_ms, valor)

    def test_navegacion_automatica_no_booleano_rechazado(self):
        ajustes = config.ajustes_por_defecto()
        ajustes.navegacion_automatica = 1

        with self.assertRaises(ValueError):
            config.validar_config(ajustes)

    def test_config_antigua_sin_claves_nuevas_carga_con_defaults(self):
        """Compatibilidad: config.json anterior a Preferencias."""

        datos = config._config_a_dict(config.ajustes_por_defecto())
        del datos["preferencias"]["navegacion_automatica"]
        del datos["preferencias"]["retardo_navegacion_ms"]

        ajustes = config._config_desde_dict(datos)

        self.assertTrue(ajustes.navegacion_automatica)
        self.assertEqual(ajustes.retardo_navegacion_ms, 400)

    def test_claves_invalidas_al_cargar_rechazadas(self):
        ruta = self.raiz / "config.json"

        datos = config._config_a_dict(config.ajustes_por_defecto())
        datos["preferencias"]["retardo_navegacion_ms"] = 5000
        ruta.write_text(json.dumps(datos), encoding="utf-8")

        with self.assertRaises(ValueError):
            config.cargar_config(ruta)


if __name__ == "__main__":
    unittest.main()
