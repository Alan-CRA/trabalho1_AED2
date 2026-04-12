import fitz  # PyMuPDF
import spacy
import networkx as nx
import matplotlib.pyplot as plt


def extrair_texto_pdf(caminho_pdf):
    documento = fitz.open(caminho_pdf)
    texto_completo = ""
    
    for pagina in documento:
        texto_completo += pagina.get_text()
    
    return texto_completo

# Uso
texto_tcc = extrair_texto_pdf("tcc_final.pdf")

# Carrega o modelo de português
# Certifica-te de ter corrido: python -m spacy download pt_core_news_lg
nlp = spacy.load("pt_core_news_lg")


# O texto_tcc veio da tua função com PyMuPDF
doc = nlp(texto_tcc)

# Criar uma lista para armazenar as entidades encontradas
entidades = []

for ent in doc.ents:
    # No teu caso, PER (Pessoas) e ORG (Organizações) são as mais ricas para grafos
    #if ent.label_ in ["PER", "ORG", "LOC"]:
    entidades.append((ent.text, ent.label_))

# Remover duplicados para ver o que foi encontrado
#print(set(entidades))


G = nx.Graph()

# Exemplo simplificado por sentenças


for sent in doc.sents:
    # Extrai entidades daquela sentença específica
    ents_na_sentenca = [ent.text for ent in sent.ents]
    
    # Se houver mais de uma entidade, elas estão relacionadas (co-ocorrência)
    if len(ents_na_sentenca) > 1:
        for i in range(len(ents_na_sentenca)):
            for j in range(i + 1, len(ents_na_sentenca)):
                # Adiciona ou aumenta o peso da ligação
                u, v = ents_na_sentenca[i], ents_na_sentenca[j]
                if G.has_edge(u, v):
                    G[u][v]['weight'] += 1
                else:
                    G.add_edge(u, v, weight=1)

nx.write_graphml(G, "meu_grafo_tcc.graphml")

# Configura o tamanho da imagem
plt.figure(figsize=(12, 12))

# Define o layout (o modo como os nós se espalham)
pos = nx.spring_layout(G, k=0.5) 

# Desenha o grafo
nx.draw(G, pos, with_labels=True, 
        node_color='skyblue', 
        node_size=2000, 
        edge_color='gray', 
        font_size=10, 
        width=[G[u][v]['weight'] for u, v in G.edges()])

plt.show()
