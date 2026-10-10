"""Punto de entrada del sistema de optimizacion de transporte.

Orquesta los tres modulos:
    A) Algoritmos (Esquina Noroeste, Costo Minimo y VAM).
    B) Representacion en grafo de cada solucion.
    C) Consulta a la IA (Gemini) como "Consultor Logistico".

Ejecucion:
    python main.py
        Abre el menu interactivo para editar los datos y ejecutar el analisis.
        La opcion "usar datos de prueba" reproduce el ejercicio del enunciado.

    python main.py --datos mi_problema.json
        Ejecuta directamente (sin menu) con los datos del archivo.

    python main.py --sin-graficos --sin-ia
        Abre el menu con los grafos y la IA ya desactivados.
"""

import argparse
import sys

from transporte import (
    ProblemaTransporte,
    EsquinaNoroeste,
    CostoMinimo,
    Vogel,
    VisualizadorGrafo,
    ConsultorIA,
    MenuInteractivo,
)
from transporte.modelo import ErrorDatos

SEPARADOR = "=" * 78


def configurar_salida_utf8():
    """Fuerza la salida estandar a UTF-8.

    La consola de Windows suele usar una codificacion (cp1252/cp850) que no
    representa correctamente los acentos ni algunos simbolos, mostrando '?'
    o caracteres extranos. Al reconfigurar la salida a UTF-8 el texto se
    muestra limpio en terminales modernas.
    """
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            # En entornos sin reconfigure (por ejemplo, salidas redirigidas
            # de forma especial) se ignora y se continua sin problemas.
            pass


def crear_parser():
    """Define y devuelve el parser de argumentos de linea de comandos."""
    parser = argparse.ArgumentParser(
        description="Optimizacion de redes de transporte con integracion de IA."
    )
    parser.add_argument(
        "--datos",
        metavar="ARCHIVO.json",
        help="Ruta de un archivo JSON con el problema (costos, oferta, demanda). "
        "Si se omite se usan los datos por defecto del enunciado.",
    )
    parser.add_argument(
        "--modelo",
        metavar="MODELO",
        help="Modelo de Gemini a utilizar (por defecto: gemini-2.0-flash).",
    )
    parser.add_argument(
        "--sin-graficos",
        action="store_true",
        help="No genera las imagenes de los grafos.",
    )
    parser.add_argument(
        "--sin-ia",
        action="store_true",
        help="No realiza la consulta a la IA.",
    )
    return parser


def cargar_problema(ruta):
    """Carga el problema desde JSON o usa los datos por defecto, validando."""
    if ruta:
        print("Cargando datos desde: %s" % ruta)
        return ProblemaTransporte.desde_json(ruta)
    print("Usando datos por defecto del enunciado.")
    return ProblemaTransporte.datos_por_defecto()


def resolver_metodos(problema):
    """Ejecuta los tres metodos y devuelve la lista de resultados."""
    metodos = [EsquinaNoroeste(problema), CostoMinimo(problema), Vogel(problema)]
    return [metodo.resolver() for metodo in metodos]


def seleccionar_mejor(resultados):
    """Devuelve el resultado con el costo total mas bajo."""
    return min(resultados, key=lambda resultado: resultado.costo_total)


def imprimir_matriz_asignacion(resultado, problema):
    """Imprime la matriz de asignaciones de un resultado de forma tabulada."""
    encabezado = "%-24s" % "Origen \\ Destino"
    for destino in problema.destinos:
        encabezado += " | %12s" % destino
    encabezado += " | %10s" % "Oferta"
    print(encabezado)
    print("-" * len(encabezado))
    for i, origen in enumerate(problema.origenes):
        linea = "%-24s" % origen
        suma = 0
        for j in range(problema.numero_destinos):
            valor = resultado.asignacion[i][j]
            suma += valor
            linea += " | %12g" % valor
        linea += " | %10g" % suma
        print(linea)


def imprimir_resultados(resultados, problema):
    """Imprime el detalle de cada metodo y su costo total."""
    for resultado in resultados:
        print("")
        print(SEPARADOR)
        print("METODO: %s" % resultado.nombre_metodo)
        print(SEPARADOR)
        print("Matriz de asignacion (unidades transportadas):")
        imprimir_matriz_asignacion(resultado, problema)
        print("")
        print("COSTO TOTAL (%s): %.2f" % (resultado.nombre_metodo, resultado.costo_total))


def ejecutar_analisis(problema, opciones):
    """Ejecuta los tres modulos (A, B y C) sobre el problema recibido.

    Se usa tanto desde el menu interactivo como desde el modo directo por
    linea de comandos. Los grafos y la consulta a la IA se construyen siempre
    a partir del ``problema`` recibido, de modo que si el usuario edito los
    datos, tanto las imagenes como la conclusion de la IA reflejan esos datos.

    Parametros:
        problema (ProblemaTransporte): problema a resolver.
        opciones (dict): claves "graficos" (bool), "ia" (bool) y "modelo".
    """
    generar_graficos = opciones.get("graficos", True)
    consultar_ia = opciones.get("ia", True)
    modelo = opciones.get("modelo")

    print(SEPARADOR)
    print(" OPTIMIZACION DE REDES DE TRANSPORTE CON INTEGRACION DE IA")
    print(SEPARADOR)

    # --- Modulo A: resolucion de los tres metodos ----------------------
    print("")
    print(problema)
    print("")
    print("Verificacion de balanceo: oferta=%s, demanda=%s (balanceado)."
          % (problema.total_oferta, problema.total_demanda))

    resultados = resolver_metodos(problema)
    imprimir_resultados(resultados, problema)

    mejor = seleccionar_mejor(resultados)

    # --- Modulo B: representacion en grafo -----------------------------
    if generar_graficos:
        print("")
        print(SEPARADOR)
        print(" GENERANDO GRAFOS DE LA RED (Modulo B)")
        print(SEPARADOR)
        try:
            visualizador = VisualizadorGrafo(problema)
            for resultado in resultados:
                ruta = visualizador.generar(resultado)
                print("  Imagen generada: %s" % ruta)
        except Exception as error:  # errores de graficacion no deben romper todo
            print("  [ADVERTENCIA] No se pudieron generar los grafos: %s" % error)

    # --- Modulo C: integracion con IA ----------------------------------
    conclusion_ia = None
    if consultar_ia:
        print("")
        print(SEPARADOR)
        print(" CONSULTA AL CONSULTOR LOGISTICO (IA - Gemini)")
        print(SEPARADOR)
        consultor = ConsultorIA(modelo=modelo)
        print("Consultando a la IA... (esto puede tardar unos segundos)")
        conclusion_ia = consultor.analizar(resultados, mejor, problema)

    # --- Pantalla final de resultados ----------------------------------
    print("")
    print(SEPARADOR)
    print(" RESULTADOS FINALES")
    print(SEPARADOR)
    for resultado in resultados:
        print("  %s" % resultado.resumen())
    print("")
    print("  MEJOR METODO: %s con un costo total de %.2f USD"
          % (mejor.nombre_metodo, mejor.costo_total))

    if conclusion_ia is not None:
        print("")
        print("-" * 78)
        print(" CONCLUSION DEL CONSULTOR LOGISTICO (IA)")
        print("-" * 78)
        print(conclusion_ia)

    print("")
    print(SEPARADOR)


def main():
    """Funcion principal: abre el menu o ejecuta directo si hay --datos."""
    configurar_salida_utf8()
    parser = crear_parser()
    argumentos = parser.parse_args()

    opciones = {
        "graficos": not argumentos.sin_graficos,
        "ia": not argumentos.sin_ia,
        "modelo": argumentos.modelo,
    }

    # Modo directo (no interactivo) cuando se indica un archivo de datos.
    if argumentos.datos:
        try:
            problema = cargar_problema(argumentos.datos)
        except ErrorDatos as error:
            print("\n[ERROR DE DATOS] %s" % error)
            return 2
        ejecutar_analisis(problema, opciones)
        return 0

    # Modo interactivo: menu con los datos por defecto del enunciado.
    menu = MenuInteractivo(ejecutar_analisis, opciones=opciones)
    menu.ejecutar()
    return 0


if __name__ == "__main__":
    sys.exit(main())
