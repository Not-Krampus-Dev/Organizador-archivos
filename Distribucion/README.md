# Organizador de Archivos — v1.0 (Windows)

Aplicación de escritorio que ordena tus archivos en carpetas por categoría
(imágenes, documentos, música, vídeos y más), mostrando una vista previa de
todo lo que va a mover **antes** de moverlo.

Incluye interfaz en **español, inglés y japonés** (cambiable en cualquier
momento sin reiniciar).

---

## ⚠️ AVISO IMPORTANTE — Cómo está empaquetado el programa

Organizador de Archivos se distribuye como una **carpeta portátil**
(tecnología PyInstaller en modo «onedir»). El archivo
`OrganizadorArchivos.exe` necesita la subcarpeta `_internal` que hay
junto a él para poder funcionar: ahí dentro está el programa real.
Por eso, cuatro reglas sencillas:

1. **Extrae el ZIP completo.** No ejecutes el programa desde dentro
   del archivo ZIP: primero extrae todo y después abre la carpeta.

2. **Conserva la carpeta `OrganizadorArchivos` completa**, con su
   subcarpeta `_internal` dentro. No borres, renombres ni muevas
   `_internal` a otro sitio.

3. **Ejecuta siempre `OrganizadorArchivos.exe` desde dentro de esa
   carpeta** (doble clic sobre el exe).

4. **¿Quieres un icono en el escritorio?** Crea un **acceso
   directo**: clic derecho sobre `OrganizadorArchivos.exe` →
   «Enviar a» → «Escritorio (crear acceso directo)». **Nunca muevas
   únicamente el EXE** fuera de su carpeta: sin `_internal` al lado,
   el programa no arrancará.

---

## Funcionalidades principales

- Organiza archivos por extensión en carpetas de categorías.
- Reconoce extensiones en mayúsculas y minúsculas.
- Crea las carpetas de destino cuando son necesarias.
- Evita sobrescribir archivos con nombres duplicados.
- Los formatos desconocidos se envían a la carpeta `Otros`
  (o se ignoran/marcan, configurable).
- Lista de archivos ignorados por nombre exacto (p. ej. `desktop.ini`).
- Vista previa del plan completo: puedes desmarcar archivos concretos
  antes de mover nada.
- Barra de progreso y resumen al terminar.
- Editor de categorías, extensiones y subcarpetas de destino.
- Preferencias e idioma guardados entre sesiones.

## Requisitos de Windows

- Windows 10 o Windows 11 (64 bits).
- No requiere Python ni ninguna otra instalación: la carpeta del
  programa ya contiene todo lo necesario.

## Cómo descargar y extraer el ZIP

1. Descarga `Organizador-de-Archivos-v1.0-Windows.zip`.
2. Haz clic derecho sobre el ZIP y elige **«Extraer todo…»**.
3. Extrae **manteniendo la estructura de carpetas** (opción
   recomendada: «Mostrar los archivos extraídos al completar»).

> ⚠️ **Importante:** dentro de la carpeta extraída debe quedarse
> siempre la subcarpeta `_internal` **junto al ejecutable**. Esa
> carpeta contiene el programa propiamente dicho; si se mueve, se
> renombra o se borra, la aplicación no arrancará.

## Cómo iniciar el programa

1. Abre la carpeta extraída y entra en `OrganizadorArchivos`.
2. Haz doble clic en `OrganizadorArchivos.exe`.

**Nota de seguridad:** la aplicación **no lleva firma digital**, por lo
que es posible que Windows SmartScreen muestre un aviso la primera vez.
Pulsa **«Más información»** y luego **«Ejecutar de todas formas»**.
No se requiere instalador.

> 💡 Para tener el programa a mano, crea un **acceso directo** al exe
> (ver la regla 4 del aviso de arriba); no muevas el exe de su carpeta.

## Cómo seleccionar origen y destino

- **Carpeta de origen**: la carpeta cuyos archivos quieres organizar
  (por ejemplo, tu carpeta de descargas).
- **Carpeta de destino**: la carpeta donde se crearán las carpetas de
  categorías.

Usa los botones **«Examinar…»** de cada panel. Origen y destino deben
ser **carpetas distintas y existentes**: la aplicación no permite
seleccionar la misma carpeta en ambos campos.

## Cómo analizar y organizar archivos

1. Pulsa **«Analizar archivos»**: se calcula el plan y la tabla muestra
   cada archivo con su categoría, destino previsto y estado.
2. Revisa la vista previa: si no quieres mover algún archivo concreto,
   desmarca su casilla en la columna **«Mover»**.
3. Pulsa **«Organizar archivos»**, confirma y observa la barra de
   progreso. Al terminar verás un resumen (movidos, omitidos, fallidos).

> ⚠️ **Recomendación:** revisa siempre la vista previa antes de
> aceptar. Los archivos se mueven de verdad de la carpeta de origen a
> la de destino. Si algo no te convence, desmárcalo o cancela: al
> cancelar **no se mueve ningún archivo**.

## Cómo personalizar categorías y extensiones

En la página **Categorías**:

- Selecciona una categoría para editar su nombre, subcarpeta de destino
  y extensiones.
- **Añadir**: escribe una extensión (con o sin punto, p. ej. `.blend`)
  y pulsa «Añadir». Si ya pertenece a otra categoría te avisará.
- **Quitar**: pulsa la «×» de la etiqueta de la extensión.
- **Nueva**: crea una categoría desde cero; **Eliminar** borra la
  seleccionada.
- Pulsa **«Guardar cambios»** para aplicar y persistir todo.

## Cómo cambiar el idioma

En la página **Preferencias**, sección **Idioma**, elige entre
**Español**, **English** o **日本語** y pulsa «Guardar cambios»: toda la
interfaz se retraduce al momento, sin reiniciar.

## Dónde se guardan tus preferencias

La configuración (categorías, extensiones, comportamiento e idioma) se
guarda en:

```
%APPDATA%\OrganizadorArchivos\config.json
```

Puedes abrir esa carpeta pegando la ruta en el Explorador de archivos.
Si borras ese archivo, la aplicación vuelve a sus valores por defecto
en el siguiente arranque.

---

## Solución de problemas

| Problema | Qué hacer |
|---|---|
| La aplicación no abre | Comprueba que `_internal` sigue **junto al exe** y que extrajiste el ZIP completo (no ejecutes el exe dentro del ZIP). |
| Windows/SmartScreen bloquea el arranque | «Más información» → «Ejecutar de todas formas». La aplicación no lleva firma digital. |
| El antivirus lo marca como sospechoso | Es una detección típica de falsos positivos en ejecutables sin firma. Descarga el ZIP solo de la fuente oficial y, si tu antivirus lo bloquea, restáuralo de la cuarentena o añade una exclusión para esa carpeta. |
| No aparece ningún archivo al analizar | Comprueba que la carpeta de origen contiene archivos (no solo carpetas) y que no están en la lista de ignorados de Preferencias. |
| No se mueven algunos archivos | Revisa el resumen final: los archivos con error se listan con su motivo (p. ej. archivo en uso por otro programa, o sin permisos). |
| Se perdieron mis preferencias | Comprueba que existe `%APPDATA%\OrganizadorArchivos\config.json`. Si lo borras, se regenera con los valores por defecto. |

## Información técnica breve

- Versión: 1.0 · Windows 64 bits · Empaquetado onedir (no requiere
  instalador).
- Formatos de imagen, música, vídeo, documentos, comprimidos,
  programación, ejecutables, fuentes, datos y presentaciones cubiertos
  por las categorías predeterminadas (11 categorías, editables).

---

*Organizador de Archivos es un proyecto de práctica de programación.
No incluye firma digital ni instalador; se distribuye como carpeta
portable.*
