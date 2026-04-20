# 📊 Análise de Entidades — TCC

Ferramenta para análise de entidades nomeadas (NER) em documentos PDF acadêmicos, com construção de grafos de co-ocorrência por frase e por parágrafo. Possui interface gráfica via Streamlit e exportação para o Gephi.

### Alunos:
- Alan César Rebouças de Araújo Carvalho
- Erick Henrique da Silva Paz
- Matheus Silva Mendes 
---
## 🚀 Instalação

### 📦 Dependências

| Biblioteca | Uso |
|---|---|
| `streamlit` | Interface gráfica |
| `pymupdf (fitz)` | Leitura do PDF |
| `spacy` | NER — reconhecimento de entidades |
| `networkx` | Construção e análise dos grafos |
| `pandas` | Manipulação dos dados |
| `matplotlib` | Visualização dos grafos |
| `numpy` | Cálculo matricial para caminhos |
| `python-louvain` | Detecção de clusters temáticos |


### 1. Clone o repositório

```bash
git clone https://github.com/Alan-CRA/trabalho1_AED2.git
cd trabalho1_AED2
```

### 2. Instale as dependências Python

```bash
pip install -r requirements.txt
```

### 3. Instale o modelo de linguagem em português

```bash
python -m spacy download pt_core_news_lg
```
### 3.1 Caso o comando anterior não der certo por qualquer motivo, tente:
```bash
pip install https://github.com/explosion/spacy-models/releases/download/pt_core_news_sm-3.7.0/pt_core_news_sm-3.7.0-py3-none-any.whl
```
---

## ▶️ Como usar

### Interface gráfica (recomendado)

```bash
streamlit run main.py
```

Abre automaticamente no navegador em `http://localhost:8501`.

### Linha de comando (sem interface)

```bash
python main.py
```

> ⚠️ Neste modo, o PDF deve se chamar `tcc_final.pdf` e estar na mesma pasta que o script.

---

## 🖥️ Interface

Após abrir no navegador:

1. **Envie o PDF** do TCC pelo campo de upload
2. **Configure as entidades** nos campos de texto:
   - Entidade para Ego Network
   - Origem e Destino para análise de caminhos
3. **Clique em "▶ Analisar"** e aguarde o processamento
4. **Explore os resultados** nas abas **Por Frase** e **Por Parágrafo**
5. **Baixe os arquivos** pelos botões de download

---

## 📈 O que é analisado

| Análise | Descrição |
|---|---|
| **Top entidades por grau** | As 10 entidades mais conectadas no grafo |
| **Frequência de entidades** | Todas as entidades com frequência e relevância em % |
| **Grafo de co-ocorrência** | Visualização das conexões entre entidades |
| **Ego Network** | Vizinhos diretos de uma entidade específica |
| **Caminhos de N passos** | Quantidade de caminhos de tamanho 2 entre duas entidades |
| **Caminho médio** | Distância média entre todos os pares de nós |
| **Clusters temáticos** | Grupos de entidades detectados pelo algoritmo de Louvain |

Todas as análises são feitas duas vezes: uma com **co-ocorrência por frase** e outra com **co-ocorrência por parágrafo**.

---

## Resultados obtidos

É possível ver os resultados na página gerada pelo streamlit
### Resultados por frase
![](images/top%20entidades%20frase.png)
![](images/frequencia%20entidades%20frase.png)
![](images/clusters%20frase.png)
![](images/grafo%20por%20frase.svg)
![](images/grafo%20xgboost%20por%20frase.svg)

### Resultados por paragrafo
![](images/top%20entidades%20paragrafo.png)
![](images/frequencia%20entidades%20paragrafo.png)
![](images/clusters%20paragrafo.png)
![](images/grafo%20por%20paragrafo.svg)
![](images/grafo%20xgboost%20por%20paragrafo.svg)

## Analises feitas




## 📁 Arquivos gerados

| Arquivo | Descrição |
|---|---|
| `entidades_frase.csv` | Entidades, labels, frequência e relevância (por frase) |
| `entidades_paragrafo.csv` | Entidades, labels, frequência e relevância (por parágrafo) |
| `grafo_final.graphml` | Grafo por frase — abre no Gephi |
| `grafo_final_paragrafo.graphml` | Grafo por parágrafo — abre no Gephi |
| `grafo_com_foco.graphml` | Ego network da entidade selecionada |

---

## 🔬 Abrindo no Gephi

1. Baixe o arquivo `.graphml` pela interface
2. Abra o Gephi
3. **File → Open** → selecione o arquivo `.graphml`
4. O grafo será carregado com os pesos das arestas e os tipos das entidades como atributos

---

## ⚙️ Configurações

No topo do arquivo `main.py`:

```python
MODELO_SPACY = "pt_core_news_lg"   # Modelo de linguagem

LABELS_INTERESSANTES = ["PER", "ORG", "LOC", "GPE", "MISC"]  # Tipos de entidade

TERMOS_LIXO = ['Capítulo', 'Pdf', 'Http', ...]  # Termos a ignorar
```

---

