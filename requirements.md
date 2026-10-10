# Optimización de Redes de Transporte con Integración de Inteligencia Artificial

## Contexto del problema

La empresa de distribución logística **“Rutas y Suministros C.A.”** necesita optimizar el envío de mercancía desde sus **tres (3) plantas principales de ensamblaje** hacia **cuatro (4) centros de distribución** a nivel nacional.

El objetivo es determinar la política de envíos que **minimice los costos totales de transporte**.

Como parte del equipo de ingeniería de software y operaciones, se te ha asignado la tarea de desarrollar un sistema automatizado que no solo resuelva el problema utilizando métodos clásicos de Investigación de Operaciones, sino que también modele visualmente la solución y utilice Inteligencia Artificial para analizar los resultados.

El problema se encuentra **balanceado (Oferta = Demanda)**. Los costos de transporte unitario (en dólares) desde cada planta a cada centro de distribución, así como las capacidades y requerimientos, se detallan en la siguiente matriz:

---

## Matriz de costos, oferta y demanda

| Origen / Destino | C.D. Caracas (D1) | C.D. Maracaibo (D2) | C.D. Pto. La Cruz (D3) | C.D. San Cristóbal (D4) | Oferta (Unidades) |
|---|---:|---:|---:|---:|---:|
| Planta San Diego (O1) | 15 | 35 | 40 | 45 | 300 |
| Planta Maracay (O2) | 10 | 45 | 30 | 50 | 400 |
| Planta Barquisimeto (O3) | 25 | 20 | 55 | 20 | 500 |
| **Demanda (Unidades)** | **250** | **350** | **400** | **200** | **Total: 1200** |

**Verificación de balanceo:**

- Oferta total: `300 + 400 + 500 = 1200`
- Demanda total: `250 + 350 + 400 + 200 = 1200`
- Por lo tanto: **Oferta = Demanda = 1200**.

---

## Desarrollo en Python

Se debe desarrollar una solución en **Python** aplicando **programación orientada a objetos (POO)**.

---

## Módulo A: Motor Algorítmico (Desde Cero) — 5 ptos

Debe programar la lógica de los siguientes algoritmos **sin utilizar librerías de optimización preexistentes** (tales como SciPy, PuLP, Google OR-Tools, etc.). Todo el manejo de matrices, iteraciones y asignaciones debe ser implementado con **estructuras de datos nativas**.

1. **Método de la Esquina Noroeste**: Para obtener la primera solución básica factible.
2. **Método del Costo Mínimo**: Para priorizar las rutas más económicas.
3. **Método de Aproximación de Vogel (VAM)**: Calculando las penalizaciones por filas y columnas iterativamente.

**Nota:** Para cada método, el sistema debe calcular e imprimir en consola el **Costo Total** de la distribución.

---

## Módulo B: Representación en Grafo (Modelo de Red) — 5 ptos

Una vez obtenidos los resultados, el sistema debe generar una **imagen para cada método**.

- **Nodos:** Plantas (Izquierda) y Centros de Distribución (Derecha).
- **Aristas:** Deben mostrar las rutas utilizadas (donde la cantidad asignada sea mayor a 0) y el peso de la arista debe indicar la cantidad transportada.
- **Excepción de librerías:** Para este módulo visual, sí está permitido el uso de librerías de graficación (como NetworkX + Matplotlib en Python, o generar un archivo de Graphviz).

---

## Módulo C: Integración con Inteligencia Artificial

El sistema debe conectarse mediante **peticiones HTTP (REST)** a una API de Inteligencia Artificial (por ejemplo, Gemini, OpenAI o Claude).

- **El Prompt:** El código debe construir dinámicamente un prompt que envíe a la IA los costos totales obtenidos por los tres métodos y la matriz de asignación del mejor método.
- **El Objetivo:** Se le debe pedir a la IA que asuma el rol de **“Consultor Logístico”** y devuelva una conclusión ejecutiva breve (**máximo 2 párrafos**) donde analice por qué un método superó a los demás matemáticamente y valide si la distribución final tiene sentido de negocio.
- **Salida:** La respuesta de la IA debe capturarse en el código e imprimirse en la pantalla final de resultados del programa.


## Pautas de Evaluación

1. Usar paradigma de programación orientada a objetos.
2. Realizar validaciones de datos introducidos por el usuario en los comandos y datos cargados.
3. Tener datos por defecto para tomarlos como prueba.
4. En cada módulo se evaluará lo siguiente:
   - Funcionamiento del módulo (errores, resultados correctos, independencia).
   - Legibilidad del código (nombres de variables, código comentado correctamente).
   - El alumno aplicó elementos conceptuales en la programación del módulo.
