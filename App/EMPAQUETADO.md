# Empaquetado del Organizador de archivos (Windows)

Instrucciones para generar el ejecutable con PyInstaller. No ejecutar
este documento automáticamente: cada paso es manual.

## Requisitos

- Python 3.10+ y el entorno virtual de `App\.venv`.
- Instalar PyInstaller **solo para desarrollo** (no entra en el bundle):

  ```powershell
  cd App
  .venv\Scripts\python.exe -m pip install pyinstaller
  ```

- Dependencias de la app: `PySide6-Essentials==6.12.0`
  (ver `requirements.txt`; el venv actual con PySide6 completo también
  funciona).

## Icono de la aplicación

Colocar el icono en:

```
App\gui\recursos\icono_app.ico
```

Con ese único archivo se activan tres cosas:

1. Icono del ejecutable (la spec lo usa si existe).
2. Icono de la ventana Qt (`main_window._aplicar_icono_ventana`).
3. Queda incluido en el bundle junto al resto de recursos.

Mientras no exista, la app arranca sin icono y sin errores, y la spec
se genera sin icono.

## Generar el ejecutable

```powershell
cd App
.venv\Scripts\python.exe -m PyInstaller --noconfirm OrganizadorArchivos.spec
```

Resultado: `App\dist\OrganizadorArchivos\OrganizadorArchivos.exe`.

Distribuir la **carpeta completa** `dist\OrganizadorArchivos\`
comprimida en ZIP (empaquetado onedir: el exe necesita el resto de
archivos junto a él).

## Dónde se guarda la configuración del usuario

- **Desarrollo**: `App\config.json` (como siempre).
- **Ejecutable**: `%APPDATA%\OrganizadorArchivos\config.json`.

Si junto al ejecutable (o en `App\` de la misma máquina) existe una
configuración antigua, se **copia** a la ubicación nueva en el primer
arranque. El archivo original nunca se borra (ver `gui\rutas.py`).

## Verificación tras el build

1. Arrancar `dist\OrganizadorArchivos\OrganizadorArchivos.exe` en una
   máquina sin Python: la barra lateral debe mostrar los iconos SVG.
2. Cambiar idioma en Preferencias, cerrar y reabrir: debe persistir
   (`%APPDATA%\OrganizadorArchivos\config.json`).
3. Crear/editar una categoría y guardar: debe persistir igual.
4. Comprobar que no aparece consola junto a la ventana (windowed).
