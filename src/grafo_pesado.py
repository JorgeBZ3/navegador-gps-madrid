from typing import List,Tuple,Dict,Callable,Union
import networkx as nx
import sys

import heapq #Librería para la creación de colas de prioridad

INFTY=sys.float_info.max #Distincia "infinita" entre nodos de un grafo


#En las siguientes funciones, las funciones de peso son funciones que reciben un grafo o digrafo y dos vértices y devuelven un real (su peso)
#Por ejemplo, si las aristas del grafo contienen en sus datos un campo llamado 'valor', una posible función de peso sería:

def distancia(G:nx.Graph,u:object, v:object):
    return G[u][v]['length']

def tiempo(G:nx.Graph,u:object, v:object):
    return G[u][v]['tiempo']

def tiempo_semaforos(G:nx.Graph,u:object, v:object):
    return G[u][v]['tiempo_semaforos']

#y, en tal caso, para calcular Dijkstra con dicho parámetro haríamos

#camino=dijkstra(G,mi_peso,origen, destino)


def dijkstra(G:Union[nx.Graph, nx.DiGraph], peso:Union[Callable[[nx.Graph,object,object],float], Callable[[nx.DiGraph,object,object],float]], origen:object)-> Dict[object,object]:
    """ Calcula un Árbol de Caminos Mínimos para el grafo pesado partiendo
    del vértice "origen" usando el algoritmo de Dijkstra. Calcula únicamente
    el árbol de la componente conexa que contiene a "origen".
    
    Args:
        origen (object): vértice del grafo de origen
    Returns:
        Dict[object,object]: Devuelve un diccionario que indica, para cada vértice alcanzable
            desde "origen", qué vértice es su padre en el árbol de caminos mínimos.
    Raises:
        TypeError: Si origen no es "hashable".
    Example:
        Si G.dijksra(1)={2:1, 3:2, 4:1} entonces 1 es padre de 2 y de 4 y 2 es padre de 3.
        En particular, un camino mínimo desde 1 hasta 3 sería 1->2->3.
    """
    # d[v] = distancia de o a v, inicializada a 0.
    distancia = {v: INFTY for v in G.nodes}
    # padre[v] = vértice anterior a v en el camino mínimo
    padre = {v: None for v in G.nodes}
    distancia[origen] = 0.0
    
    # Cola de prioridad (min-heap) almacena tuplas (distancia_actual, nodo)
    cola_prioridad = [(0.0, origen)] 

    while cola_prioridad:
        # Aqui hacemos el paso 1
        # Extraer el nodo con la menor distancia actual
        d_actual, u = heapq.heappop(cola_prioridad)
        
        # Optimizamos las entradas obsoletas del nodo u
        if d_actual > distancia[u]:
            continue
            
        # Iterar sobre los vecinos de u
        for v in G.neighbors(u):
            # aqui obtenemos el peso de la arista (u, v)
            try:
                peso_uv = peso(G, u, v) 
            except Exception:
                continue 

            # Hacemos el paso 2
            # Cálculo y relajación
            nueva_distancia = distancia[u] + peso_uv
            
            if nueva_distancia < distancia[v]:
                distancia[v] = nueva_distancia
                padre[v] = u
                # Añadir a la cola de prioridad para poder extraerlo en el futuro
                heapq.heappush(cola_prioridad, (nueva_distancia, v))

    # Devolver el diccionario de padres 
    return padre


def camino_minimo(G:Union[nx.Graph, nx.DiGraph], peso:Union[Callable[[nx.Graph,object,object],float], Callable[[nx.DiGraph,object,object],float]] ,origen:object,destino:object)->List[object]:
    """ Calcula el camino mínimo desde el vértice origen hasta el vértice
    destino utilizando el algoritmo de Dijkstra.
    
    Args:
        G (nx.Graph o nx.Digraph): grafo a grado dirigido
        peso (función): función que recibe un grafo o grafo dirigido y dos vértices del mismo y devuelve el peso de la arista que los conecta
        origen (object): vértice del grafo de origen
        destino (object): vértice del grafo de destino
    Returns:
        List[object]: Devuelve una lista con los vértices del grafo por los que pasa
            el camino más corto entre el origen y el destino. El primer elemento de
            la lista es origen y el último destino.
    Example:
        Si dijksra(G,peso,1,4)=[1,5,2,4] entonces el camino más corto en G entre 1 y 4 es 1->5->2->4.
    Raises:
        TypeError: Si origen o destino no son "hashable".
    """
    # Primer paso
    # Calculamos el árbol de caminos mínimos usando Dijkstra
    arbol_padres = dijkstra(G, peso, origen)
    
    # Segundo paso
    # Reconstruimos el camino yendo hacia atrás desde el destino al origen
    if destino not in arbol_padres:
        return [] # Destino no está en el grafo
    
    camino = []
    actual = destino

    # Hay que verificar si el destino se puede alcanzar
    # Para ello hay que ver si tiene un padre o es el origen, ya que sino no hay camino
    if actual != origen and arbol_padres.get(actual) is None:
        return []

    while actual is not None:
        camino.append(actual)
        
        if actual == origen:
            break
        
        actual = arbol_padres.get(actual)

    # Como el camino se construye del destino al origen, hay que invertirlo para obtener el camino correcto (del origen al destino)
    camino.reverse()
    
    # Si la lista esta vacia o el origen no es el inicio, no hay camino
    # Por lo tanto, si la lista comienza en el origen es un camino valido
    if not camino or camino[0] != origen:
        return []

    return camino


def prim(G:nx.Graph, peso:Callable[[nx.Graph,object,object],float])-> Dict[object,object]:
    """ Calcula un Árbol Abarcador Mínimo para el grafo pesado
    usando el algoritmo de Prim.
    
    Args: None
    Returns:
        G (nx.Graph): grafo
        peso (función): función que recibe un grafo y dos vértices del grafo y devuelve el peso de la arista que los conecta
        Dict[object,object]: Devuelve un diccionario que indica, para cada vértice del
            grafo, qué vértice es su padre en el árbol abarcador mínimo.
    Raises: None
    Example:
        Si prim(G,peso)={1: None, 2:1, 3:2, 4:1} entonces en un árbol abarcador mínimo tenemos que:
            1 es una raíz (no tiene padre)
            1 es padre de 2 y de 4
            2 es padre de 3
    """
    if not G.nodes:
        return {}

    # Seleccionar un nodo para iniciar
    origen = next(iter(G.nodes))
    

    key = {v: INFTY for v in G.nodes}
    padre = {v: None for v in G.nodes}
    en_AAM = {v: False for v in G.nodes} 


    key[origen] = 0.0
    cola_prioridad = [(0.0, origen)]
    
    # Creamos un diccionario final con los padres del AAM
    AAM_padre = {v: None for v in G.nodes}
    
    # Se ejecuta el bucle mientras hayan nodos que se puedan alcanzar fuera del AAM
    # Por lo tanto, mientras N no es vacio
    while cola_prioridad:
        coste_u, u = heapq.heappop(cola_prioridad)
        
        # Ignoramos las entradas obsoletas
        if en_AAM[u]:
            continue
        
        # Marcamos a u como parte del AAM
        # Lo añadimos a P
        en_AAM[u] = True
        
        # Si tiene padre no puede ser el origen, por lo tanto hay que añadir una conexion al resultado final.
        if padre[u] is not None:
            AAM_padre[u] = padre[u]
        
        # Iteramos sobre los vecinos de u, por lo tanto v
        for v in G.neighbors(u):
            # Si v no esta en el AAM
            if not en_AAM[v]:
                peso_uv = peso(G, u, v)
                
                # En este paso comprobamos si (u, v) es la arista de menos peso para conectar v al AAM
                if peso_uv < key[v]:
                    key[v] = peso_uv
                    padre[v] = u # Ponemos u como el nuevo padre de v
                    # Luego lo añadimos a la cola de prioridad
                    heapq.heappush(cola_prioridad, (peso_uv, v))
                    
    # Devolvemos el arbol de AAM
    return AAM_padre


class UnionFind:
    def __init__(self, vertices):
        self.padre = {v: v for v in vertices}
        self.rango = {v: 0 for v in vertices}

    def find(self, i):
        if self.padre[i] == i:
            return i
        self.padre[i] = self.find(self.padre[i])
        return self.padre[i]

    def union(self, i, j):
        raiz_i = self.find(i)
        raiz_j = self.find(j)
        
        if raiz_i != raiz_j:
            if self.rango[raiz_i] < self.rango[raiz_j]:
                self.padre[raiz_i] = raiz_j
            elif self.rango[raiz_i] > self.rango[raiz_j]:
                self.padre[raiz_j] = raiz_i
            else:
                self.padre[raiz_j] = raiz_i
                self.rango[raiz_i] += 1
            return True # Se realizó la unión
        return False # No se realizó la unión (ya estaban en el mismo conjunto)
                

def kruskal(G:nx.Graph, peso:Callable[[nx.Graph,object,object],float])-> List[Tuple[object,object]]:
    """ Calcula un Árbol Abarcador Mínimo para el grafo
    usando el algoritmo de Kruskal.
    
    Args:
        G (nx.Graph): grafo
        peso (función): función que recibe un grafo y dos vértices del grafo y devuelve el peso de la arista que los conecta
    Returns:
        List[Tuple[object,object]]: Devuelve una lista [(s1,t1),(s2,t2),...,(sn,tn)]
            de los pares de vértices del grafo que forman las aristas
            del arbol abarcador mínimo.
    Raises: None
    Example:
        En el ejemplo anterior en que prim(G,peso)={1:None, 2:1, 3:2, 4:1} podríamos tener, por ejemplo,
        kruskal(G,peso)=[(1,2),(1,4),(3,2)]
    """
    AAM_aristas = []
    
    # Primer paso
    # Creamos la estructura UnionFind
    uf = UnionFind(G.nodes)
    
    # Segundo paso
    # Construimos una lista con todas las aristas que incluya su peso tambien 
    aristas = []
    for u, v in G.edges:
        peso_uv = peso(G, u, v)
        # Lo almacenamos como (peso, u, v)
        aristas.append((peso_uv, u, v))
        
    # Tercer paso
    # Al tener las aristas con los pesos, podemos ordenarlas de forma ascendente
    aristas.sort()
    
    # Guardamos el numero de vértices necesario para la condición de parada
    num_vertices = len(G.nodes)
    
    # Iteramos sobre las aristas ordenadas
    for peso_uv, u, v in aristas:
        # Verificamos aqui si (u, v) crea un ciclo usando UnionFind
        if uf.find(u) != uf.find(v):
            # Si no existe el ciclo, lo añadimos al AAM
            AAM_aristas.append((u, v))
            # Unimos los conjuntos 
            uf.union(u, v)
            
            # condicion de parada
            if len(AAM_aristas) == num_vertices - 1:
                break
                
    return AAM_aristas