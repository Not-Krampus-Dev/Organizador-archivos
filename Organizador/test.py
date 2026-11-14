from pathlib import Path

archivo = Path("FOTO.JPG")

extension = archivo.suffix.lower()

print("Archivo:", archivo.name)
print("Extensión original:", archivo.suffix)
print("Extensión para comparar:", extension)