"""Menu interactivo para capturar y modificar el problema de transporte.

Permite al usuario:

    * usar los datos de prueba del enunciado (el ejercicio tal cual),
    * editar oferta, demanda, costos, nombres y dimensiones,
    * cargar un archivo JSON,
    * configurar la generacion de grafos y la consulta a la IA,
    * ejecutar los tres modulos (A, B y C) con los datos actuales.

Cada ejecucion reutiliza el problema que el usuario tenga cargado en ese
momento, por lo que tanto los grafos (Modulo B) como la conclusion de la IA
(Modulo C) se generan a partir de dichos datos y no de los del enunciado.
"""

from .modelo import ProblemaTransporte, ErrorDatos


class MenuInteractivo:
    """Menu de consola para editar los datos y ejecutar el analisis.

    Atributos:
        ejecutar_analisis (callable): funcion encargada de resolver los
            modulos A, B y C. Recibe ``(problema, opciones)``.
        problema (ProblemaTransporte): problema cargado actualmente.
        opciones (dict): banderas "graficos" e "ia" y el "modelo" de IA.
    """

    def __init__(self, ejecutar_analisis, problema=None, opciones=None):
        """Inicializa el menu con el problema y las opciones iniciales."""
        self.ejecutar_analisis = ejecutar_analisis
        self.problema = (
            problema if problema is not None
            else ProblemaTransporte.datos_por_defecto()
        )
        self.opciones = dict(opciones) if opciones else {}
        self.opciones.setdefault("graficos", True)
        self.opciones.setdefault("ia", True)
        self.opciones.setdefault("modelo", None)

    # ------------------------------------------------------------------
    # Bucle principal
    # ------------------------------------------------------------------
    def ejecutar(self):
        """Muestra el menu en bucle hasta que el usuario decida salir."""
        while True:
            self._mostrar_menu()
            opcion = self._leer_linea("Seleccione una opcion").strip()
            try:
                if opcion == "0":
                    print("\n  Saliendo del programa. Hasta luego.")
                    return
                elif opcion == "1":
                    self._usar_datos_prueba()
                elif opcion == "2":
                    self._editar_oferta()
                elif opcion == "3":
                    self._editar_demanda()
                elif opcion == "4":
                    self._editar_costos()
                elif opcion == "5":
                    self._editar_nombres()
                elif opcion == "6":
                    self._gestionar_origenes()
                elif opcion == "7":
                    self._gestionar_destinos()
                elif opcion == "8":
                    self._cargar_json()
                elif opcion == "9":
                    self._ver_problema()
                elif opcion == "10":
                    self._configurar_opciones()
                elif opcion == "11":
                    self._ejecutar()
                else:
                    print("  Opcion no valida. Intente de nuevo.")
            except (KeyboardInterrupt, EOFError):
                print("\n  Saliendo del programa. Hasta luego.")
                return

    def _mostrar_menu(self):
        """Imprime el estado actual y las opciones disponibles."""
        problema = self.problema
        estado = "balanceado" if problema.esta_balanceado else "DESBALANCEADO"
        print("")
        print("=" * 78)
        print(" MENU: OPTIMIZACION DE TRANSPORTE")
        print("=" * 78)
        print(" Datos actuales: %d origenes x %d destinos | oferta=%g, demanda=%g (%s)"
              % (problema.numero_origenes, problema.numero_destinos,
                 problema.total_oferta, problema.total_demanda, estado))
        print(" Grafos: %-3s | IA: %-3s | Modelo IA: %s"
              % ("ON" if self.opciones["graficos"] else "OFF",
                 "ON" if self.opciones["ia"] else "OFF",
                 self.opciones["modelo"] or "(por defecto)"))
        print("-" * 78)
        print("  1) Usar datos de prueba del enunciado")
        print("  2) Editar oferta")
        print("  3) Editar demanda")
        print("  4) Editar costos")
        print("  5) Editar nombres de origenes/destinos")
        print("  6) Agregar/quitar origen (planta)")
        print("  7) Agregar/quitar destino (centro de distribucion)")
        print("  8) Cargar datos desde archivo JSON")
        print("  9) Ver el problema actual")
        print(" 10) Configurar opciones (grafos / IA / modelo)")
        print(" 11) EJECUTAR (metodos A + grafos B + IA C)")
        print("  0) Salir")
        print("-" * 78)

    # ------------------------------------------------------------------
    # Acciones del menu
    # ------------------------------------------------------------------
    def _usar_datos_prueba(self):
        """Carga el problema de ejemplo descrito en el enunciado."""
        self.problema = ProblemaTransporte.datos_por_defecto()
        print("  Datos de prueba del enunciado cargados correctamente.")

    def _editar_oferta(self):
        """Solicita una nueva oferta para cada origen."""
        problema = self.problema
        nueva_oferta = []
        for i, nombre in enumerate(problema.origenes):
            valor = self._leer_flotante(
                "%s (oferta, actual=%g)" % (nombre, problema.oferta[i]),
                minimo=0.0, por_defecto=problema.oferta[i])
            nueva_oferta.append(valor)
        self._aplicar_cambios(
            costos=problema.costos, oferta=nueva_oferta,
            demanda=problema.demanda, origenes=problema.origenes,
            destinos=problema.destinos)

    def _editar_demanda(self):
        """Solicita una nueva demanda para cada destino."""
        problema = self.problema
        nueva_demanda = []
        for j, nombre in enumerate(problema.destinos):
            valor = self._leer_flotante(
                "%s (demanda, actual=%g)" % (nombre, problema.demanda[j]),
                minimo=0.0, por_defecto=problema.demanda[j])
            nueva_demanda.append(valor)
        self._aplicar_cambios(
            costos=problema.costos, oferta=problema.oferta,
            demanda=nueva_demanda, origenes=problema.origenes,
            destinos=problema.destinos)

    def _editar_costos(self):
        """Solicita una nueva fila de costos para cada origen."""
        problema = self.problema
        nuevos_costos = []
        for i, nombre in enumerate(problema.origenes):
            print("  Costos de %s (actual: %s)" % (nombre, problema.costos[i]))
            fila = self._leer_lista_flotantes(
                "costos de %s (Enter = mantener)" % nombre,
                problema.numero_destinos, por_defecto=problema.costos[i])
            nuevos_costos.append(fila)
        self._aplicar_cambios(
            costos=nuevos_costos, oferta=problema.oferta,
            demanda=problema.demanda, origenes=problema.origenes,
            destinos=problema.destinos)

    def _editar_nombres(self):
        """Solicita nuevos nombres para los origenes y los destinos."""
        problema = self.problema
        origenes = []
        for i, nombre in enumerate(problema.origenes):
            texto = self._leer_linea(
                "Origen %d (actual: %s)" % (i + 1, nombre)).strip()
            origenes.append(texto or nombre)
        destinos = []
        for j, nombre in enumerate(problema.destinos):
            texto = self._leer_linea(
                "Destino %d (actual: %s)" % (j + 1, nombre)).strip()
            destinos.append(texto or nombre)
        self._aplicar_cambios(
            costos=problema.costos, oferta=problema.oferta,
            demanda=problema.demanda, origenes=origenes, destinos=destinos)

    def _gestionar_origenes(self):
        """Submenu para agregar o quitar un origen (planta)."""
        problema = self.problema
        print("  Origenes actuales:")
        for i, nombre in enumerate(problema.origenes):
            print("    %d) %s (oferta=%g)" % (i + 1, nombre, problema.oferta[i]))
        print("  a) Agregar origen      q) Quitar origen      Enter) Volver")
        opcion = self._leer_linea("Opcion").strip().lower()
        if opcion == "a":
            self._agregar_origen()
        elif opcion == "q":
            self._quitar_origen()

    def _gestionar_destinos(self):
        """Submenu para agregar o quitar un destino (centro de distribucion)."""
        problema = self.problema
        print("  Destinos actuales:")
        for j, nombre in enumerate(problema.destinos):
            print("    %d) %s (demanda=%g)" % (j + 1, nombre, problema.demanda[j]))
        print("  a) Agregar destino     q) Quitar destino     Enter) Volver")
        opcion = self._leer_linea("Opcion").strip().lower()
        if opcion == "a":
            self._agregar_destino()
        elif opcion == "q":
            self._quitar_destino()

    def _agregar_origen(self):
        """Agrega una nueva fila (origen) con oferta y costos indicados."""
        problema = self.problema
        nombre = self._leer_linea(
            "Nombre del nuevo origen (Enter = automatico)").strip()
        if not nombre:
            nombre = "Origen %d" % (problema.numero_origenes + 1)
        oferta = self._leer_flotante(
            "Oferta del nuevo origen", minimo=0.0, por_defecto=0.0)
        fila = self._leer_lista_flotantes(
            "costos del nuevo origen (%d valores)" % problema.numero_destinos,
            problema.numero_destinos, por_defecto=[0] * problema.numero_destinos)
        self._aplicar_cambios(
            costos=[list(f) for f in problema.costos] + [fila],
            oferta=list(problema.oferta) + [oferta],
            demanda=problema.demanda,
            origenes=list(problema.origenes) + [nombre],
            destinos=problema.destinos)

    def _quitar_origen(self):
        """Elimina un origen (fila) del problema."""
        problema = self.problema
        if problema.numero_origenes <= 1:
            print("  Debe existir al menos un origen.")
            return
        indice = self._leer_entero(
            "Numero del origen a quitar (1..%d)" % problema.numero_origenes,
            minimo=1, maximo=problema.numero_origenes) - 1
        self._aplicar_cambios(
            costos=[f for k, f in enumerate(problema.costos) if k != indice],
            oferta=[v for k, v in enumerate(problema.oferta) if k != indice],
            demanda=problema.demanda,
            origenes=[n for k, n in enumerate(problema.origenes) if k != indice],
            destinos=problema.destinos)

    def _agregar_destino(self):
        """Agrega una nueva columna (destino) con demanda y costos indicados."""
        problema = self.problema
        nombre = self._leer_linea(
            "Nombre del nuevo destino (Enter = automatico)").strip()
        if not nombre:
            nombre = "Destino %d" % (problema.numero_destinos + 1)
        demanda = self._leer_flotante(
            "Demanda del nuevo destino", minimo=0.0, por_defecto=0.0)
        columna = self._leer_lista_flotantes(
            "costos del nuevo destino (%d valores)" % problema.numero_origenes,
            problema.numero_origenes, por_defecto=[0] * problema.numero_origenes)
        nuevos_costos = [
            list(fila) + [columna[i]]
            for i, fila in enumerate(problema.costos)
        ]
        self._aplicar_cambios(
            costos=nuevos_costos, oferta=problema.oferta,
            demanda=list(problema.demanda) + [demanda],
            origenes=problema.origenes,
            destinos=list(problema.destinos) + [nombre])

    def _quitar_destino(self):
        """Elimina un destino (columna) del problema."""
        problema = self.problema
        if problema.numero_destinos <= 1:
            print("  Debe existir al menos un destino.")
            return
        indice = self._leer_entero(
            "Numero del destino a quitar (1..%d)" % problema.numero_destinos,
            minimo=1, maximo=problema.numero_destinos) - 1
        nuevos_costos = [
            [v for k, v in enumerate(fila) if k != indice]
            for fila in problema.costos
        ]
        self._aplicar_cambios(
            costos=nuevos_costos, oferta=problema.oferta,
            demanda=[v for k, v in enumerate(problema.demanda) if k != indice],
            origenes=problema.origenes,
            destinos=[n for k, n in enumerate(problema.destinos) if k != indice])

    def _cargar_json(self):
        """Carga el problema desde un archivo JSON indicado por el usuario."""
        ruta = self._leer_linea("Ruta del archivo JSON").strip().strip('"')
        if not ruta:
            print("  Operacion cancelada.")
            return
        try:
            self.problema = ProblemaTransporte.desde_json(ruta)
        except ErrorDatos as error:
            print("  [ERROR DE DATOS] %s" % error)
            return
        print("  Datos cargados desde: %s" % ruta)

    def _ver_problema(self):
        """Muestra por pantalla el problema cargado actualmente."""
        problema = self.problema
        print("")
        print(problema)
        print("")
        print("  Oferta total = %g | Demanda total = %g | %s"
              % (problema.total_oferta, problema.total_demanda,
                 "Balanceado" if problema.esta_balanceado else "Desbalanceado"))

    def _configurar_opciones(self):
        """Permite activar/desactivar grafos e IA y cambiar el modelo."""
        print("  Grafos actualmente: %s"
              % ("ON" if self.opciones["graficos"] else "OFF"))
        self.opciones["graficos"] = self._confirmar(
            "  ¿Generar grafos al ejecutar?", self.opciones["graficos"])
        print("  IA actualmente: %s"
              % ("ON" if self.opciones["ia"] else "OFF"))
        self.opciones["ia"] = self._confirmar(
            "  ¿Consultar a la IA al ejecutar?", self.opciones["ia"])
        modelo = self._leer_linea(
            "Modelo de IA (actual: %s, Enter = mantener)"
            % (self.opciones["modelo"] or "(por defecto)")).strip()
        if modelo:
            self.opciones["modelo"] = modelo

    def _ejecutar(self):
        """Ejecuta los modulos A, B y C con el problema actual."""
        print("")
        print("  Ejecutando con los datos actuales...")
        self.ejecutar_analisis(self.problema, self.opciones)
        print("")
        self._leer_linea("Presione Enter para volver al menu")

    # ------------------------------------------------------------------
    # Aplicacion de cambios y balanceo
    # ------------------------------------------------------------------
    def _aplicar_cambios(self, costos, oferta, demanda, origenes, destinos):
        """Construye el problema con los datos indicados, validando antes.

        Si el resultado queda desbalanceado se ofrece balancearlo de forma
        automatica. Ante cualquier dato invalido se avisa y no se modifica el
        problema actual.
        """
        total_oferta = sum(oferta)
        total_demanda = sum(demanda)

        if total_oferta != total_demanda:
            print("")
            print("  ADVERTENCIA: el problema quedo desbalanceado.")
            print("    Oferta total = %g | Demanda total = %g | Diferencia = %g"
                  % (total_oferta, total_demanda, total_oferta - total_demanda))
            if not self._confirmar(
                    "  ¿Desea balancearlo automaticamente?", True):
                print("  Cambios descartados (el problema debe estar balanceado).")
                return
            modo = self._elegir_modo_balanceo(total_oferta, total_demanda)
            if modo is None:
                print("  Cambios descartados.")
                return
            datos = ProblemaTransporte.balancear_datos(
                costos, oferta, demanda, origenes, destinos, modo=modo)
        else:
            datos = {
                "costos": costos, "oferta": oferta, "demanda": demanda,
                "origenes": origenes, "destinos": destinos,
            }

        try:
            self.problema = ProblemaTransporte.desde_diccionario(datos)
        except ErrorDatos as error:
            print("  [ERROR DE DATOS] %s" % error)
            print("  Los cambios no se aplicaron.")
            return
        print("  Cambios aplicados. Oferta total = %g | Demanda total = %g."
              % (self.problema.total_oferta, self.problema.total_demanda))

    def _elegir_modo_balanceo(self, total_oferta, total_demanda):
        """Pregunta como balancear: origen/destino ficticio o ajuste."""
        diferencia = total_demanda - total_oferta
        print("  Opciones de balanceo:")
        if diferencia > 0:
            print("    a) Agregar un ORIGEN ficticio con oferta %g y costo 0"
                  % diferencia)
        else:
            print("    a) Agregar un DESTINO ficticio con demanda %g y costo 0"
                  % (-diferencia))
        print("    b) Ajustar el ultimo valor de oferta/demanda")
        opcion = self._leer_linea("Modo (a/b, Enter = b)").strip().lower()
        if opcion == "a":
            return "ficticio"
        if opcion in ("", "b"):
            return "ajustar"
        print("  Opcion no valida; se usara el ajuste del ultimo valor.")
        return "ajustar"

    # ------------------------------------------------------------------
    # Utilidades de entrada
    # ------------------------------------------------------------------
    @staticmethod
    def _leer_linea(mensaje):
        """Lee una linea de texto de la entrada estandar."""
        return input("  %s: " % mensaje)

    def _leer_flotante(self, mensaje, minimo=0.0, por_defecto=None):
        """Lee un numero (acepta coma o punto decimal) con validacion."""
        while True:
            texto = self._leer_linea(mensaje).strip()
            if not texto and por_defecto is not None:
                return por_defecto
            try:
                valor = float(texto.replace(",", "."))
            except ValueError:
                print("    Valor no numerico. Intente de nuevo.")
                continue
            if minimo is not None and valor < minimo:
                print("    El valor no puede ser menor que %g." % minimo)
                continue
            return valor

    def _leer_lista_flotantes(self, mensaje, cantidad, por_defecto=None):
        """Lee una lista de numeros separados por espacios, comas o ';'."""
        while True:
            texto = self._leer_linea(mensaje).strip()
            if not texto and por_defecto is not None:
                return list(por_defecto)
            tokens = texto.replace(",", " ").replace(";", " ").split()
            if len(tokens) != cantidad:
                print("    Se esperaban %d valores y se recibieron %d. "
                      "Intente de nuevo." % (cantidad, len(tokens)))
                continue
            try:
                valores = [float(t) for t in tokens]
            except ValueError:
                print("    Algun valor no es numerico. Intente de nuevo.")
                continue
            if any(valor < 0 for valor in valores):
                print("    Los valores no pueden ser negativos.")
                continue
            return valores

    def _leer_entero(self, mensaje, minimo=None, maximo=None):
        """Lee un numero entero dentro del rango indicado."""
        while True:
            texto = self._leer_linea(mensaje).strip()
            try:
                valor = int(texto)
            except ValueError:
                print("    Debe ser un numero entero. Intente de nuevo.")
                continue
            if minimo is not None and valor < minimo:
                print("    Debe ser mayor o igual a %d." % minimo)
                continue
            if maximo is not None and valor > maximo:
                print("    Debe ser menor o igual a %d." % maximo)
                continue
            return valor

    def _confirmar(self, mensaje, por_defecto=True):
        """Pregunta si/no; el Enter toma el valor por defecto."""
        sufijo = " (S/n)" if por_defecto else " (s/N)"
        while True:
            texto = self._leer_linea(mensaje + sufijo).strip().lower()
            if not texto:
                return por_defecto
            if texto in ("s", "si", "y", "yes"):
                return True
            if texto in ("n", "no"):
                return False
            print("    Responda 's' o 'n'.")
