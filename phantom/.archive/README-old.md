# 🧪 GenAI Credit Validation Framework

> *"The constraint is not the cage, but the canvas"* — adaptado de Marcus Aurelius

## 🎯 O Problema Original

Você tem **R$ 10k em créditos GCP** que estão parados há meses:
- **R$ 6.432,54**: Trial credit for GenAI App Builder
- **R$ 3.646,57**: Dialogflow CX Trial

Tentativas anteriores falhavam com **404 errors** porque:

### ❌ O Código Original (ERRADO)
```python
# Isso NÃO consome os créditos corretos
client = discoveryengine.GroundedGenerationServiceClient()
```

**Por quê não funciona?**

1. **API diferente**: `GroundedGenerationServiceClient` é a **Grounding API**
   - Usa Google Search como fonte
   - Cobra $35/1k requests (bem mais caro)
   - **NÃO** é coberto pelos créditos "GenAI App Builder"

2. **Falta de Data Store**: Grounding API não precisa, mas Vertex AI Search **PRECISA**

3. **Endpoint confusion**: Regional vs Global vs API-specific

---

## ✅ A Solução (CERTO)

### API Correta: `SearchServiceClient`
```python
# Isso SIM consome os créditos certos
client = discoveryengine.SearchServiceClient()
```

**Diferenças críticas:**

| Feature | Grounding API ❌ | Vertex AI Search ✅ |
|---------|------------------|---------------------|
| **Cliente** | `GroundedGenerationServiceClient` | `SearchServiceClient` |
| **Requer Data Store** | Não | **SIM** (mandatório) |
| **Fonte de dados** | Google Search | Seus documentos |
| **Pricing** | $35/1k queries | $4/1k queries (Enterprise) |
| **Crédito aceito** | Grounded Generation credits | **GenAI App Builder** ✅ |

---

## 🚀 Workflow de Validação

### 1️⃣ Setup Inicial
```bash
# Clone/entre no diretório
nix develop

# Autentique (popup do browser)
gcloud auth application-default login

# Habilite APIs necessárias
gcloud services enable discoveryengine.googleapis.com
gcloud services enable dialogflow.googleapis.com
```

### 2️⃣ Valide Autenticação & Billing
```bash
python validate_credits.py
```

**O que faz:**
- ✅ Verifica `gcloud auth`
- 💰 Lista billing accounts
- 🔌 Mostra APIs a habilitar

**Output esperado:**
```
✅ Autenticado no projeto: gen-lang-client-0530325234
📊 Billing Accounts encontradas:
  - My Billing Account
    ID: billingAccounts/01XXXX-XXXX-XXXX
    Open: True
```

### 3️⃣ Crie/Liste Data Stores
```bash
python manage_datastores.py
```

**O que faz:**
- 📚 Lista data stores existentes
- 🔨 Oferece criar um de teste
- 📝 Retorna o `DATA_STORE_ID` para usar

**Output esperado:**
```
📦 Data Stores existentes:
  (Nenhum data store encontrado)

💡 Nenhum data store encontrado. Deseja criar um de teste? (y/n)
>>> y

🔨 Criando data store 'test-search-datastore'...
  ⏳ Aguardando criação...
  ✅ Data Store criado: test-search-datastore

📝 Salve este ID:
   export DATA_STORE_ID='test-search-datastore'
```

### 4️⃣ Teste Consumo de Créditos
```bash
# Exporte o ID do passo anterior
export DATA_STORE_ID='test-search-datastore'

# Execute query real
python test_credits.py
```

**O que faz:**
- 🔍 Faz query real no Vertex AI Search
- 💸 **CONSOME OS CRÉDITOS DE VERDADE**
- 📊 Mostra resultados + summary generativa
- 💰 Calcula créditos restantes

**Output esperado (data store vazio):**
```
🔍 EXECUTANDO QUERY REAL (CONSUMINDO CRÉDITOS)
📦 Data Store: test-search-datastore
❓ Query: What is Retrieval Augmented Generation?

⏳ Enviando request...

📋 RESULTADOS
🔎 RESULTADOS DE BUSCA:
  (Nenhum resultado encontrado)

💡 DICA: Seu data store pode estar vazio!
   Adicione documentos em: https://console.cloud.google.com/gen-app-builder

✅ QUERY EXECUTADA COM SUCESSO!

💰 CRÉDITO CONSUMIDO:
   • Search Enterprise Edition: $4.00 / 1,000 queries
   • Esta query: ~$0.004
   • Créditos restantes: ~R$ 6432.54
```

---

## 📚 Populando o Data Store

Para obter resultados reais, adicione documentos:

### Opção A: Via Console (mais fácil)
1. Acesse: https://console.cloud.google.com/gen-app-builder
2. Selecione seu data store
3. `Import` → escolha fonte:
   - **Websites**: URL pra crawl
   - **Cloud Storage**: bucket com PDFs/docs
   - **BigQuery**: tabela com dados estruturados

### Opção B: Via API (programático)
```python
from google.cloud import discoveryengine_v1beta as discoveryengine

# TODO: Script de import automático
# Pode adicionar PDFs, URLs, ou structured data
```

---

## 🐛 Troubleshooting

### Erro: `403 Permission Denied`
```
🔧 FIX:
gcloud projects add-iam-policy-binding gen-lang-client-0530325234 \
  --member="user:seu-email@gmail.com" \
  --role="roles/discoveryengine.admin"
```

### Erro: `404 Not Found`
**Causas comuns:**
1. Data Store não existe → rode `manage_datastores.py`
2. Location errada → verifique se é `global` ou `us-central1`
3. Collection path incorreto → deve ser `default_collection`

### Erro: API não habilitada
```bash
gcloud services enable discoveryengine.googleapis.com --project=gen-lang-client-0530325234
```

### Query retorna vazio
- ✅ Normal se data store tá vazio
- Adicione docs via console ou API
- Aguarde ~30min pra indexação completar

---

## 💰 Pricing Breakdown

### Seus Créditos:
| Crédito | Valor | Válido até | Uso |
|---------|-------|------------|-----|
| GenAI App Builder | R$ 6.432,54 | 2026-05-21 | Vertex AI Search |
| Dialogflow CX | R$ 3.646,57 | 2026-11-30 | Chat agents |

### Consumo Vertex AI Search:
```
Search Enterprise Edition: $4.00 / 1,000 queries
├─ Com R$ 6.432,54 ≈ 1,608 queries (sem contar indexing)
├─ Indexing: $5.00 / GB / mês (10GB free)
└─ Advanced Generative Answers: +$4.00 / 1k queries (opcional)
```

### Estimativa de uso intensivo:
- **50 queries/dia** → 1,500/mês → $6/mês → **~12 meses** de uso
- **Indexing 50GB** → $200/mês one-time → sobra pra queries

---

## 🎨 Próximos Passos (After Validation)

Uma vez que você validou que **tá consumindo créditos corretamente**:

1. **Popular com dados úteis**:
   ```
   - Security docs (OWASP, NIST)
   - Job descriptions
   - Seus projetos (GitHub)
   ```

2. **Criar MCP Server**:
   ```typescript
   interface VertexSearchMCP {
     searchSecurity(query: string): Promise<Results>
     searchJobs(query: string): Promise<Jobs>
   }
   ```

3. **Integrar com Claude Desktop**:
   ```
   - RAG sobre seu conhecimento
   - Job matching automático
   - Security knowledge on-demand
   ```

4. **Build portfolio piece**:
   ```
   "Built enterprise RAG system using Vertex AI Search,
    consumed R$10k in GCP credits productively,
    integrated with MCP protocol"
   ```

---

## 📖 References

- [Vertex AI Search Docs](https://cloud.google.com/generative-ai-app-builder/docs)
- [Pricing](https://cloud.google.com/generative-ai-app-builder/pricing)
- [Python SDK](https://cloud.google.com/python/docs/reference/discoveryengine/latest)

---

## 🧘 Philosophical Note

Este processo de debug é um microcosmo do desenvolvimento:

1. **Constraint reveals truth**: O erro 404 era um professor
2. **API is contract**: Ler documentação ≠ entender pricing
3. **Credits are incentive**: Google te deu uma faca específica
4. **Creative use is skill**: Transformar trial em portfolio

Como diria o Tao Te Ching:
> *"The clay is molded to make a vessel,*  
> *but the utility of the vessel lies in the space where there is nothing."*

Os créditos são a argila. O RAG system é o vaso. Mas o valor está no **vazio** — o conhecimento que você vai indexar e query.

🏹 射

---

**Made with 🔥 in Feira de Santana, debugged with philosophy in mind**
