import networkx as nx

# Función para agregar un nodo al grafo con el nombre especificado
def agregar_nodo_con_nombre(grafo, nombre):
  grafo.add_node(nombre)

# Función para agregar una arista bidireccional al grafo
def agregar_arista_bidireccional(grafo, nodo_origen, nodo_destino):
  grafo.add_edge(nodo_origen, nodo_destino)
  grafo.add_edge(nodo_destino, nodo_origen)

# Función para agregar una arista unidireccional al grafo
def agregar_arista_unidireccional(grafo, nodo_origen, nodo_destino):
  grafo.add_edge(nodo_origen, nodo_destino)


def crear_grafo(modelJ):
  dictModel = modelJ['submodels']
  G = nx.DiGraph()

  for documents in dictModel:
    models = documents['documents']
    realations = documents['relations']
    docs = {}

    for model in models:
      name_doc = model['name']
      id_doc = model['id']
      agregar_nodo_con_nombre(G, name_doc)
      docs[id_doc] = name_doc

      # crear nodos de documentos internos
      nest_doc = model['nested_docs']
      for subdocs in nest_doc:
        name_subdocs = subdocs['name']
        agregar_nodo_con_nombre(G, name_subdocs)
        agregar_arista_unidireccional(G, name_subdocs, name_doc)

    # crear relaciones entre documentos
    for key, value in realations.items():
      agregar_arista_bidireccional(G, docs[key], docs[value]) 

  return G
 