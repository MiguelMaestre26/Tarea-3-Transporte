"""Motor algoritmico del problema de transporte (implementado desde cero).

Se implementan tres metodos clasicos para obtener una solucion basica
factible inicial:

    1. Esquina Noroeste.
    2. Costo Minimo.
    3. Aproximacion de Vogel (VAM).

No se utilizan librerias de optimizacion (SciPy, PuLP, OR-Tools, numpy, etc.).
Todo el manejo de matrices se realiza con listas nativas de Python.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ResultadoTransporte:
    """Resultado de aplicar un metodo de transporte.

    Atributos:
        nombre_metodo (str): nombre legible del metodo aplicado.
        asignacion (list[list[float]]): matriz de unidades transportadas.
        costo_total (float): costo total de la distribucion.
    """

    nombre_metodo: str
    asignacion: list
    costo_total: float

    def resumen(self):
        """Devuelve un texto breve con el nombre y el costo total."""
        return "%-30s Costo Total = %.2f" % (self.nombre_metodo, self.costo_total)


class MetodoTransporte(ABC):
    """Clase base abstracta para los metodos de transporte."""

    nombre = "Metodo"

    def __init__(self, problema):
        """Guarda la referencia al problema a resolver."""
        self.problema = problema

    @abstractmethod
    def _calcular_asignacion(self):
        """Devuelve la matriz de asignaciones (implementado por cada metodo)."""

    def resolver(self):
        """Aplica el metodo y devuelve un :class:`ResultadoTransporte`."""
        asignacion = self._calcular_asignacion()
        costo_total = self.calcular_costo(asignacion)
        return ResultadoTransporte(self.nombre, asignacion, costo_total)

    def calcular_costo(self, asignacion):
        """Calcula el costo total de una matriz de asignaciones dada."""
        total = 0.0
        for i in range(self.problema.numero_origenes):
            for j in range(self.problema.numero_destinos):
                total += asignacion[i][j] * self.problema.costos[i][j]
        return total


class EsquinaNoroeste(MetodoTransporte):
    """Metodo de la Esquina Noroeste (Northwest Corner).

    Comienza en la celda superior izquierda y asigna la mayor cantidad
    posible, avanzando hacia la derecha o hacia abajo segun se agote la
    oferta o la demanda.
    """

    nombre = "Esquina Noroeste"

    def _calcular_asignacion(self):
        problema = self.problema
        asignacion = problema.crear_matriz_ceros()

        # Copias de trabajo de la oferta y la demanda (no se modifican los
        # datos originales del problema).
        oferta = list(problema.oferta)
        demanda = list(problema.demanda)

        fila = 0
        columna = 0
        while fila < problema.numero_origenes and columna < problema.numero_destinos:
            cantidad = min(oferta[fila], demanda[columna])
            asignacion[fila][columna] = cantidad
            oferta[fila] -= cantidad
            demanda[columna] -= cantidad

            if oferta[fila] == 0 and demanda[columna] == 0:
                # Ambas se agotan a la vez: se avanza en diagonal.
                fila += 1
                columna += 1
            elif oferta[fila] == 0:
                fila += 1
            else:
                columna += 1
        return asignacion


class CostoMinimo(MetodoTransporte):
    """Metodo del Costo Minimo.

    En cada iteracion selecciona la celda de menor costo entre las filas y
    columnas aun activas y asigna la mayor cantidad posible.
    """

    nombre = "Costo Minimo"

    def _calcular_asignacion(self):
        problema = self.problema
        asignacion = problema.crear_matriz_ceros()
        oferta = list(problema.oferta)
        demanda = list(problema.demanda)

        filas_activas = [True] * problema.numero_origenes
        columnas_activas = [True] * problema.numero_destinos

        while True:
            celda = self._buscar_celda_menor_costo(filas_activas, columnas_activas)
            if celda is None:
                break
            fila, columna = celda
            cantidad = min(oferta[fila], demanda[columna])
            asignacion[fila][columna] = cantidad
            oferta[fila] -= cantidad
            demanda[columna] -= cantidad

            # Se desactiva la fila o la columna (o ambas) que se agoten.
            if oferta[fila] == 0:
                filas_activas[fila] = False
            if demanda[columna] == 0:
                columnas_activas[columna] = False
        return asignacion

    def _buscar_celda_menor_costo(self, filas_activas, columnas_activas):
        """Devuelve (fila, columna) de la celda activa de menor costo."""
        mejor = None
        for i in range(self.problema.numero_origenes):
            if not filas_activas[i]:
                continue
            for j in range(self.problema.numero_destinos):
                if not columnas_activas[j]:
                    continue
                if mejor is None or self.problema.costos[i][j] < self.problema.costos[mejor[0]][mejor[1]]:
                    mejor = (i, j)
        return mejor


class Vogel(MetodoTransporte):
    """Metodo de Aproximacion de Vogel (VAM).

    Calcula penalizaciones por fila y columna (diferencia entre el costo
    minimo y el segundo costo minimo de la linea activa), elige la linea con
    mayor penalizacion y asigna en su celda de menor costo. Se repite hasta
    cubrir toda la oferta y la demanda.
    """

    nombre = "Aproximacion de Vogel (VAM)"

    def _calcular_asignacion(self):
        problema = self.problema
        asignacion = problema.crear_matriz_ceros()
        oferta = list(problema.oferta)
        demanda = list(problema.demanda)

        filas_activas = [True] * problema.numero_origenes
        columnas_activas = [True] * problema.numero_destinos

        while any(filas_activas) and any(columnas_activas):
            linea = self._elegir_linea_mayor_penalizacion(
                filas_activas, columnas_activas)
            tipo, indice = linea
            fila, columna = self._celda_menor_costo_de_linea(
                tipo, indice, filas_activas, columnas_activas)

            cantidad = min(oferta[fila], demanda[columna])
            asignacion[fila][columna] = cantidad
            oferta[fila] -= cantidad
            demanda[columna] -= cantidad

            if oferta[fila] == 0:
                filas_activas[fila] = False
            if demanda[columna] == 0:
                columnas_activas[columna] = False
        return asignacion

    @staticmethod
    def _penalizacion(valores):
        """Penalizacion de una linea: 2do menor costo menos el menor.

        Si la linea solo tiene una celda activa, la penalizacion es el propio
        costo de dicha celda (convencion habitual de VAM).
        """
        if not valores:
            return 0
        if len(valores) == 1:
            return valores[0]
        ordenados = sorted(valores)
        return ordenados[1] - ordenados[0]

    def _elegir_linea_mayor_penalizacion(self, filas_activas, columnas_activas):
        """Devuelve ('fila', i) o ('columna', j) con la mayor penalizacion."""
        mejor_linea = None
        mejor_penalizacion = None

        # Penalizaciones por fila.
        for i in range(self.problema.numero_origenes):
            if not filas_activas[i]:
                continue
            costos = [
                self.problema.costos[i][j]
                for j in range(self.problema.numero_destinos)
                if columnas_activas[j]
            ]
            penalizacion = self._penalizacion(costos)
            if mejor_penalizacion is None or penalizacion > mejor_penalizacion:
                mejor_penalizacion = penalizacion
                mejor_linea = ("fila", i)

        # Penalizaciones por columna.
        for j in range(self.problema.numero_destinos):
            if not columnas_activas[j]:
                continue
            costos = [
                self.problema.costos[i][j]
                for i in range(self.problema.numero_origenes)
                if filas_activas[i]
            ]
            penalizacion = self._penalizacion(costos)
            if mejor_penalizacion is None or penalizacion > mejor_penalizacion:
                mejor_penalizacion = penalizacion
                mejor_linea = ("columna", j)

        return mejor_linea

    def _celda_menor_costo_de_linea(self, tipo, indice, filas_activas, columnas_activas):
        """Devuelve la celda activa de menor costo dentro de una linea."""
        if tipo == "fila":
            fila = indice
            columna = min(
                (j for j in range(self.problema.numero_destinos) if columnas_activas[j]),
                key=lambda j: self.problema.costos[fila][j],
            )
            return fila, columna

        columna = indice
        fila = min(
            (i for i in range(self.problema.numero_origenes) if filas_activas[i]),
            key=lambda i: self.problema.costos[i][columna],
        )
        return fila, columna
