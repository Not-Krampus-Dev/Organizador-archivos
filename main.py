# Biblioteca para trabajar con rutas
from pathlib import Path

# Variable con la ruta de la carpeta
carpeta = Path.home() / "Downloads"

# Lista con las extensiones de las imagenes
extensiones_imagenes = [".jpg", ".jpeg", ".png", ".webp", ".gif"]

# Lista con las extensiones de los documentos
extensiones_documentos = [".pdf", ".txt", ".docx", ".csv"]

# Lista con las extensiones de música
extensiones_musica = [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"]

# Lista con las extensiones de vídeo
extensiones_videos = [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm"]

# Lista con las extensiones de archivos comprimidos
extensiones_comprimidos = [".zip", ".rar", ".7z", ".tar", ".gz"]

# Lista con las extensiones de programación
extensiones_programacion = [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".cs", ".php"]

# Lista con las extensiones de instaladores y ejecutables
extensiones_ejecutables = [".exe", ".msi", ".msix", ".bat", ".cmd"]

# Lista con las extensiones de fuentes
extensiones_fuentes = [".ttf", ".otf", ".woff", ".woff2"]

# Lista con las extensiones de datos
extensiones_datos = [".sql", ".xml", ".yaml", ".yml", ".log", ".json"]

# Lista con las extensiones de presentaciones
extensiones_presentaciones = [".ppt", ".pptx", ".odp"]

# Lista con las extensiones de hojas de cálculo
extensiones_hojas_calculo = [".xls", ".xlsx", ".ods"]

# Lista de archivos a ignorar
archivos_ignorados = ["desktop.ini"]

# Rutas de las carpetas
ruta_imagenes = carpeta / "Imagenes"
ruta_documentos = carpeta / "Documentos"
ruta_musica = carpeta / "Música"
ruta_videos = carpeta / "Vídeos"
ruta_comprimidos = carpeta / "Comprimidos"
ruta_programacion = carpeta / "Programación"
ruta_ejecutables = carpeta / "Ejecutables"
ruta_fuentes = carpeta / "Fuentes"
ruta_datos = carpeta / "Datos"
ruta_presentaciones = carpeta / "Presentaciones"
ruta_hojas_calculo = carpeta / "Hojas de cálculo"
ruta_otros = carpeta / "Otros"

rutas_por_extension = {}

for extension in extensiones_imagenes:
    rutas_por_extension[extension] = ruta_imagenes

for extension in extensiones_documentos:
    rutas_por_extension[extension] = ruta_documentos

for extension in extensiones_musica:
    rutas_por_extension[extension] = ruta_musica

for extension in extensiones_videos:
    rutas_por_extension[extension] = ruta_videos

for extension in extensiones_comprimidos:
    rutas_por_extension[extension] = ruta_comprimidos

for extension in extensiones_programacion:
    rutas_por_extension[extension] = ruta_programacion

for extension in extensiones_ejecutables:
    rutas_por_extension[extension] = ruta_ejecutables

for extension in extensiones_fuentes:
    rutas_por_extension[extension] = ruta_fuentes

for extension in extensiones_datos:
    rutas_por_extension[extension] = ruta_datos

for extension in extensiones_presentaciones:
    rutas_por_extension[extension] = ruta_presentaciones

for extension in extensiones_hojas_calculo:
    rutas_por_extension[extension] = ruta_hojas_calculo

# Función para mover el archivo a la carpeta correspondiente
def mover_archivo(ruta, elemento):
    ruta.mkdir(exist_ok=True)

    destino = ruta / elemento.name
    contador = 1

    while destino.exists():
        destino = ruta / f"{elemento.stem}_{contador}{elemento.suffix}"
        contador += 1

    elemento.rename(destino)

    return destino

# Función para mostrar el archivo y su destino
def mensaje_archivo(elemento, destino):
    print(f"Archivo: {elemento.name}")
    print(f"Destino: {destino}")

# Función para procesar el archivo
def procesar_archivo(ruta, elemento):
    destino = mover_archivo(ruta, elemento)
    mensaje_archivo(elemento, destino)

# Recorre la carpeta y obtiene los elementos de la carpeta
for elemento in carpeta.iterdir():

    if elemento.is_file():

        if elemento.name in archivos_ignorados:
            continue    

        extension = elemento.suffix.lower()

        ruta = rutas_por_extension.get(extension, ruta_otros)

        procesar_archivo(ruta, elemento)

print("Organización terminada")
