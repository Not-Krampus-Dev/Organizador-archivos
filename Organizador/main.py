# Biblioteca para trabajar con rutas
from pathlib import Path

# Variable con la ruta de la carpeta
carpeta = Path.home() / "Downloads"

# Extensiones agrupadas por categoría
categorias = {
    "Imagenes": [".jpg", ".jpeg", ".png", ".webp", ".gif"],
    "Documentos": [".pdf", ".txt", ".docx", ".csv"],
    "Música": [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"],
    "Vídeos": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm"],
    "Comprimidos": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Programación": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".cs", ".php"],
    "Ejecutables": [".exe", ".msi", ".msix", ".bat", ".cmd"],
    "Fuentes": [".ttf", ".otf", ".woff", ".woff2"],
    "Datos": [".sql", ".xml", ".yaml", ".yml", ".log", ".json"],
    "Presentaciones": [".ppt", ".pptx", ".odp"],
    "Hojas de cálculo": [".xls", ".xlsx", ".ods"]
}

archivos_ignorados = ["desktop.ini"]

# Crear el diccionario de extensiones y rutas
rutas_por_extension = {}

for categoria, extensiones in categorias.items():
    ruta = carpeta / categoria

    for extension in extensiones:
        rutas_por_extension[extension] = ruta

ruta_otros = carpeta / "Otros"
destinos_simulados = set()

# Función para obtener el destino del archivo
def obtener_destino(ruta, elemento, destinos_simulados):
    destino = ruta / elemento.name
    contador = 1

    while destino.exists() or destino in destinos_simulados:
        destino = ruta / f"{elemento.stem}_{contador}{elemento.suffix}"
        contador += 1

    return destino

# Función para mover el archivo a la carpeta correspondiente
def mover_archivo(ruta, elemento, simulacion, destinos_simulados):
    try:
        if not simulacion:
            ruta.mkdir(parents=True, exist_ok=True)

        destino = obtener_destino(ruta, elemento, destinos_simulados)

        if simulacion:
            destinos_simulados.add(destino)
        else:
            elemento.rename(destino)

        return destino

    except OSError as error:
        print(f"No se pudo procesar {elemento.name}: {error}")
        return None

# Función para mostrar el archivo y su destino
def mensaje_archivo(elemento, destino, simulacion=False):
    print(f"Archivo: {elemento.name}")

    if simulacion:
        print(f"Destino previsto: {destino}")
    else:
        print(f"Destino: {destino}")

# Función para procesar el archivo
def procesar_archivo(ruta, elemento, simulacion, destinos_simulados):
    destino = mover_archivo(ruta, elemento, simulacion, destinos_simulados)

    if destino is None:
        return False

    mensaje_archivo(elemento, destino, simulacion)
    return True


simulacion = True

archivos_procesados = 0
archivos_fallidos = 0

error_acceso = False

print("Simulación de organización de archivos")

try:
    for elemento in carpeta.iterdir():
        if elemento.is_file():
            if elemento.name in archivos_ignorados:
                continue

            extension = elemento.suffix.lower()
            ruta = rutas_por_extension.get(extension, ruta_otros)

            resultado = procesar_archivo(
                ruta, elemento, simulacion, destinos_simulados
            )

            if resultado:
                archivos_procesados += 1
            else:
                archivos_fallidos += 1

except OSError as error:
    error_acceso = True
    print(f"No se pudo acceder a la carpeta {carpeta}: {error}")

if error_acceso:
    print("El proceso terminó con un error de acceso.")
elif simulacion:
    print("Simulación terminada. No se movió ningún archivo.")
else:
    print("Organización terminada.")

print("\n--- Resumen ---")
print(f"Archivos procesados: {archivos_procesados}")
print(f"Archivos fallidos: {archivos_fallidos}")
print("----------------")
