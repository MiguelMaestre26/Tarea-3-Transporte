"""Integracion con Inteligencia Artificial (Modulo C).

Se conecta mediante peticiones HTTP (REST) a la API de Gemini. El codigo
construye dinamicamente un prompt que incluye los costos totales obtenidos
por los tres metodos y la matriz de asignacion del mejor metodo, y solicita
una conclusion ejecutiva en el rol de "Consultor Logistico".
"""

import json
import time
import unicodedata

import requests

from config import obtener_api_key, obtener_modelo


class ErrorIA(Exception):
    """Error controlado durante la consulta a la API de inteligencia artificial."""


class ConsultorIA:
    """Cliente REST para la API de Gemini."""

    URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"

    # Reintentos ante errores transitorios del servicio (demanda, red, etc.).
    MAX_REINTENTOS = 5
    ESPERA_REINTENTO = 3  # segundos (crece de forma lineal por intento)
    CODIGOS_REINTENTABLES = (429, 500, 502, 503, 504)

    def __init__(self, api_key=None, modelo=None, timeout=60):
        """Inicializa el cliente.

        La clave se toma del parametro o, si no se indica, del archivo .env /
        variables de entorno mediante :func:`config.obtener_api_key`.
        """
        self.api_key = api_key if api_key is not None else obtener_api_key()
        self.modelo = modelo or obtener_modelo()
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Construccion del prompt
    # ------------------------------------------------------------------
    def construir_prompt(self, resultados, mejor, problema):
        """Construye dinamicamente el prompt enviado a la IA.

        Incluye los costos totales de los tres metodos y la matriz de
        asignacion del mejor metodo.
        """
        lineas = []
        lineas.append(
            "Actua como un 'Consultor Logistico' con amplia experiencia en "
            "investigacion de operaciones y distribucion."
        )
        lineas.append("")
        lineas.append(
            "Contexto: la empresa 'Rutas y Suministros C.A.' debe distribuir "
            "mercancia desde %d plantas hacia %d centros de distribucion. "
            "El problema esta balanceado (oferta = demanda = %s unidades)."
            % (problema.numero_origenes, problema.numero_destinos, problema.total_oferta)
        )
        lineas.append("")
        lineas.append("Costos totales obtenidos por cada metodo:")
        for resultado in resultados:
            lineas.append(
                "- %s: %.2f USD" % (resultado.nombre_metodo, resultado.costo_total)
            )
        lineas.append("")
        lineas.append(
            "El metodo con menor costo total fue: %s (%.2f USD)."
            % (mejor.nombre_metodo, mejor.costo_total)
        )
        lineas.append("")
        lineas.append("Matriz de asignacion (unidades transportadas) del mejor metodo:")
        lineas.append(self._formatear_matriz(mejor, problema))
        lineas.append("")
        lineas.append("Analiza en un texto ejecutivo BREVE (maximo 2 parrafos):")
        lineas.append(
            "1) Por que este metodo supero a los demas matematicamente, "
            "relacionando su logica (penalizaciones, costos minimos, etc.) con el resultado."
        )
        lineas.append(
            "2) Si la distribucion final tiene sentido de negocio, mencionando "
            "las rutas principales y cualquier oportunidad de mejora."
        )
        lineas.append("")
        lineas.append(
            "Responde en espanol, en tono profesional y sin listas numeradas."
        )
        lineas.append(
            "IMPORTANTE: escribe usando SOLO caracteres ASCII. Reemplaza "
            "cualquier vocal acentuada por su version sin acento, no uses la "
            "letra enie (escribe 'n') y no incluyas emojis ni simbolos."
        )
        return "\n".join(lineas)

    @staticmethod
    def _formatear_matriz(resultado, problema):
        """Convierte la matriz de asignacion en texto tabulado legible."""
        encabezado = "%-24s" % "Origen \\ Destino"
        for destino in problema.destinos:
            encabezado += " | %14s" % destino
        filas = [encabezado]
        for i, origen in enumerate(problema.origenes):
            linea = "%-24s" % origen
            for j in range(problema.numero_destinos):
                linea += " | %14g" % resultado.asignacion[i][j]
            filas.append(linea)
        return "\n".join(filas)

    # ------------------------------------------------------------------
    # Consulta a la API
    # ------------------------------------------------------------------
    def analizar(self, resultados, mejor, problema):
        """Realiza la consulta completa a Gemini y devuelve el texto.

        Ante cualquier error (falta de clave, red, cuota, etc.) se devuelve un
        mensaje descriptivo en lugar de lanzar una excepcion, de modo que el
        programa pueda finalizar mostrando los resultados calculados.
        """
        prompt = self.construir_prompt(resultados, mejor, problema)
        try:
            return self._peticion_gemini(prompt)
        except ErrorIA as error:
            return "[No se pudo obtener la conclusion de la IA: %s]" % error

    def _peticion_gemini(self, prompt):
        """Realiza la peticion HTTP POST a la API REST de Gemini."""
        if not self.api_key:
            raise ErrorIA(
                "no se encontro la clave GEMINI_API_KEY. "
                "Colocala en el archivo .env (ver .env.example)."
            )

        url = self.URL_BASE.format(modelo=self.modelo)

        # Se desactiva el "pensamiento" para evitar que el modelo consuma todo
        # el limite de tokens razonando y trunque la respuesta.
        cuerpo = self._construir_cuerpo(prompt, con_thinking=True)
        respuesta = self._enviar_con_reintentos(url, cuerpo)

        # Algunos modelos no admiten "thinkingConfig": se reintenta sin el.
        if respuesta.status_code == 400 and "thinkingConfig" in cuerpo["generationConfig"]:
            cuerpo = self._construir_cuerpo(prompt, con_thinking=False)
            respuesta = self._enviar_con_reintentos(url, cuerpo)

        if respuesta.status_code != 200:
            raise ErrorIA(self._mensaje_de_error(respuesta))

        return self._extraer_texto(respuesta.json())

    @staticmethod
    def _construir_cuerpo(prompt, con_thinking=True):
        """Arma el cuerpo JSON de la peticion a Gemini."""
        configuracion = {
            "temperature": 0.7,
            # Limite amplio para evitar cortes si el modelo razona.
            "maxOutputTokens": 4096,
            "topP": 0.95,
        }
        if con_thinking:
            # thinkingBudget=0 desactiva el razonamiento en modelos que lo
            # soportan (mas rapido y evita truncamientos).
            configuracion["thinkingConfig"] = {"thinkingBudget": 0}
        return {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": configuracion,
        }

    def _enviar_con_reintentos(self, url, cuerpo):
        """Envia la peticion reintentando ante errores transitorios.

        Devuelve la ultima respuesta HTTP recibida. Lanza :class:`ErrorIA`
        solo ante fallos de red que impiden obtener cualquier respuesta.
        """
        ultima = None
        for intento in range(self.MAX_REINTENTOS):
            try:
                ultima = requests.post(
                    url,
                    params={"key": self.api_key},
                    json=cuerpo,
                    timeout=self.timeout,
                )
            except requests.exceptions.Timeout:
                raise ErrorIA("la peticion excedio el tiempo de espera.")
            except requests.exceptions.ConnectionError:
                raise ErrorIA("no hay conexion con el servicio de Gemini.")
            except requests.exceptions.RequestException as error:
                raise ErrorIA("error de red: %s" % error)

            if ultima.status_code not in self.CODIGOS_REINTENTABLES:
                return ultima
            if intento < self.MAX_REINTENTOS - 1:
                time.sleep(self.ESPERA_REINTENTO * (intento + 1))
        return ultima

    @staticmethod
    def _mensaje_de_error(respuesta):
        """Construye un mensaje legible a partir de una respuesta HTTP fallida."""
        detalle = ""
        try:
            datos = respuesta.json()
            detalle = datos.get("error", {}).get("message", "")
        except (ValueError, json.JSONDecodeError):
            detalle = respuesta.text[:200]
        return "HTTP %d: %s" % (respuesta.status_code, detalle or "respuesta invalida")

    @staticmethod
    def _extraer_texto(datos):
        """Extrae el texto generado de la respuesta JSON de Gemini."""
        try:
            candidatos = datos.get("candidates", [])
            partes = candidatos[0]["content"]["parts"]
            texto = "".join(parte.get("text", "") for parte in partes).strip()
        except (IndexError, KeyError, TypeError):
            texto = ""

        if not texto:
            raise ErrorIA("la respuesta de Gemini no contiene texto.")
        return ConsultorIA._a_ascii(texto)

    @staticmethod
    def _a_ascii(texto):
        """Convierte el texto a ASCII: quita acentos y emojis/simbolos.

        Se descompone cada caracter (NFKD) y se conserva unicamente lo que
        pueda representarse en ASCII. Asi 'origenes' con acento se vuelve
        'origenes' y la enie se convierte en 'n', evitando caracteres
        extranos ('?') en consolas que no manejan UTF-8.
        """
        descompuesto = unicodedata.normalize("NFKD", texto)
        return descompuesto.encode("ascii", "ignore").decode("ascii")
