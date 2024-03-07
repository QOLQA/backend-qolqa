import networkx as nx

# Función para agregar un nodo al grafo con el nombre especificado
def agregar_nodo_con_nombre(graph, id, name,  atributs={}):
  graph.add_node(id, nombre=name, **atributs)

# Función para agregar una arista bidireccional al grafo
def agregar_arista_bidireccional(graph, nodo_origen, nodo_destino, cardinalidad=''):
  graph.add_edge(nodo_origen, nodo_destino, cardinalidad=cardinalidad)
  graph.add_edge(nodo_destino, nodo_origen, cardinalidad=cardinalidad)

# Función para agregar una arista unidireccional al grafo
def agregar_arista_unidireccional(graph, nodo_origen, nodo_destino, cardinalidad=''):
  graph.add_edge(nodo_origen, nodo_destino, cardinalidad=cardinalidad)


def procesar_nestDoc(G, nest_doc, id_doc):
  for subdocs in nest_doc:
    name_subdocs = subdocs['name']
    id_subdocs = subdocs['id']
    cardinality = subdocs['cardinality']
    agregar_nodo_con_nombre(G, id_subdocs, name_subdocs)
    agregar_arista_unidireccional(G, id_subdocs, id_doc, cardinality)

    if len(subdocs['nested_docs']) > 0:
      procesar_nestDoc(G, subdocs['nested_docs'], id_subdocs)


def crear_grafo(dictModelT):
  dictModel = dictModelT["submodels"]
  G = nx.DiGraph()

  for documents in dictModel:
    models = documents['collections']
    realations = documents['relations']

    for model in models:
      name_doc = model['name']
      id_doc = model['id']
      atributs = model['fields']
      agregar_nodo_con_nombre(G, id_doc,name_doc, atributs)

      # crear nodos de documentos internos
      nest_doc = model['nested_docs']
      procesar_nestDoc(G, nest_doc, id_doc)

  # crear relaciones entre documentos
  for relation in realations:
    agregar_arista_bidireccional(G, relation['id_source'], relation['id_target'], relation['cardinality'])


  return G
 