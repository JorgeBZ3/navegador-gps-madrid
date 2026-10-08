# Navegador GPS sobre el callejero de Madrid

Proyecto de **Matemática Discreta** · Grado en Ingeniería Matemática e Inteligencia Artificial · Comillas ICAI · Curso 2025/2026

Navegador por consola que, dadas dos direcciones de Madrid, calcula la mejor ruta y genera instrucciones de conducción paso a paso, mostrando el recorrido resaltado sobre el mapa.

## Qué hace

- Modela el callejero como un **grafo ponderado** con datos de OpenStreetMap.
- Calcula la ruta con **Dijkstra parametrizado** por la función de coste. Tres modos:
  1. Ruta más corta (distancia)
  2. Ruta más rápida (velocidad media por tipo de vía)
  3. Ruta más rápida penalizando semáforos
- **Búsqueda difusa de direcciones** (distancia de Levenshtein): tolera abreviaturas, acentos y erratas, como "AVDA" por "AVENIDA".
- Genera instrucciones de giro (izquierda, derecha o recto) con nombres de calle y distancias.
- Dibuja la ruta con zoom automático sobre la zona relevante.

## Cómo ejecutarlo

Requisitos: **Python 3.12 o superior** y conexión a internet.

**1. Clonar el repositorio**

```bash
git clone https://github.com/JorgeBZ3/navegador-gps-madrid.git
cd navegador-gps-madrid
```

**2. Crear y activar el entorno virtual**

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

**3. Instalar las dependencias**

```bash
python -m pip install -r requirements.txt
```

**4. Descargar el fichero de direcciones**

El callejero no se incluye en el repositorio. Descárgalo del Portal de Datos Abiertos del Ayuntamiento de Madrid:

> [Callejero vigente. Relación de direcciones vigentes, con coordenadas (CSV)](https://datos.madrid.es/en/dataset/213605-0-callejero-oficial-madrid/resource/213605-4-callejero-oficial-madrid-csv)

En esa página pulsa el botón de descarga del recurso, renombra el archivo a `direcciones.csv` y guárdalo en la carpeta `data/`, de forma que quede en `data/direcciones.csv`.

**5. Ejecutar `gps.py`**

```bash
cd src   # TODO: ajusta o elimina esta línea según dónde esté gps.py
python gps.py
```

La primera ejecución puede tardar más porque carga el grafo de OpenStreetMap. <!-- TODO: confirma que es así en tu código -->

## Uso

1. Introduce la dirección de **origen** y la de **destino**. Si hay varias coincidencias, el programa te pide elegir una.
2. Elige el modo de cálculo (1, 2 o 3).
3. Se muestran las instrucciones y se abre el mapa con la ruta resaltada.
4. Pulsa `ENTER` sin escribir nada para salir.

Ejemplo de salida:

```
1- Comience la marcha por Calle de Alberto Aguilera.
2- Continúe por Calle de Alberto Aguilera durante 117 metros y luego gire a la izquierda hacia Calle de Serrano Jover.
...
20- Continúe por Avenida de Rafael Ybarra durante 103 metros y habrá llegado a su destino.
```

## Estructura

<!-- TODO: ajusta a tu estructura real -->
```
.
├── data/
│   └── direcciones.csv     # se descarga aparte
├── src/
│   ├── gps.py              # programa principal e interfaz de usuario
│   ├── callejero.py        # carga del callejero y del grafo
│   └── grafo_pesado.py     # Dijkstra y funciones de coste
├── requirements.txt
└── README.md
```

## Tecnologías

Python · NetworkX · OSMnx · pandas · Levenshtein · matplotlib

## Datos

Callejero de datos abiertos del Ayuntamiento de Madrid (licencia CC BY 4.0) y red viaria de © OpenStreetMap contributors.
