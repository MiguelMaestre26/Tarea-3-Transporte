"""Modelo del problema de transporte.

Define la clase :class:`ProblemaTransporte`, que almacena y valida la matriz
de costos unitarios, la oferta de cada planta y la demanda de cada centro de
distribucion. Toda la informacion se maneja con estructuras de datos nativas
(listas y diccionarios), sin librerias de optimizacion.
"""

import json


class ErrorDatos(Exception):
    """Excepcion lanzada cuando los datos del problema son invalidos."""


class ProblemaTransporte:
    """Problema de transporte balanceado (Oferta total = Demanda total).

    Atributos:
        costos (list[list[float]]): matriz de costos unitarios [fila][columna].
        oferta (list[float]): unidades disponibles en cada origen.
        demanda (list[float]): unidades requeridas en cada destino.
        origenes (list[str]): nombres de las plantas (filas).
        destinos (list[str]): nombres de los centros de distribucion (columnas).
    """

    # Datos por defecto tomados del enunciado de la tarea.
    COSTOS_POR_DEFECTO = [
        [15, 35, 40, 45],
        [10, 45, 30, 50],
        [25, 20, 55, 20],
    ]
    OFERTA_POR_DEFECTO = [300, 400, 500]
    DEMANDA_POR_DEFECTO = [250, 350, 400, 200]
    ORIGENES_POR_DEFECTO = [
        "Planta San Diego (O1)",
        "Planta Maracay (O2)",
        "Planta Barquisimeto (O3)",
    ]
    DESTINOS_POR_DEFECTO = [
        "C.D. Caracas (D1)",
        "C.D. Maracaibo (D2)",
        "C.D. Pto. La Cruz (D3)",
        "C.D. San Cristobal (D4)",
    ]

    def __init__(self, costos, oferta, demanda, origenes=None, destinos=None):
        """Construye y valida un problema de transporte.

        Los parametros se convierten a estructuras nativas y se validan de
        inmediato. Si algun dato es invalido se lanza :class:`ErrorDatos`.
        """
        self.costos = [list(fila) for fila in costos]
        self.oferta = list(oferta)
        self.demanda = list(demanda)
        self.origenes = self._preparar_nombres(
            origenes, len(self.oferta), "Origen"
        )
        self.destinos = self._preparar_nombres(
            destinos, len(self.demanda), "Destino"
        )
        self.validar()

    # ------------------------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------------------------
    @staticmethod
    def _preparar_nombres(nombres, cantidad, prefijo):
        """Genera nombres por defecto si no se suministran."""
        if nombres is None:
            return ["%s %d" % (prefijo, i + 1) for i in range(cantidad)]
        nombres = list(nombres)
        if len(nombres) != cantidad:
            raise ErrorDatos(
                "Se esperaban %d nombres de %s pero se recibieron %d."
                % (cantidad, prefijo.lower(), len(nombres))
            )
        return nombres

    # ------------------------------------------------------------------
    # Propiedades de conveniencia
    # ------------------------------------------------------------------
    @property
    def numero_origenes(self):
        """Cantidad de plantas (filas de la matriz)."""
        return len(self.oferta)

    @property
    def numero_destinos(self):
        """Cantidad de centros de distribucion (columnas de la matriz)."""
        return len(self.demanda)

    @property
    def total_oferta(self):
        """Suma total de las unidades ofrecidas."""
        return sum(self.oferta)

    @property
    def total_demanda(self):
        """Suma total de las unidades demandadas."""
        return sum(self.demanda)

    @property
    def esta_balanceado(self):
        """Indica si la oferta total coincide con la demanda total."""
        return self.total_oferta == self.total_demanda

    # ------------------------------------------------------------------
    # Validacion
    # ------------------------------------------------------------------
    def validar(self):
        """Valida la coherencia completa de los datos cargados.

        Comprueba que la matriz sea rectangular, que los valores sean
        numericos y no negativos y que el problema este balanceado.
        """
        if not self.costos:
            raise ErrorDatos("La matriz de costos esta vacia.")
        if not self.oferta:
            raise ErrorDatos("La lista de oferta esta vacia.")
        if not self.demanda:
            raise ErrorDatos("La lista de demanda esta vacia.")

        # La matriz debe ser rectangular y coincidir con oferta/demanda.
        numero_columnas = self.numero_destinos
        if len(self.costos) != self.numero_origenes:
            raise ErrorDatos(
                "La matriz de costos tiene %d filas pero hay %d origenes."
                % (len(self.costos), self.numero_origenes)
            )
        for indice, fila in enumerate(self.costos):
            if len(fila) != numero_columnas:
                raise ErrorDatos(
                    "La fila %d de costos tiene %d columnas; se esperaban %d."
                    % (indice, len(fila), numero_columnas)
                )

        # Validacion de tipos y de no negatividad.
        self._validar_numeros_no_negativos(self.oferta, "oferta")
        self._validar_numeros_no_negativos(self.demanda, "demanda")
        for i, fila in enumerate(self.costos):
            self._validar_numeros_no_negativos(fila, "costos (fila %d)" % i)

        # Balanceo: Oferta total debe ser igual a Demanda total.
        if self.total_oferta != self.total_demanda:
            raise ErrorDatos(
                "El problema no esta balanceado: oferta=%s, demanda=%s."
                % (self.total_oferta, self.total_demanda)
            )
        return True

    @staticmethod
    def _validar_numeros_no_negativos(valores, etiqueta):
        """Verifica que todos los elementos sean numeros >= 0."""
        for indice, valor in enumerate(valores):
            if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                raise ErrorDatos(
                    "El valor '%s' en %s (posicion %d) no es numerico."
                    % (valor, etiqueta, indice)
                )
            if valor < 0:
                raise ErrorDatos(
                    "El valor '%s' en %s (posicion %d) es negativo."
                    % (valor, etiqueta, indice)
                )

    # ------------------------------------------------------------------
    # Constructores alternativos
    # ------------------------------------------------------------------
    @classmethod
    def datos_por_defecto(cls):
        """Devuelve el problema de ejemplo descrito en el enunciado."""
        return cls(
            costos=cls.COSTOS_POR_DEFECTO,
            oferta=cls.OFERTA_POR_DEFECTO,
            demanda=cls.DEMANDA_POR_DEFECTO,
            origenes=cls.ORIGENES_POR_DEFECTO,
            destinos=cls.DESTINOS_POR_DEFECTO,
        )

    @classmethod
    def desde_diccionario(cls, datos):
        """Construye un problema a partir de un diccionario validado.

        Se espera un diccionario con las claves: costos, oferta y demanda
        (y opcionalmente origenes y destinos).
        """
        if not isinstance(datos, dict):
            raise ErrorDatos("Los datos deben ser un diccionario.")
        faltantes = {"costos", "oferta", "demanda"} - set(datos.keys())
        if faltantes:
            raise ErrorDatos(
                "Faltan claves obligatorias en los datos: %s."
                % ", ".join(sorted(faltantes))
            )
        return cls(
            costos=datos["costos"],
            oferta=datos["oferta"],
            demanda=datos["demanda"],
            origenes=datos.get("origenes"),
            destinos=datos.get("destinos"),
        )

    @classmethod
    def desde_json(cls, ruta):
        """Carga y valida un problema desde un archivo JSON."""
        try:
            # utf-8-sig tolera el BOM que agregan algunos editores en Windows.
            with open(ruta, "r", encoding="utf-8-sig") as archivo:
                datos = json.load(archivo)
        except FileNotFoundError:
            raise ErrorDatos("No se encontro el archivo: %s" % ruta)
        except json.JSONDecodeError as error:
            raise ErrorDatos("El archivo %s no es un JSON valido: %s" % (ruta, error))
        return cls.desde_diccionario(datos)

    def con_reemplazos(self, costos=None, oferta=None, demanda=None,
                       origenes=None, destinos=None):
        """Devuelve una copia del problema reemplazando los datos indicados.

        Cualquier parametro que se omita conserva su valor actual. El nuevo
        problema se revalida en el constructor, por lo que si el resultado
        queda inconsistente se lanza :class:`ErrorDatos`.
        """
        return ProblemaTransporte(
            costos=self.costos if costos is None else costos,
            oferta=self.oferta if oferta is None else oferta,
            demanda=self.demanda if demanda is None else demanda,
            origenes=self.origenes if origenes is None else origenes,
            destinos=self.destinos if destinos is None else destinos,
        )

    @staticmethod
    def balancear_datos(costos, oferta, demanda,
                        origenes=None, destinos=None, modo="ajustar"):
        """Balancea una copia de los datos (Oferta total = Demanda total).

        Devuelve un diccionario listo para :meth:`desde_diccionario` sin
        modificar las estructuras recibidas. El parametro ``modo`` admite:

            * ``"ajustar"``: incrementa el ultimo valor de oferta o demanda
              para igualar los totales (no cambia las dimensiones).
            * ``"ficticio"``: agrega un origen o destino ficticio con costo 0
              para cubrir la diferencia (no altera los datos reales).
        """
        costos = [list(fila) for fila in costos]
        oferta = list(oferta)
        demanda = list(demanda)
        origenes = None if origenes is None else list(origenes)
        destinos = None if destinos is None else list(destinos)

        total_oferta = sum(oferta)
        total_demanda = sum(demanda)
        if total_oferta == total_demanda:
            return {
                "costos": costos, "oferta": oferta, "demanda": demanda,
                "origenes": origenes, "destinos": destinos,
            }

        if modo == "ficticio":
            if total_oferta < total_demanda:
                # Falta mercancia: se agrega un origen ficticio con costo 0.
                oferta.append(total_demanda - total_oferta)
                costos.append([0 for _ in demanda])
                if origenes is not None:
                    origenes.append("Origen ficticio (balanceo)")
            else:
                # Sobra mercancia: se agrega un destino ficticio con costo 0.
                demanda.append(total_oferta - total_demanda)
                for fila in costos:
                    fila.append(0)
                if destinos is not None:
                    destinos.append("Destino ficticio (balanceo)")
        else:
            # Ajuste del ultimo valor de oferta o demanda.
            if total_oferta < total_demanda:
                oferta[-1] += total_demanda - total_oferta
            else:
                demanda[-1] += total_oferta - total_demanda

        return {
            "costos": costos, "oferta": oferta, "demanda": demanda,
            "origenes": origenes, "destinos": destinos,
        }

    # ------------------------------------------------------------------
    # Representacion
    # ------------------------------------------------------------------
    def crear_matriz_ceros(self):
        """Crea una matriz de asignaciones inicializada en cero."""
        return [
            [0 for _ in range(self.numero_destinos)]
            for _ in range(self.numero_origenes)
        ]

    def __str__(self):
        """Representacion legible del problema (matriz + margenes)."""
        lineas = ["Problema de transporte (%d x %d):" % (
            self.numero_origenes, self.numero_destinos)]
        for i, origen in enumerate(self.origenes):
            fila = "  ".join(
                "%6s" % valor for valor in self.costos[i]
            )
            lineas.append("  %-28s | %s | oferta=%s" % (
                origen, fila, self.oferta[i]))
        margenes = "  ".join("%6s" % dem for dem in self.demanda)
        lineas.append("  %-28s | %s | demanda" % ("", margenes))
        return "\n".join(lineas)
