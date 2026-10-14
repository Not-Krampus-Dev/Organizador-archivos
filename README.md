# Organizador de archivos

Script en Python que organiza archivos automáticamente por extensión, utilizando carpetas de categorías.

## Descripción

El organizador recorre la carpeta `Downloads` del usuario actual, identifica los archivos y determina su destino según la extensión.

Los archivos que no coinciden con ninguna categoría se asignan a `Otros`.

El programa incluye un modo de simulación para revisar los destinos previstos antes de mover archivos.

## Características

- Organiza archivos por extensión.
- Reconoce extensiones en mayúsculas y minúsculas.
- Crea las carpetas de destino cuando son necesarias.
- Evita sobrescribir archivos con nombres duplicados.
- Envía formatos desconocidos a `Otros`.
- Ignora los archivos definidos en una lista de exclusión.
- Procesa archivos e ignora carpetas.
- Incluye un modo de simulación activado por defecto.
- Maneja errores comunes del sistema de archivos.
- Muestra un resumen de archivos procesados y fallidos.

## Categorías

- `Imagenes`
- `Documentos`
- `Música`
- `Vídeos`
- `Comprimidos`
- `Programación`
- `Ejecutables`
- `Fuentes`
- `Datos`
- `Presentaciones`
- `Hojas de cálculo`
- `Otros`

## Requisitos

- Python 3.10 o superior.
- No requiere librerías externas.

El proyecto utiliza principalmente la biblioteca estándar `pathlib`.

## Uso

1. Descarga o clona el repositorio.
2. Abre una terminal en la carpeta del proyecto.
3. Ejecuta el programa:

   ```bash
   python main.py
   ```

Por defecto, el programa utiliza la carpeta `Downloads` del usuario actual y ejecuta una simulación. Durante esta simulación, muestra los destinos previstos sin mover archivos.

### Activar el movimiento real

Para organizar los archivos realmente, abre `main.py` y cambia:

```python
simulacion = True
```

por:

```python
simulacion = False
```

Guarda el archivo y vuelve a ejecutar el programa.

**Precaución:** en modo real, los archivos se moverán de la carpeta seleccionada a las categorías correspondientes. Se recomienda probar primero con una carpeta que contenga archivos de prueba.

## Tecnologías y conceptos utilizados

- Python.
- `pathlib`.
- Funciones y parámetros.
- Bucles `for` y `while`.
- Condicionales.
- Listas y diccionarios.
- Conjuntos (`set`) para registrar destinos simulados.
- Manejo de rutas y archivos.
- Manejo de excepciones con `try` y `except`.

## Qué aprendí con este proyecto

Este proyecto fue creado como práctica de Python y como parte de mi portafolio.

Durante su desarrollo practiqué:

- Trabajar con rutas mediante `pathlib`.
- Recorrer archivos y carpetas.
- Obtener nombres y extensiones de archivos.
- Crear funciones con responsabilidades específicas.
- Relacionar extensiones con categorías mediante diccionarios.
- Evitar conflictos con nombres duplicados.
- Controlar errores del sistema de archivos.
- Separar responsabilidades y mejorar la estructura del código.
- Probar el programa en simulación y con movimientos reales.
- Documentar un proyecto para GitHub.

## Mejoras futuras

- Permitir elegir la carpeta desde la terminal.
- Añadir un archivo de configuración para personalizar categorías y extensiones.
- Registrar las operaciones en un archivo de historial.
- Crear una interfaz gráfica de escritorio.
- Ampliar las categorías y los formatos compatibles.

## Estado del proyecto

**Versión 1.1 - En desarrollo**

Esta versión incorpora simulación, manejo básico de errores y un resumen de resultados. El proyecto continúa en desarrollo como práctica de programación y parte de mi portafolio.