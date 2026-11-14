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
 
# Recorre la carpeta y obtiene los elementos de la carpeta
for elemento in carpeta.iterdir():

    if elemento.is_file():

        if elemento.name in archivos_ignorados:
            continue    

        extension = elemento.suffix.lower()

        if extension in extensiones_imagenes:
            ruta_imagenes.mkdir(exist_ok=True)

            destino = ruta_imagenes / elemento.name

            elemento.rename(destino)

            print(f"Imagen: {elemento.name}")
            print(f"Destino: {destino}")

        elif extension in extensiones_documentos:
            ruta_documentos.mkdir(exist_ok=True)

            destino  =  ruta_documentos / elemento.name
            elemento.rename(destino)

            print(f"Documento: {elemento.name}")
            print(f"Destino: {destino}")
            
        elif extension in extensiones_musica:
            ruta_musica.mkdir(exist_ok=True)

            destino = ruta_musica / elemento.name
            elemento.rename(destino)

            print(f"Música: {elemento.name}")
            print(f"Destino: {destino}")

        elif extension in extensiones_videos:
            ruta_videos.mkdir(exist_ok=True)

            destino = ruta_videos / elemento.name
            elemento.rename(destino)

            print(f"Vídeo: {elemento.name}")
            print(f"Destino: {destino}")

        elif extension in extensiones_comprimidos:
            ruta_comprimidos.mkdir(exist_ok=True)

            destino = ruta_comprimidos / elemento.name
            elemento.rename(destino)

            print(f"Comprimido: {elemento.name}")
            print(f"Destino: {destino}")

        elif extension in extensiones_programacion:
            ruta_programacion.mkdir(exist_ok=True)

            destino = ruta_programacion / elemento.name
            elemento.rename(destino)

            print(f"Programación: {elemento.name}")
            print(f"Destino: {destino}")

        elif extension in extensiones_ejecutables:
            ruta_ejecutables.mkdir(exist_ok=True)

            destino = ruta_ejecutables / elemento.name
            elemento.rename(destino)

            print(f"Ejecutable: {elemento.name}")
            print(f"Destino: {destino}")

        elif extension in extensiones_fuentes:
            ruta_fuentes.mkdir(exist_ok=True)

            destino = ruta_fuentes / elemento.name
            elemento.rename(destino)
            
            print(f"Fuente: {elemento.name}")
            print(f"Destino: {destino}")

        elif extension in extensiones_datos:
            ruta_datos.mkdir(exist_ok=True)

            destino = ruta_datos / elemento.name
            elemento.rename(destino)

            print(f"Datos: {elemento.name}")
            print(f"Destino: {destino}")

        elif extension in extensiones_presentaciones:
            ruta_presentaciones.mkdir(exist_ok=True)

            destino = ruta_presentaciones / elemento.name
            elemento.rename(destino)

            print(f"Presentación: {elemento.name}")
            print(f"Destino: {destino}")

        elif extension in extensiones_hojas_calculo:
            ruta_hojas_calculo.mkdir(exist_ok=True)

            destino = ruta_hojas_calculo / elemento.name
            elemento.rename(destino)

            print(f"Hoja de cálculo: {elemento.name}")
            print(f"Destino: {destino}")

            # Si no pertenece a ninguna categoría conocida
        else:
            ruta_otros.mkdir(exist_ok=True)

            destino = ruta_otros / elemento.name
            contador = 1

            while destino.exists():
                destino = ruta_otros / f"{elemento.stem}_{contador}{elemento.suffix}"
                contador += 1

            elemento.rename(destino)
            print(f"Destino: {destino}")
            

            print(f"Otros: {elemento.name}") 
            
            

            