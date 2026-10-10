"""Paquete del sistema de optimizacion de redes de transporte.

Contiene los modulos:
    - modelo: definicion y validacion del problema de transporte.
    - metodos: algoritmos (Esquina Noroeste, Costo Minimo y VAM).
    - grafo: representacion visual de las soluciones.
    - ia: integracion con la API de Gemini (consultor logistico).
    - menu: menu interactivo para editar datos y ejecutar el analisis.
"""

from .modelo import ProblemaTransporte
from .metodos import (
    EsquinaNoroeste,
    CostoMinimo,
    Vogel,
    ResultadoTransporte,
)
from .grafo import VisualizadorGrafo
from .ia import ConsultorIA
from .menu import MenuInteractivo

__all__ = [
    "ProblemaTransporte",
    "EsquinaNoroeste",
    "CostoMinimo",
    "Vogel",
    "ResultadoTransporte",
    "VisualizadorGrafo",
    "ConsultorIA",
    "MenuInteractivo",
]
