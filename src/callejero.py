import osmnx as ox
import networkx as nx
import pandas as pd
import re
from Levenshtein import distance
import os
import matplotlib.pyplot as plt
import glob

from typing import Tuple

STREET_FILE_NAME=glob.glob("data/*.csv")[0]

PLACE_NAME = "Madrid, Spain"
MAP_FILE_NAME="data/madrid.graphml"

MAX_SPEEDS = {
    'living_street': '20',
    'residential': '30',
    'road': '30',            
    'service': '20',         
    'primary_link': '40',
    'unclassified': '40',
    'secondary_link': '40',
    'trunk_link': '40',
    'secondary': '50',
    'tertiary': '50',
    'primary': '50',
    'trunk': '50',
    'tertiary_link': '50',
    'busway': '50',
    'motorway_link': '70',
    'motorway': '100',
}


class ServiceNotAvailableError(Exception):
    "Excepción que indica que la navegación no está disponible en este momento"
    pass


class AdressNotFoundError(Exception):
    "Excepción que indica que una dirección buscada no existe en la base de datos"
    pass



def grados_a_decimal(posicion:str) -> float:
    """Función para convertir un string de posición en formato: _º_'_''_
    a decimal, extrayendo los grados, minutos y segundos y calculando el
    valor decimal en grados.

    Args:
        posicion (str): posición geográfica. Ejemplo: “3º42'24.69''W”

    Returns:
        float: posición decimal en grados
    """
    # Eliminamos espacios innecesarios
    posicion = posicion.strip()

    # Creamos un patron regex que cumpla el formato y extraiga grados, minutos y segundos en grupos
    patron = r"(\d+)°(\d+)'([\d.]+)''\s*([NSEW])"
    coincidencias = re.match(patron, posicion)

    # Extraemos cada elemento de los grupos regex
    grados = int(coincidencias.group(1))
    minutos = int(coincidencias.group(2))
    segundos = float(coincidencias.group(3))
    direccion = coincidencias.group(4)

    # Pasamos de grados a decimal
    posicion_dec = grados + minutos/60 + segundos/3600

    # Si la direccion es norte o este, consideramos valores positivos
    if direccion == "N" or direccion == "E":
        return posicion_dec
    
    # Si la direccion es sur u oeste, consideramos valores negativos
    elif direccion == "S" or direccion == "W":
        posicion_dec = posicion_dec * -1
        return posicion_dec



def carga_callejero() -> pd.DataFrame:
    """ Función que carga el callejero de Madrid, lo procesa y devuelve
    un DataFrame con los datos procesados
    
    Args: None
    Returns:
        DataFrame: dataframe con los datos del callejero procesados.
    Raises:
        FileNotFoundError si el fichero csv con las direcciones no existe
    """
    # Si el fichero de direcciones no existe, lanzar error
    if not os.path.exists(STREET_FILE_NAME):
        raise FileNotFoundError
    
    df = pd.read_csv(STREET_FILE_NAME, sep=";", usecols=["VIA_CLASE", "VIA_PAR", "VIA_NOMBRE", "NUMERO", "LATITUD", "LONGITUD"], encoding="latin1")
    
    # Convertimos todos los valores de las columnas "LATITUD" y "LONGITUD" a valor decimal en grados
    df["LATITUD"] = df["LATITUD"].apply(grados_a_decimal)
    df["LONGITUD"] = df["LONGITUD"].apply(grados_a_decimal)

    # Sustituimos los valores nulos de la columna "VIA_PAR" por " " para facilitar la creación de direcciones
    df["VIA_PAR"] = df["VIA_PAR"].fillna(" ")

    # Convertimos los valores de la columna "NUMERO" para facilitar la creación de direcciones
    df["NUMERO"] = df["NUMERO"].apply(lambda x: str(x))
    
    # Creamos una nueva columna que contiene la dirección formada por las columnas del dataframe que refieren a la direccion
    df["DIRECCION"] = df["VIA_CLASE"] + " " + df["VIA_PAR"] + " " + df["VIA_NOMBRE"] + ", " + df["NUMERO"]

    return df



def busca_direccion(direccion:str, callejero:pd.DataFrame) -> Tuple[float,float]:
    """ Función que busca una dirección, dada en el formato
        calle, numero
    en el DataFrame callejero de Madrid y devuelve el par (latitud, longitud) en grados de la
    ubicación geográfica de dicha dirección
    
    Args:
        direccion (str): Nombre completo de la calle con número, en formato "Calle, num"
        callejero (DataFrame): DataFrame con la información de las calles
    Returns:
        Tuple[float,float]: Par de float (latitud,longitud) de la dirección buscada, expresados en grados
    Raises:
        AdressNotFoundError: Si la dirección no existe en la base de datos
    Example:
        busca_direccion("Calle de Alberto Aguilera, 23", data)=(40.42998055555555,-3.7112583333333333)
        busca_direccion("Calle de Alberto Aguilera, 25", data)=(40.43013055555555,-3.7126916666666667)
    """
    # Convertimos el string de entrada a mayúsculas para poder compararlo con el dataframe
    direccion = direccion.upper().strip()

    # Para aplicar fuzzy search utilizamos la distancia de Leivenshtein
    # Esta distancia nos dice los mínimos cambios necesarios para pasar de un string a otro
    callejero["DISTANCIA_LEV"] = callejero["DIRECCION"].apply(lambda x: distance(direccion, str(x).upper()))

    # Buscamos la mínima distancia de Leivenshtein
    min_dist = callejero["DISTANCIA_LEV"].min()

    # Buscamos la dirección con la distancia mínima
    resultado = callejero[callejero["DISTANCIA_LEV"] == min_dist]

    # Establecemos un umbral para aquellas entradas que se alejan mucho de las direcciones del callejero
    umbral = 10

    # Si la distancia supera el umbral, devolvemos error
    if min_dist > umbral:
        raise AdressNotFoundError("La dirección introducida no tiene coincidencias similares.")
    
    # Si hay más de una dirección con la misma distancia Leivenshtein (varias coincidencias), damos a elejir al usuario
    elif len(resultado) > 1:
        resultados = []
        resultado["DIRECCION"].apply(lambda x: resultados.append(x))

        print("Existen varias coincidencias:")

        for i, direccion in enumerate(resultados):
            print(f"{i+1}. {direccion}")

        print(f"{i+2}. Ninguna de las opciones corresponde con la dirección")

        while True:
            try:
                opc = int(input("\n>>Introduzca la opción que desea: "))

                if 1 <= opc <= i+2:
                    break
                
                else:
                    print(f"\nEscoja una de las opciones en pantalla (1 - {i+2})")

            except ValueError:
                print(f"\nDebes introducir un valor numérico entre 1 y {i+2}")
            
        if opc == i+2:
            raise AdressNotFoundError("No pudimos encontrar la dirección introducida.")
            
        else:
            resultado = resultado[resultado["DIRECCION"] == resultados[opc-1]]
            
    print(f"\nHas seleccionado la dirección: {resultado['DIRECCION'].iloc[0]}")    

    # Creamos el par: (latitud, longitud)
    par = (resultado["LATITUD"].iloc[0], resultado["LONGITUD"].iloc[0])

    return par




def carga_grafo() -> nx.MultiDiGraph:
    """ Función que recupera el quiver de calles de Madrid de OpenStreetMap.
    Args: None
    Returns:
        nx.MultiDiGraph: Quiver de las calles de Madrid.
    Raises:
        ServiceNotAvailableError: Si no es posible recuperar el grafo de OpenStreetMap.
    """
    # Si el archivo ya existe, lo cargamos en una variable
    if os.path.exists(MAP_FILE_NAME):
        grafo = ox.load_graphml(MAP_FILE_NAME)
    
    # Si el archivo no existe, lo extraemos de OpenStreetMap y lo guardamos en un fichero
    else:
        try:
            grafo = ox.graph_from_place(PLACE_NAME, "drive")
            ox.save_graphml(grafo, MAP_FILE_NAME)
        except:
            raise ServiceNotAvailableError("No es posible recuperar el grafo de OpenStreetMap")
    
    return grafo

    
def procesa_grafo(multidigrafo:nx.MultiDiGraph) -> nx.DiGraph:
    """ Función que recupera el quiver de calles de Madrid de OpenStreetMap.
    Args:
        multidigrafo: multidigrafo de las calles de Madrid obtenido de OpenStreetMap.
    Returns:
        nx.DiGraph: Grafo dirigido y sin bucles asociado al multidigrafo dado.
    Raises: None
    """
    # Convertimos el multidigrafo a un grafo dirigido
    G = ox.convert.to_digraph(multidigrafo)

    # Obtenemos en una lista los bucles que tiene el grafo
    bucles = list(nx.selfloop_edges(G))

    # Eliminamos los bucles del grafo
    G.remove_edges_from(bucles)

    # Añadimos información del tiempo que se tarda en recorrer una arista a velocidad máxima
    # Lo usaremos posteriormente para calcular la ruta de menor tiempo posible
    for u, v, data in G.edges(data=True):
        hw = data.get("highway")

        if isinstance(hw, list):
            hw = hw[0]

        distancia = data["length"]
        velocidad = int(MAX_SPEEDS[hw]) * (10/36) # en metros/segundo
        data["tiempo"] = distancia / velocidad

        # Por otro lado añadimos otro atributo teniendo en cuenta los cruces
        # Si un nodo tiene el atributo "highway" implica que es un cruce en el que podemos perder tiempo
        # Por ello, si la arista se dirige a un nodo con ese atributo se le suma una penalización = 0.8 * 30
        if "highway" in G.nodes[v]:
            data["tiempo_semaforos"] = data["tiempo"] + 0.8 * 30
        
        else:
            data["tiempo_semaforos"] = data["tiempo"]

    return G


def mostrar_grafo_dirigido(digrafo:nx.DiGraph, camino:list):
    """Función para mostrar información de las aristas y representar 
    un grafo dirigido utilizando NetworkX.

    Args:
        digrafo (nx.DiGraph): grafo dirigido que queremos representar
    """
    # Extraemos la posición (x,y) de los nodos
    pos = {node: (data["x"], data["y"]) for node, data in digrafo.nodes(data=True)}
    aristas_camino = list(zip(camino, camino[1:]))

    # Representamos el grafo con las posiciones extraídas, utilizando matplotlib.pyplot y networkx
    plt.figure(figsize=(9, 9))
    
    # No pintamos las flechas para ahorrar recursos. 
    # Establecemos tamaño de los nodos a 0 y de las aristas a 0.3 para una buena visualización
    nx.draw_networkx(digrafo, pos, node_size=0, arrows=False, with_labels=False, width=0.2)
    
    # Pintamos el camino de un color distinto y de mayor grosor
    nx.draw_networkx_edges(digrafo, pos=pos, edgelist=aristas_camino, edge_color='r', width=2, arrows=False)

    # Pintamos el nodo de origen para facilitar la visualización
    nx.draw_networkx_nodes(digrafo, pos=pos, nodelist=[camino[0]], node_color='b', node_size=50, label="Direccion de origen")

    # Pintamos el nodo de destino para facilitar la visualización
    nx.draw_networkx_nodes(digrafo, pos=pos, nodelist=[camino[len(camino)-1]], node_color='g', node_size=50, label="Dirección de destino")

    # Para facilitar la visualización del camino, vamos a hacer un zoom al camino:

    # Calculamos las posiciones de los nodos del camino
    xs = [pos[n][0] for n in camino]
    ys = [pos[n][1] for n in camino]

    # Hayamos la diferencia entre el menor punto y el máximo de cada eje
    x = max(xs) - min(xs)
    y = max(ys) - min(ys)

    # El lado será el máximo del tamaño de cada eje
    lado = max(x, y)

    # Centro del camino
    cx = (min(xs) + max(xs)) / 2
    cy = (min(ys) + max(ys)) / 2

    # Mitad del lado
    r = lado / 2

    # Margen para mostrar el camino
    margen = 0.003

    # Límites centrados
    plt.xlim(cx - r - margen, cx + r + margen)
    plt.ylim(cy - r - margen, cy + r + margen)

    # Código para que el gráfico mantenga la proporción al cambiar el tamaño de la ventana
    ax = plt.gca()
    ax.set_aspect('equal', adjustable='box')

    plt.title("Mapa de Madrid")
    plt.xlabel("Longitud")
    plt.ylabel("Latitud")
    plt.legend(loc='upper left')
    plt.show()
