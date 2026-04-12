import fitz  # PyMuPDF
import spacy
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt

# --- CONFIGURAÇÕES ---
ARQUIVO_PDF = "tcc_final.pdf"
MODELO_SPACY = "pt_core_news_lg"
TERMOS_LIXO = ['Figura', 'Tabela', 'Capítulo', 'Pdf', 'Http', 'Https', 'E-Mail', 'Referência', 'Anexo', 'Equação', 'Art.']
LABELS_INTERESSANTES = ["PER", "ORG", "LOC", "GPE", "MISC"]


# --- 1. EXTRAÇÃO DE TEXTO ---
def extrair_texto_pdf(caminho_pdf):
    doc_pdf = fitz.open(caminho_pdf)
    return "".join([pagina.get_text() for pagina in doc_pdf])

print("Lendo PDF...")
texto_tcc = extrair_texto_pdf(ARQUIVO_PDF)

# --- 2. PROCESSAMENTO NATURAL DE LINGUAGEM ---
print("Carregando NLP e processando entidades...")
nlp = spacy.load(MODELO_SPACY)
doc = nlp(texto_tcc)

# --- 3. CONSTRUÇÃO DO GRAFO E COLETA DE DADOS ---
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
            
            ents_validas.append(texto_normalizado)
            
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
                u, v = ents_unicas[i], ents_unicas[j]
                if G.has_edge(u, v):
                    G[u][v]['weight'] += 1
                else:
                    G.add_edge(u, v, weight=1)

# --- 4. TRATAMENTO DA BASE DE DADOS (PANDAS) ---
print("Gerando CSV de métricas...")
df_bruto = pd.DataFrame(entidades_para_df)
df_limpo = df_bruto.groupby(['Texto', 'Label']).size().reset_index(name='Frequencia')
df_limpo = df_limpo.sort_values(by='Frequencia', ascending=False)

# Adicionando uma métrica de relevância simples
total_ents = df_limpo['Frequencia'].sum()
df_limpo['Relevancia_%'] = (df_limpo['Frequencia'] / total_ents * 100).round(2)

# Salvar CSV final
df_limpo.to_csv("entidades_tcc_final.csv", index=False, encoding='utf-8-sig')

# --- 5. EXPORTAÇÃO E VISUALIZAÇÃO ---
# Salvar grafo para abrir no Gephi (Recomendado para o TCC)
nx.write_graphml(G, "grafo_final.graphml")

print(f"\n--- RELATÓRIO FINAL ---")
print(f"Total de entidades únicas: {len(df_limpo)}")
print(f"Total de conexões criadas: {G.number_of_edges()}")
print(f"Arquivos gerados: 'entidades_tcc_final.csv' e 'grafo_final.graphml'")

# Visualização rápida (apenas das conexões fortes)
plt.figure(figsize=(12, 12))
# Filtramos apenas arestas com peso > 1 para diminuir o "ruído" visual no gráfico
subgrafo = nx.Graph([(u, v, d) for u, v, d in G.edges(data=True) if d['weight'] > 1])
pos = nx.spring_layout(subgrafo, k=0.3)
nx.draw(subgrafo, pos, with_labels=True, node_size=1000, node_color="lightsalmon", font_size=8)
plt.show()