# Organizador de archivos

Script en Python que organiza automáticamente los archivos de la carpeta `Downloads` según su extensión.

## Descripción

Este proyecto recorre la carpeta `Downloads`, identifica los archivos y los mueve a diferentes carpetas según el tipo de archivo.

Los formatos que no están definidos en una categoría se envían a `Otros`.

El programa también evita sobrescribir archivos cuando encuentra un nombre duplicado.

## Características

- Organiza archivos automáticamente por extensión.
- Reconoce extensiones en mayúsculas y minúsculas.
- Crea las carpetas de destino cuando son necesarias.
- Evita sobrescribir archivos duplicados.
- Envía archivos desconocidos a `Otros`.
- Ignora archivos definidos en una lista de exclusión.
- Ignora carpetas y procesa solamente archivos.

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

- Python 3.10 o superior
- No requiere librerías externas.

El proyecto utiliza principalmente la biblioteca estándar `pathlib`.

## Uso

1. Descarga o clona el repositorio.
2. Abre una terminal en la carpeta del proyecto.
3. Ejecuta:

```bash
python main.py
```

El programa trabajará sobre la carpeta `Downloads` del usuario actual.

> Se recomienda revisar los archivos de `Downloads` antes de ejecutar el programa, ya que los archivos serán movidos automáticamente.

## Tecnologías utilizadas

- Python
- `pathlib`
- Funciones
- Bucles `for` y `while`
- Condicionales
- Listas
- Diccionarios
- Manejo de rutas y archivos

## Qué aprendí con este proyecto

Este proyecto fue creado como práctica de Python y como parte de mi portafolio.

Durante su desarrollo practiqué:

- Trabajar con rutas mediante `pathlib`.
- Recorrer archivos y carpetas.
- Obtener nombres y extensiones de archivos.
- Crear y utilizar funciones.
- Utilizar diccionarios para relacionar extensiones con carpetas.
- Manejar archivos duplicados.
- Separar diferentes responsabilidades dentro del programa.
- Organizar y documentar un proyecto para GitHub.

## Mejoras futuras

Algunas mejoras que podrían añadirse en futuras versiones:

- Modo de simulación para mostrar qué archivos se moverían sin modificarlos.
- Archivo de configuración para personalizar las categorías.
- Registro de los archivos organizados.
- Interfaz gráfica.
- Más formatos y categorías.
- Opciones para elegir qué carpeta organizar.

## Estado del proyecto

**Versión 1.0 - Funcional**

El organizador cumple actualmente con su función principal de clasificar y mover archivos automáticamente.
