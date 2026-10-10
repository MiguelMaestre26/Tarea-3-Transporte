"""Configuracion central del sistema.

Se encarga de localizar la clave de la API de Gemini (GEMINI_API_KEY) y el
modelo a utilizar. La clave se busca primero en las variables de entorno y,
si no existe, en el archivo ".env" ubicado en la raiz del proyecto.

Coloca tu clave real en el archivo ".env" (ver ".env.example").
"""

import os

# Ruta absoluta del archivo .env dentro de la raiz del proyecto.
RUTA_ENV = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

# Valores por defecto.
MODELO_POR_DEFECTO = "gemini-3.8-flash"
VARIABLE_API_KEY = "GEMINI_API_KEY"
VARIABLE_MODELO = "GEMINI_MODELO"


def _leer_archivo_env(ruta=RUTA_ENV):
    """Lee un archivo .env de forma manual (sin dependencias externas).

    Devuelve un diccionario con las variables encontradas. Ignora lineas
    vacias, comentarios (que inician con '#') y valores entre comillas.
    """
    variables = {}
    if not os.path.isfile(ruta):
        return variables

    with open(ruta, "r", encoding="utf-8") as archivo:
        for linea in archivo:
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            nombre, _, valor = linea.partition("=")
            nombre = nombre.strip()
            valor = valor.strip().strip('"').strip("'")
            variables[nombre] = valor
    return variables


def _cargar_dotenv():
    """Intenta cargar python-dotenv si esta instalado (opcional)."""
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(RUTA_ENV)
        return True
    except ImportError:
        return False


def obtener_api_key():
    """Devuelve la clave de Gemini o una cadena vacia si no esta definida."""
    # 1) Variable de entorno del sistema.
    valor = os.environ.get(VARIABLE_API_KEY)
    if valor and valor.strip():
        return valor.strip()

    # 2) Carga via python-dotenv (si esta disponible).
    _cargar_dotenv()
    valor = os.environ.get(VARIABLE_API_KEY)
    if valor and valor.strip():
        return valor.strip()

    # 3) Lectura manual del archivo .env como respaldo.
    return _leer_archivo_env().get(VARIABLE_API_KEY, "").strip()


def obtener_modelo():
    """Devuelve el nombre del modelo de Gemini a utilizar."""
    valor = os.environ.get(VARIABLE_MODELO)
    if valor and valor.strip():
        return valor.strip()

    valor = _leer_archivo_env().get(VARIABLE_MODELO, "").strip()
    return valor or MODELO_POR_DEFECTO
