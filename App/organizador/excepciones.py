# Excepciones del motor de organización.

from __future__ import annotations


class ErrorConfiguracion(ValueError):
    """Error de configuración con clave de traducción.

    Es un ValueError (las pruebas y el código existente siguen
    funcionando) pero además lleva:

      · clave:     identificador estable del mensaje (p. ej.
                   "config.nombre_vacio") para la interfaz.
      · parametros: valores interpolados en el mensaje, para que la
                   interfaz pueda regenerarlo en otro idioma.

    El texto en español se construye con los mismos parámetros, así
    str(error) sigue mostrando exactamente el mensaje de siempre.
    """

    def __init__(self, clave: str, mensaje_es: str, **parametros):
        self.clave = clave
        self.parametros = dict(parametros)
        super().__init__(mensaje_es.format(**parametros))
