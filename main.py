import fitz  # PyMuPDF
import spacy
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
import pandas as pd
import community.community_louvain as community_louvain
# CONFIGURAÇÕES
ARQUIVO_PDF = "tcc_final.pdf"
MODELO_SPACY = "pt_core_news_lg"
TERMOS_LIXO = ['Figura', 'Tabela', 'Capítulo', 'Pdf', 'Http', 'Https', 'E-Mail', 'Referência', 'Anexo', 'Equação', 'Art.']
LABELS_INTERESSANTES = ["PER", "ORG", "LOC", "GPE", "MISC"]
def analisar_ego_network(G, entidade, mostrar=True):
    """
    Gera e analisa a ego network de uma entidade.
    
    Parâmetros:
    - G: grafo NetworkX
    - entidade: nó central (string)
    - mostrar: se True, imprime informações
    
    Retorno:
    - subgrafo ego
    """
    
    import networkx as nx
    
    # Verifica se a entidade existe no grafo
    if entidade not in G:
        print(f"A entidade '{entidade}' não está no grafo.")
        return None
    
    # Cria ego network (raio 1 = vizinhos diretos)
    ego = nx.ego_graph(G, entidade, radius=1)
    
    if mostrar:
        print(f"\n--- Ego Network de '{entidade}' ---")
        print(f"Número de nós: {ego.number_of_nodes()}")
        print(f"Número de arestas: {ego.number_of_edges()}")
        
        print("\nVizinhos diretos:")
        for vizinho in G.neighbors(entidade):
            peso = G[entidade][vizinho]['weight']
            print(f"{vizinho} (peso: {peso})")

        nx.write_graphml(ego, "grafo_com_foco.graphml")
    
    return ego

def top_entidades_por_grau(G, top_n=10, mostrar=True):
    
    #Retorna as entidades mais importantes com base no grau ponderado.
    
    # Grau ponderado
    graus = dict(G.degree(weight='weight'))
    
    # Lista de (entidade, grau)
    lista_graus = list(graus.items())
    
    # Ordena do maior para o menor
    lista_ordenada = sorted(lista_graus, key=lambda item: item[1], reverse=True)
    
    # Seleciona top N
    top_grau = lista_ordenada[:top_n]
    
    if mostrar:
        print(f"\nTop {top_n} entidades por grau ponderado:")
        for ent, grau in top_grau:
            print(f"{ent}: {grau}")
    
    return top_grau

def contar_caminhos_n_passos(G, origem, destino, n=2):

    # 1. Verificar se os nós existem no grafo
    if origem not in G or destino not in G:
        print(f"Erro: Um dos nós ('{origem}' ou '{destino}') não foi encontrado.")
        return 0

    # 2. Obter a matriz de adjacência e a lista de nós (para indexação)
    # Usamos weight=None para contar apenas a existência de caminhos. 
    # Se quiser considerar a frequência do NER, use weight='weight'.
    adj_matrix = nx.to_numpy_array(G, weight=None)
    nos = list(G.nodes())
    
    # 3. Mapear os nomes para os índices numéricos do array NumPy
    idx_origem = nos.index(origem)
    idx_destino = nos.index(destino)
    
    # 4. Elevar a matriz à potência N
    # Isso calcula todas as combinações de caminhos de comprimento N
    matriz_n = np.linalg.matrix_power(adj_matrix, n)
    
    # 5. Extrair o valor específico
    quantidade = matriz_n[idx_origem, idx_destino]
    
    print(f"--- Análise de Caminhos (N={n}) ---")
    print(f"Origem: {origem}")
    print(f"Destino: {destino}")
    print(f"Quantidade de caminhos encontrados: {int(quantidade)}")
    
    return int(quantidade)

def menor_caminho_medio(G):
    # Verifica se o grafo está conectado
    if not nx.is_connected(G):
        print("Grafo desconectado! Calculando para o maior componente...")
        # Pega o maior subgrafo conectado
        G_componente = G.subgraph(max(nx.connected_components(G), key=len))
    else:
        G_componente = G

    caminho_medio = nx.average_shortest_path_length(G_componente, weight='weight')
    print(f"Caminho médio do maior componente: {caminho_medio}")
    return caminho_medio
    
def detectar_clusters_tematicos(G):
    # O algoritmo de Louvain funciona melhor em grafos não-direcionados
    if G.is_directed():
        G_undirected = G.to_undirected()
    else:
        G_undirected = G

    # 1. Calcula a melhor partição (clusters)
    # O parâmetro weight='weight' garante que a frequência do NER seja levada em conta
    clusters = community_louvain.best_partition(G_undirected, weight='weight')

    # 2. Organiza os resultados para visualização
    grupos = {}
    for no, cluster_id in clusters.items():
        if cluster_id not in grupos:
            grupos[cluster_id] = []
        grupos[cluster_id].append(no)

    print(f"--- Foram detectados {len(grupos)} clusters temáticos ---")

    # 3. Exibe os termos de cada cluster (limitando aos 5 primeiros por grupo)
    for cluster_id, termos in grupos.items():
        print(f"\nCluster {cluster_id} (Principais termos):")
        print(", ".join(termos[:10])) # Mostra até 10 termos para dar contexto

    return clusters # Retorna um dicionário {nó: id_do_cluster}
# EXTRAÇÃO DE TEXTO 
def extrair_texto_pdf(caminho_pdf):
    doc_pdf = fitz.open(caminho_pdf)
    return "".join([pagina.get_text() for pagina in doc_pdf])


print("Lendo PDF...")
texto_tcc = extrair_texto_pdf(ARQUIVO_PDF)

# PROCESSAMENTO NATURAL DE LINGUAGEM
print("Carregando NLP e processando entidades...")
nlp = spacy.load(MODELO_SPACY)
doc = nlp(texto_tcc)

# 3. CONSTRUÇÃO DO GRAFO E COLETA DE DADOS
G = nx.Graph()
entidades_para_df = []

print("Construindo grafo de co-ocorrência...")
for sent in doc.sents:
    # Extrair, normalizar e filtrar entidades da sentença atual
    ents_validas = []
    for ent in sent.ents:
        texto_normalizado = ent.text.strip().title()
        
        # Filtros de qualidade
        if (ent.label_ in LABELS_INTERESSANTES and 
            texto_normalizado not in TERMOS_LIXO and 
            len(texto_normalizado) > 2):
            
            ents_validas.append((texto_normalizado, ent.label_))
            
            # Guardar para o nosso CSV de métricas
            entidades_para_df.append({
                "Texto": texto_normalizado,
                "Label": ent.label_
            })
    
    # Remover duplicatas dentro da mesma sentença (evita self-loops)
    ents_unicas = list(set(ents_validas))
    
    # Criar as relações (Arestas)
    if len(ents_unicas) > 1:
        for i in range(len(ents_unicas)):
            for j in range(i + 1, len(ents_unicas)):
                (u, tipo_u) = ents_unicas[i]
                (v, tipo_v) = ents_unicas[j]

                # Adiciona nós com atributo tipo
                G.add_node(u, tipo=tipo_u)
                G.add_node(v, tipo=tipo_v)

                if G.has_edge(u, v):
                    G[u][v]['weight'] += 1
                else:
                    G.add_edge(u, v, weight=1)

# 4. TRATAMENTO DA BASE DE DADOS (PANDAS) 
print("Gerando CSV de métricas...")
df_bruto = pd.DataFrame(entidades_para_df)
df_limpo = df_bruto.groupby(['Texto', 'Label']).size().reset_index(name='Frequencia')
df_limpo = df_limpo.sort_values(by='Frequencia', ascending=False)

# Adicionando uma métrica de relevância simples
total_ents = df_limpo['Frequencia'].sum()
df_limpo['Relevancia_%'] = (df_limpo['Frequencia'] / total_ents * 100).round(2)

# Salvar CSV final
df_limpo.to_csv("entidades_tcc_final.csv", index=False, encoding='utf-8-sig')

# 5. EXPORTAÇÃO E VISUALIZAÇÃO
# Salvar grafo para abrir no Gephi (Recomendado para o TCC)
nx.write_graphml(G, "grafo_final.graphml")

print(f"\n--- RELATÓRIO FINAL ---")
print(f"Total de entidades únicas: {len(df_limpo)}")
print(f"Total de conexões criadas: {G.number_of_edges()}")
print(f"Arquivos gerados: 'entidades_tcc_final.csv' e 'grafo_final.graphml'")

top_entidades_por_grau(G)
ego = analisar_ego_network(G, "Xgboost")
for node, data in G.nodes(data=True):
    print(node, data)
    break


# Visualização rápida (apenas das conexões fortes)
plt.figure(figsize=(12, 12))
# Filtramos apenas arestas com peso > 1 para diminuir o "ruído" visual no gráfico
subgrafo = nx.Graph([(u, v, d) for u, v, d in G.edges(data=True) if d['weight'] > 1])
pos = nx.spring_layout(subgrafo, k=0.3)
nx.draw(subgrafo, pos, with_labels=True, node_size=1000, node_color="lightsalmon", font_size=8)
plt.show()

print()
contar_caminhos_n_passos(G,"Xgboost","Random Forest",2)
print()
menor_caminho_medio(G)

detectar_clusters_tematicos(G)