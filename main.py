import streamlit as st
import fitz
import spacy
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import community.community_louvain as community_louvain
import tempfile
import os
import re  

# CONFIGURAÇÕES
MODELO_SPACY = "pt_core_news_lg"

TERMOS_LIXO = [
    'Capítulo', 'Pdf', 'Http', 'Https', 'E-Mail', 'Referência', 'Anexo', 
    'Equação', 'Art.', 'Tabela', 'Fig.', 'Figura', 'Abstract', 'Resumo',
    'Introdução', 'Metodologia', 'Conclusão', 'Resultados', 'Mape', 'Rmse', 
    'Mae', 'Rsq', 'Value', 'Valor', 'Et', 'Al', 'Https', 'Doi'
]
LABELS_INTERESSANTES = ["PER", "ORG", "LOC", "GPE", "MISC"]

# ── FUNÇÕES ──────────────────────────────────────────────────

def analisar_ego_network(G, entidade):
    if entidade not in G:
        return None, []
    ego = nx.ego_graph(G, entidade, radius=1)
    vizinhos = [(v, G[entidade][v]['weight']) for v in G.neighbors(entidade)]
    return ego, vizinhos

def top_entidades_por_grau(G, top_n=10):
    graus = dict(G.degree(weight='weight'))
    return sorted(graus.items(), key=lambda x: x[1], reverse=True)[:top_n]

def contar_caminhos_n_passos(G, origem, destino, n=2):
    if origem not in G or destino not in G:
        return 0
    adj_matrix = nx.to_numpy_array(G, weight=None)
    nos = list(G.nodes())
    idx_origem = nos.index(origem)
    idx_destino = nos.index(destino)
    matriz_n = np.linalg.matrix_power(adj_matrix, n)
    return int(matriz_n[idx_origem, idx_destino])

def menor_caminho_medio(G):
    if not nx.is_connected(G):
        G = G.subgraph(max(nx.connected_components(G), key=len))
    return nx.average_shortest_path_length(G, weight='weight')

def detectar_clusters_tematicos(G):
    G_u = G.to_undirected() if G.is_directed() else G
    clusters = community_louvain.best_partition(G_u, weight='weight')
    grupos = {}
    for no, cid in clusters.items():
        grupos.setdefault(cid, []).append(no)
    return clusters, grupos

def extrair_texto_pdf(caminho_pdf):
    doc_pdf = fitz.open(caminho_pdf)
    return "".join([p.get_text() for p in doc_pdf])

def extrair_paragrafos_pdf(caminho_pdf):
    paragrafos = []
    for pagina in fitz.open(caminho_pdf):
        for bloco in pagina.get_text("blocks"):
            texto = bloco[4].strip()
            if texto:
                paragrafos.append(texto)
    return paragrafos


def limpar_texto(texto):
    texto = texto.replace('\n', ' ').replace('\t', ' ')
    texto = re.sub(r'\s+', ' ', texto) 
    texto = re.sub(r'[:;,.]$', '', texto) 
    return texto.strip().title()

def construir_grafo(unidades):
    G = nx.Graph()
    entidades_para_df = []
    for unidade in unidades:
        ents_validas = []
        for ent in unidade.ents:
            texto_normalizado = limpar_texto(ent.text)
            
            if (ent.label_ in LABELS_INTERESSANTES and
                    texto_normalizado not in TERMOS_LIXO and
                    len(texto_normalizado) > 2):
                ents_validas.append((texto_normalizado, ent.label_))
                entidades_para_df.append({"Texto": texto_normalizado, "Label": ent.label_})
        
        ents_unicas = list(set(ents_validas))
        if len(ents_unicas) > 1:
            for i in range(len(ents_unicas)):
                for j in range(i + 1, len(ents_unicas)):
                    (u, tipo_u) = ents_unicas[i]
                    (v, tipo_v) = ents_unicas[j]
                    G.add_node(u, tipo=tipo_u)
                    G.add_node(v, tipo=tipo_v)
                    if G.has_edge(u, v):
                        G[u][v]['weight'] += 1
                    else:
                        G.add_edge(u, v, weight=1)
    return G, entidades_para_df

def montar_df(entidades_para_df):
    df = pd.DataFrame(entidades_para_df)
    df = df.groupby(['Texto', 'Label']).size().reset_index(name='Frequencia')
    df = df.sort_values(by='Frequencia', ascending=False)
    df['Relevancia_%'] = (df['Frequencia'] / df['Frequencia'].sum() * 100).round(2)
    return df

def plotar_grafo(G, titulo, cor):
    fig, ax = plt.subplots(figsize=(12, 12))
    subgrafo = nx.Graph([(u, v, d) for u, v, d in G.edges(data=True) if d['weight'] > 1])
    pos = nx.spring_layout(subgrafo, k=0.3)
    nx.draw(subgrafo, pos, with_labels=True, node_size=1000,
            node_color=cor, font_size=8, ax=ax)
    ax.set_title(titulo)
    return fig

# ── INTERFACE ────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Análise de Entidades TCC", layout="wide")
st.title("📊 Análise de Entidades — TCC")

arquivo = st.file_uploader("Envie o PDF do TCC", type="pdf")
entidade_ego = st.text_input("Entidade para Ego Network", value="Xgboost")
origem_caminho = st.text_input("Origem (caminhos)", value="Xgboost")
destino_caminho = st.text_input("Destino (caminhos)", value="Random Forest")

if arquivo and st.button("▶ Analisar"):

    # Salva PDF temporariamente
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(arquivo.read())
        caminho_pdf = tmp.name

    with st.spinner("Lendo PDF..."):
        texto_tcc = extrair_texto_pdf(caminho_pdf)
        paragrafos_texto = extrair_paragrafos_pdf(caminho_pdf)

    with st.spinner("Carregando modelo NLP..."):
        nlp = spacy.load(MODELO_SPACY)

    with st.spinner("Processando por frase..."):
        doc = nlp(texto_tcc)
        G, ents_df = construir_grafo(doc.sents)
        df_frase = montar_df(ents_df)
        nx.write_graphml(G, "grafo_final.graphml")

    with st.spinner("Processando por parágrafo..."):
        docs_par = list(nlp.pipe(paragrafos_texto))
        G_par, ents_df_par = construir_grafo(docs_par)
        df_par = montar_df(ents_df_par)
        nx.write_graphml(G_par, "grafo_final_paragrafo.graphml")

    os.unlink(caminho_pdf)

    # ── RESULTADOS ────────────────────────────────────────────────────────────
    tab1, tab2 = st.tabs(["📄 Por Frase", "📃 Por Parágrafo"])

    for tab, grafo, df, cor, label in [
        (tab1, G,     df_frase, "lightsalmon", "Frase"),
        (tab2, G_par, df_par,   "lightblue",   "Parágrafo"),
    ]:
        with tab:
            col1, col2 = st.columns(2)
            col1.metric("Entidades únicas", len(df))
            col2.metric("Conexões", grafo.number_of_edges())

            st.subheader("Top entidades por grau")
            top = top_entidades_por_grau(grafo)
            st.dataframe(pd.DataFrame(top, columns=["Entidade", "Grau"]))

            st.subheader("Frequência de entidades")
            st.dataframe(df)

            st.subheader(f"Grafo de co-ocorrência — {label}")
            st.pyplot(plotar_grafo(grafo, f"Co-ocorrência por {label}", cor))

            st.subheader(f"Ego Network — {entidade_ego}")
            ego, vizinhos = analisar_ego_network(grafo, entidade_ego)
            if ego:
                st.write(f"Nós: {ego.number_of_nodes()} | Arestas: {ego.number_of_edges()}")
                st.dataframe(pd.DataFrame(vizinhos, columns=["Vizinho", "Peso"]))
            else:
                st.warning(f"'{entidade_ego}' não encontrada no grafo.")

            st.subheader("Caminhos de N passos")
            qtd = contar_caminhos_n_passos(grafo, origem_caminho, destino_caminho, 2)
            st.write(f"Caminhos de tamanho 2 entre **{origem_caminho}** e **{destino_caminho}**: **{qtd}**")

            st.subheader("Caminho médio")
            try:
                cm = menor_caminho_medio(grafo)
                st.write(f"{cm:.4f}")
            except Exception as e:
                st.warning(str(e))

            st.subheader("Clusters temáticos")
            _, grupos = detectar_clusters_tematicos(grafo)
            for cid, termos in grupos.items():
                st.write(f"**Cluster {cid}:** {', '.join(termos[:10])}")

            st.subheader("Downloads")
            st.download_button("⬇ CSV", df.to_csv(index=False, encoding='utf-8-sig'),
                               f"entidades_{label.lower()}.csv", "text/csv")
            with open(f"grafo_final{'_paragrafo' if label == 'Parágrafo' else ''}.graphml", "rb") as f:
                st.download_button("⬇ GraphML", f, f"grafo_{label.lower()}.graphml")