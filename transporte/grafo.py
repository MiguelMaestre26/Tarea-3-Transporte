"""Representacion grafica de la red de transporte (Modulo B).

Genera una imagen por cada metodo resuelto. Los nodos de las plantas se
ubican a la izquierda y los centros de distribucion a la derecha. Solo se
dibujan las aristas cuya cantidad transportada sea mayor a cero y el peso de
cada arista indica la cantidad transportada.

Este modulo si puede usar librerias de graficacion (NetworkX + Matplotlib).
"""

import os
import re

import matplotlib

# Se fuerza un backend sin interfaz grafica para poder guardar archivos PNG
# de forma segura en cualquier entorno (consola, servidor, etc.).
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import networkx as nx

from .metodos import ResultadoTransporte


class VisualizadorGrafo:
    """Dibuja y guarda el grafo bipartito de una solucion de transporte."""

    def __init__(self, problema, directorio_salida="salidas"):
        """Guarda el problema y el directorio donde se guardaran las imagenes."""
        self.problema = problema
        self.directorio_salida = directorio_salida
        os.makedirs(self.directorio_salida, exist_ok=True)

    def generar(self, resultado):
        """Genera y guarda la imagen para un :class:`ResultadoTransporte`.

        Devuelve la ruta del archivo PNG generado.
        """
        grafo, posiciones, etiquetas = self._construir_grafo(resultado)
        ruta = os.path.join(
            self.directorio_salida, "grafo_%s.png" % self._nombre_archivo(resultado.nombre_metodo)
        )
        self._dibujar(grafo, posiciones, etiquetas, resultado, ruta)
        return ruta

    # ------------------------------------------------------------------
    # Construccion del grafo
    # ------------------------------------------------------------------
    def _construir_grafo(self, resultado):
        """Crea el DiGraph, las posiciones y las etiquetas de las aristas."""
        problema = self.problema
        grafo = nx.DiGraph()

        etiquetas_nodos = {}
        # Nodos de origen (izquierda).
        for i, nombre in enumerate(problema.origenes):
            identificador = "O%d" % i
            grafo.add_node(identificador)
            etiquetas_nodos[identificador] = "%s\n(oferta=%s)" % (nombre, problema.oferta[i])
        # Nodos de destino (derecha).
        for j, nombre in enumerate(problema.destinos):
            identificador = "D%d" % j
            grafo.add_node(identificador)
            etiquetas_nodos[identificador] = "%s\n(demanda=%s)" % (nombre, problema.demanda[j])

        # Aristas con cantidad transportada > 0.
        etiquetas_aristas = {}
        for i in range(problema.numero_origenes):
            for j in range(problema.numero_destinos):
                cantidad = resultado.asignacion[i][j]
                if cantidad > 0:
                    nodo_origen = "O%d" % i
                    nodo_destino = "D%d" % j
                    grafo.add_edge(nodo_origen, nodo_destino, weight=cantidad)
                    etiquetas_aristas[(nodo_origen, nodo_destino)] = "%g" % cantidad

        posiciones = self._calcular_posiciones()
        self._etiquetas_nodos = etiquetas_nodos
        return grafo, posiciones, etiquetas_aristas

    def _calcular_posiciones(self):
        """Distribuye los nodos a la izquierda (origenes) y derecha (destinos)."""
        posiciones = {}
        n_origenes = self.problema.numero_origenes
        n_destinos = self.problema.numero_destinos

        for i in range(n_origenes):
            posiciones["O%d" % i] = (0, (n_origenes - 1) / 2.0 - i)
        for j in range(n_destinos):
            posiciones["D%d" % j] = (2, (n_destinos - 1) / 2.0 - j)
        return posiciones

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------
    def _dibujar(self, grafo, posiciones, etiquetas_aristas, resultado, ruta):
        """Dibuja el grafo y lo guarda en disco."""
        n_origenes = self.problema.numero_origenes
        nodos_origen = ["O%d" % i for i in range(n_origenes)]
        nodos_destino = [n for n in grafo.nodes if n.startswith("D")]

        # Grosor de arista proporcional a la cantidad transportada.
        pesos = [grafo[u][v]["weight"] for u, v in grafo.edges()]
        maximo = max(pesos) if pesos else 1
        grosores = [1.0 + 4.0 * (peso / maximo) for peso in pesos]

        figura, eje = plt.subplots(figsize=(13, 6.5))

        nx.draw_networkx_nodes(
            grafo, posiciones, nodelist=nodos_origen,
            node_color="#4C8BF5", node_size=2600, ax=eje)
        nx.draw_networkx_nodes(
            grafo, posiciones, nodelist=nodos_destino,
            node_color="#F5A623", node_size=2600, ax=eje)

        nx.draw_networkx_edges(
            grafo, posiciones, width=grosores, edge_color="#555555",
            arrows=True, arrowsize=18, node_size=2600, ax=eje)

        nx.draw_networkx_labels(
            grafo, posiciones, labels=self._etiquetas_nodos,
            font_size=7, ax=eje)

        # Las etiquetas de cada arista (la cantidad asignada) se dibujan una
        # por una y a una altura distinta sobre la arista. Si todas se
        # dibujaran en el punto medio, las rutas que se cruzan en el centro
        # (por ejemplo San Diego->San Cristobal con Maracay->Pto. La Cruz)
        # quedarian superpuestas y no se distinguiria la asignacion de cada
        # metodo. Se desplaza la etiqueta segun la columna de destino para
        # que cada valor quede siempre legible y asociado a su ruta.
        for (nodo_origen, nodo_destino) in grafo.edges():
            columna = int(nodo_destino[1:])
            nx.draw_networkx_edge_labels(
                grafo, posiciones,
                edge_labels={(nodo_origen, nodo_destino): etiquetas_aristas[(nodo_origen, nodo_destino)]},
                label_pos=self._factor_etiqueta(columna),
                font_size=9, font_color="#B00020", font_weight="bold",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85),
                rotate=False, ax=eje)

        # Cuadro resumen: lista explicita de cada asignacion (planta -> centro
        # de distribucion con su cantidad). Asi la imagen no deja ninguna
        # duda de que ruta transporta cuanto en este metodo. Se ubica a la
        # derecha de la red, fuera de los nodos de destino, para no taparlos.
        eje.text(
            2.75, 0.0, self._texto_asignaciones(resultado),
            va="center", ha="left", fontsize=8.5, family="monospace",
            bbox=dict(boxstyle="round,pad=0.6", fc="#F7F7F7", ec="#999999"))

        eje.set_title(
            "Metodo: %s  |  Costo Total = %.2f"
            % (resultado.nombre_metodo, resultado.costo_total),
            fontsize=12)
        eje.axis("off")
        figura.tight_layout()
        figura.savefig(ruta, dpi=130, bbox_inches="tight")
        plt.close(figura)

    def _texto_asignaciones(self, resultado):
        """Devuelve el detalle de cada ruta activa: origen -> destino: cantidad."""
        problema = self.problema
        lineas = ["Asignaciones (unidades):"]
        for i in range(problema.numero_origenes):
            for j in range(problema.numero_destinos):
                cantidad = resultado.asignacion[i][j]
                if cantidad > 0:
                    lineas.append(
                        "%s -> %s: %g"
                        % (problema.origenes[i], problema.destinos[j], cantidad)
                    )
        return "\n".join(lineas)

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def _factor_etiqueta(self, columna):
        """Fraccion de la arista donde se coloca la etiqueta de cantidad.

        Se reparte entre 0.25 y 0.75 segun la columna de destino, de modo que
        las etiquetas de destinos distintos queden separadas horizontalmente y
        nunca coincidan en el mismo punto aunque las aristas se crucen.
        """
        n_destinos = self.problema.numero_destinos
        if n_destinos <= 1:
            return 0.5
        return 0.25 + 0.5 * (columna / float(n_destinos - 1))

    @staticmethod
    def _nombre_archivo(nombre_metodo):
        """Convierte el nombre del metodo en un nombre de archivo valido."""
        limpio = re.sub(r"[^A-Za-z0-9]+", "_", nombre_metodo).strip("_").lower()
        return limpio or "metodo"
