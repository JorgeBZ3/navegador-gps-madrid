import callejero as cal
import networkx as nx
import osmnx as ox
import grafo_pesado as gp

# Lo usaremos para traducir los tipos de vías en aquellas que no tengan nombre
TIPOS_VIA_ES = {
    'living_street': 'calle residencial',
    'residential': 'residencial',
    'primary_link': 'enlace de carretera primaria',
    'unclassified': 'vía sin clasificar',
    'secondary_link': 'enlace de carretera secundaria',
    'trunk_link': 'enlace de autovía',
    'secondary': 'carretera secundaria',
    'tertiary': 'carretera terciaria',
    'primary': 'carretera primaria',
    'trunk': 'autovía',
    'tertiary_link': 'enlace de carretera terciaria',
    'busway': 'carril bus',
    'motorway_link': 'enlace de autopista',
    'motorway': 'autopista'
}

class ExitRequest(Exception):
    pass

def obtener_nodo_mas_cercano(G:nx.DiGraph, lon:float, lat:float) -> int:
    """Calcula a partir de unas coordenadas y un grafo, 
    el nodo más cercano a esas coordenadas.

    Args:
        G (nx.Digraph): grafo dirigido
        lon (float): longitud del punto
        lat (float): latitud del punto

    Returns:
        int: nodo más cercano a las coordenadas
    """
    min_dist = float('inf')
    nearest_node = None
    
    for node, data in G.nodes(data=True):
        x = data["x"]   # longitud
        y = data["y"]   # latitud
        
        # Distancia euclídea
        dist = ((x - lon)**2 + (y - lat)**2)**0.5
        
        # Actualizamos el nodo más cercano si la distancia es menor
        if dist < min_dist:
            min_dist = dist
            nearest_node = node
    
    return nearest_node

def hallar_secuencia_calles(G:nx.digraph, camino:list[tuple]) -> list:
    """Devuelve una lista con los nombres de las calles
    con sus respectivas distancias, de las aristas que
    forman el camino

    Args:
        G (nx.digraph): Grafo dirigido del mapa de Madrid
        camino (list[tuple]): Lista de aristas del camino

    Returns:
        list: lista de calles con sus distancias
    """
    secuencia_calles = []

    for u, v in camino:
        edge_data = G[u][v]
        nombre = edge_data.get("name")
        distancia = edge_data.get("length")

        # En algunos casos las aristas contienen varios nombres
        # En ese caso cogemos la primera que aparece
        if isinstance(nombre, list):
            nombre = nombre[0]
            
        # Existen casos de aristas que no tienen nombre ya que pueden ser enlaces de autovías que no tienen nombre
        # En ese caso, en lugar de dar indicaciones en función del nombre, daremos indicaciones en función del tipo de vía
        # Para ello, las traducimos a español
        if not nombre:
            tipo_via = edge_data.get("highway")
            nombre = TIPOS_VIA_ES[tipo_via]         

        secuencia_calles.append(((u,v), nombre, distancia))

    return secuencia_calles

def hallar_giro(G:nx.DiGraph, arista_prev:tuple, arista_post:tuple) -> str:
    """Determina si el paso de una arista a la siguiente implica un giro a la izquierda,
    derecha o si se continúa recto. Para ello calcula el signo del producto cruzado
    entre los vectores de dirección de ambas aristas usando las coordenadas de los
    nodos del grafo.

    Args:
        G (nx.DiGraph): Grafo dirigido del mapa de Madrid
        arista_prev (tuple): arista previa al giro
        arista_post (tuple): arista posterior al giro

    Returns:
        str: devuelve si el giro es a la derecha, a la izquierda o recto
    """
    nodo_1 = G.nodes[arista_prev[0]]
    nodo_2 = G.nodes[arista_prev[1]]
    nodo_3 = G.nodes[arista_post[1]]

    dir_1 = (nodo_2['x'] - nodo_1['x'], nodo_2['y'] - nodo_1['y'])
    dir_2 = (nodo_3['x'] - nodo_2['x'], nodo_3['y'] - nodo_2['y'])

    cruce = dir_1[0] * dir_2[1] - dir_1[1] * dir_2[0]

    eps = 1e-9

    if cruce > eps:
        giro = "left"
    
    elif cruce < -eps:
        giro = "right"
    
    else:
        giro = "recto"
    
    return giro

def generar_instrucciones(G:nx.DiGraph, ruta:list) -> list:
    """Devuelve una lista de instrucciones a partir de una
    lista de secuencia de calles.

    Args:
        G (nx.DiGraph): Grafo dirigido de Madrid
        ruta (list): Secuencia de calles de la ruta

    Returns:
        list: lista de instrucciones para llegar al destino
    """

    instrucciones = []

    # Primera instrucción
    _, primera_calle, primera_dist = ruta[0]
    instrucciones.append(f"Comience la marcha por {primera_calle}.")

    # Instrucciones intermedias
    for i in range(1, len(ruta)-1):

        (arista_prev, calle_actual, dist_actual) = ruta[i-1]
        (arista_post, calle_siguiente, dist_siguiente) = ruta[i]

        # Si no cambia la calle, no se instruye
        if calle_actual == calle_siguiente:
            continue

        giro = hallar_giro(G, ruta[i-1][0], ruta[i][0])

        # Texto de giro
        if giro == "left":
            direccion = "gire a la izquierda"
        elif giro == "right":
            direccion = "gire a la derecha"
        else:
            direccion = "siga recto"

        instrucciones.append(f"Continúe por {calle_actual} durante {dist_actual:.0f} metros y luego {direccion} hacia {calle_siguiente}.")

    # Instrucción de la última calle
    _, ultima_calle, ultima_dist = ruta[-1]

    instrucciones.append(f"Continúe por {ultima_calle} durante {ultima_dist:.0f} metros y habrá llegado a su destino.")

    return instrucciones

def main():
    """Es la función principal del GPS, cargamos los datos, el grafo
    e interactuamos con el usuario para obtener las direcciones que se
    desean. Por último, representa la ruta introducida en el mapa.

    Raises:
        FileNotFoundError: error si no existe archivo "direcciones.csv"
        cal.ServiceNotAvailableError: error si al descargar grafo ocurre algún problema
        ExitRequest: excepción para cerrar el programa
    """
    print("\nCargando datos del callejero de Madrid...")

    # Contro de error: no existe fichero "direcciones.csv"
    try:
        callejero = cal.carga_callejero()
    
    except FileNotFoundError:
        raise FileNotFoundError("El fichero 'direcciones.csv' no existe.")
    
    print("\nDatos cargados correctamente.")
    
    print("\nConstruyendo grafo de calles de Madrid...")

    # Control de posible error al cargar el grafo de OpenStreetMap
    try:
        G = cal.carga_grafo()

    except cal.ServiceNotAvailableError as error:
        raise cal.ServiceNotAvailableError(error)
    
    G = cal.procesa_grafo(G)     
    
    print("\nGrafo creado correctamente.")

    # Bucle para que el programa funcione hasta que el usuario lo interrumpa
    while True:

        while True:
            origen = input("\nIntroduzca la dirección de origen (ENTER para salir): ")

            # Si el usuario pulsa ENTER con la entrada vacía, se cierra el programa
            if origen == "":
                raise ExitRequest
            
            else:
                # Tratamos de encontrar la dirección introducida
                try:
                    coordenadas_ori = cal.busca_direccion(origen, callejero)
                    break

                # Si no encontramos la dirección, mostramos mensaje y volvemos a pedir la dirección al usuario
                except cal.AdressNotFoundError as error:
                    print(error)
        
        while True:
            destino = input("\nIntroduzca la dirección de destino (ENTER para salir): ")

            if destino == "":
                raise ExitRequest
            
            else:
                try:
                    coordenadas_des = cal.busca_direccion(destino, callejero)
                    break
                except cal.AdressNotFoundError as error:
                    print(error)

        # Hallamos el nodo más cercano a las coordenadas de origen
        nodo_origen = obtener_nodo_mas_cercano(G, coordenadas_ori[1], coordenadas_ori[0])

        # Hallamos el nodo más cercano a las coordenadas de destino
        nodo_destino = obtener_nodo_mas_cercano(G, coordenadas_des[1], coordenadas_des[0])

        # Pedimos al usuario el modo que desea
        while True:
            print("\n>>Elija el modo de cálculo de ruta:")
            print("1- Ruta más corta.")
            print("2- Ruta más rápida.")
            print("3- Ruta más rápida, optimizando semáforos.")
            modo_str = input("\n>> Elija una opción (ENTER para salir): ")

            if destino == "":
                raise ExitRequest
            
            else:
                # Calculamos la ruta en función del modo que haya introducido el usuario
                try:
                    modo_int = int(modo_str)
                    if modo_int == 1:
                        camino = gp.camino_minimo(G, gp.distancia, nodo_origen, nodo_destino)
                        break
                    elif modo_int == 2:
                        camino = gp.camino_minimo(G, gp.tiempo, nodo_origen, nodo_destino)
                        break
                    elif modo_int == 3:
                        camino = gp.camino_minimo(G, gp.tiempo_semaforos, nodo_origen, nodo_destino)
                        break
                    else:
                        print("Introduzca un número del 1 al 3")

                except ValueError:
                    print("Introduzca un número entero del 1 al 3.")

        # Creamos la lista de aristas del camino a partir de los nodos
        aristas_camino = list(zip(camino, camino[1:]))

        # Creamos una lista con las calles correspondientes a las aristas
        secuencia_calles = hallar_secuencia_calles(G, aristas_camino)

        # Generamos las instrucciones
        instrucciones = generar_instrucciones(G, secuencia_calles)

        # Mostramos las instrucciones en la terminal
        for i, instruccion in enumerate(instrucciones):
            print(f"{i+1}- {instruccion}")

        # Mostramos el grafo con la ruta
        cal.mostrar_grafo_dirigido(G, camino)


if __name__ == "__main__":
    try:
        main()

    except ExitRequest:
        print("Saliendo del programa...")

    except KeyboardInterrupt:
        print("\nSe ha interrumpido el programa. Saliendo...")

    except cal.ServiceNotAvailableError as error:
        print(error)

    except FileNotFoundError as error:
        print(error)
