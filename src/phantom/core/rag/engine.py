import json
from pathlib import Path
from typing import Any, Dict

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_google_vertexai import VertexAI, VertexAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


class RigorousRAGEngine:
    def __init__(self, persist_directory: str = "./data/vector_db"):
        self.persist_directory = persist_directory
        self.embeddings = VertexAIEmbeddings(model="text-embedding-004")
        self.llm = VertexAI(model="gemini-1.5-flash-001", temperature=0.0)
        self.vector_db = None

    def ingest(self, jsonl_path: str) -> int:
        """
        Ingere artefatos com controle estrito de metadados.
        """
        path = Path(jsonl_path)
        if not path.exists():
            raise FileNotFoundError(f"Artifacts not found: {jsonl_path}")

        # Carregamento Customizado para Preservar Metadados
        documents = []
        with open(path, "r") as f:
            for line in f:
                data = json.loads(line)
                inner = json.loads(data["jsonData"])
                doc = Document(
                    page_content=f"TITLE: {inner['title']}\nCONTENT:\n{inner['content']}",
                    metadata={
                        "source": f"{inner.get('repo', 'unknown')}/{inner.get('title', 'untitled')}",
                        "repo": inner.get("repo", ""),
                        "type": "code_artifact",
                        "context": inner.get("context", "N/A"),
                    },
                )
                documents.append(doc)

        # Splitting Otimizado para Código
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            separators=["\nclass ", "\ndef ", "\n\n", "\n", " ", ""],
        )
        texts = splitter.split_documents(documents)

        # Indexação Local (Chroma)
        # BATCHING: Vertex AI has a hard limit of 250 instances per request.
        # AND a token limit (approx 20k tokens/request).
        # We use a safe batch size of 20 to respect both.
        batch_size = 20
        total_chunks = len(texts)
        
        from tqdm import tqdm
        import time
        
        print(f"📦 Processing {total_chunks} chunks in batches of {batch_size}...")

        for i in tqdm(range(0, total_chunks, batch_size), desc="Ingesting Batches"):
            batch = texts[i : i + batch_size]
            
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    if self.vector_db is None:
                        # Initialize DB with first batch
                        self.vector_db = Chroma.from_documents(
                            documents=batch,
                            embedding=self.embeddings,
                            persist_directory=self.persist_directory,
                        )
                    else:
                        # Add subsequent batches
                        self.vector_db.add_documents(documents=batch)
                    
                    # Success - break retry loop
                    time.sleep(1) # Gentle base delay
                    break
                    
                except Exception as e:
                    if "429" in str(e) or "Resource exhausted" in str(e):
                        if attempt == max_retries - 1:
                            print(f"\n❌ Batch failed after {max_retries} retries: {e}")
                            raise e
                        
                        wait_time = (2 ** attempt) * 2  # 2, 4, 8, 16, 32s
                        # print(f"⚠️ Quota hit. Backing off {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        print(f"\n❌ Unexpected error at batch {i}: {e}")
                        raise e

        if self.vector_db:
            self.vector_db.persist()
        
        return total_chunks

    def query_with_metrics(self, query: str, k: int = 4) -> Dict[str, Any]:
        """
        Executa retrieval e retorna métricas de precisão (Hit Rate Proxy).
        """
        if not self.vector_db:
            self.vector_db = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
            )

        # 1. Retrieval com Scores
        docs_with_scores = self.vector_db.similarity_search_with_relevance_scores(
            query, k=k
        )

        if not docs_with_scores:
            return {
                "answer": "No context found.",
                "metrics": {"hit_rate_k": "0%", "avg_confidence": 0.0, "top_source": "N/A"},
            }

        # 2. Cálculo de Métricas
        scores = [score for _, score in docs_with_scores]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        hit_rate = (
            len([s for s in scores if s > 0.7]) / k
        )  # Exemplo: Score > 0.7 é "Hit"

        # 3. Geração Aterrada
        context_text = "\n\n".join([d.page_content for d, _ in docs_with_scores])
        prompt = PromptTemplate(
            template="""Você é um Arquiteto de Software Sênior (PHANTOM).
Responda a pergunta baseada ESTRITAMENTE no contexto abaixo. Seja técnico e direto.

CONTEXTO:
{context}

PERGUNTA:
{question}

RESPOSTA (Markdown):""",
            input_variables=["context", "question"],
        )

        chain = prompt | self.llm
        response = chain.invoke({"context": context_text, "question": query})

        return {
            "answer": response,
            "metrics": {
                "avg_confidence": round(avg_score, 4),
                "hit_rate_k": f"{hit_rate:.0%}",
                "retrieved_docs": k,
                "top_source": docs_with_scores[0][0].metadata.get("source", "unknown"),
            },
        }
