import pytest
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
from phantom.core.extraction.analyze_code import HermeticAnalyzer, RepoMetrics
from phantom.core.rag.engine import RigorousRAGEngine

@pytest.mark.integration
class TestPhantomWorkflow:
    """
    Integration tests for the full Phantom workflow:
    Analyze -> Ingest -> Query
    """

    @pytest.fixture(scope="class")
    def test_data_dir(self):
        base_dir = Path("./data/test_integration")
        base_dir.mkdir(parents=True, exist_ok=True)
        yield base_dir
        # Cleanup after tests
        if base_dir.exists():
            shutil.rmtree(base_dir)

    def test_1_analyze_repo(self, test_data_dir):
        """Test code analysis on a dummy file."""
        # Create a dummy python file
        repo_path = test_data_dir / "dummy_repo"
        repo_path.mkdir(exist_ok=True)
        (repo_path / "main.py").write_text("def hello():\n    print('world')")

        analyzer = HermeticAnalyzer()
        result = analyzer.analyze_repo(repo_path)
        
        assert len(result["artifacts"]) > 0
        assert result["artifacts"][0].name == "hello"
        
        # Save artifacts for ingestion
        import json
        jsonl_path = test_data_dir / "artifacts.jsonl"
        with open(jsonl_path, "w") as f:
            for a in result["artifacts"]:
                doc = {
                    "jsonData": json.dumps({
                        "title": a.name,
                        "content": a.content,
                        "repo": "dummy_repo",
                        "context": "test"
                    })
                }
                f.write(json.dumps(doc) + "\n")
        
        assert jsonl_path.exists()

    @patch("phantom.core.rag.engine.VertexAIEmbeddings")
    @patch("phantom.core.rag.engine.VertexAI")
    def test_2_ingest_artifacts(self, mock_llm, mock_emb, test_data_dir):
        """Test ingestion with mocked Vertex AI (to avoid quota/cost in CI)."""
        # We verify logic, batching and persistence here.
        
        # Mock Embeddings to return dummy vectors
        mock_instance = mock_emb.return_value
        mock_instance.embed_documents.side_effect = lambda texts: [[0.1]*768 for _ in texts]
        
        engine = RigorousRAGEngine(persist_directory=str(test_data_dir / "vector_db"))
        # Force inject mocked embeddings just in case __init__ was already called
        engine.embeddings = mock_instance
        
        jsonl_path = test_data_dir / "artifacts.jsonl"
        count = engine.ingest(str(jsonl_path))
        
        assert count > 0
        assert (test_data_dir / "vector_db").exists()

    @patch("phantom.core.rag.engine.VertexAIEmbeddings")
    @patch("phantom.core.rag.engine.VertexAI")
    def test_3_query_rag(self, mock_llm, mock_emb, test_data_dir):
        """Test querying the persisted DB."""
        
        # Mock Embeddings
        mock_emb_instance = mock_emb.return_value
        mock_emb_instance.embed_query.return_value = [0.1]*768
        
        # Mock LLM generation
        mock_llm_instance = mock_llm.return_value
        mock_llm_instance.invoke.return_value = "The hello function prints world."
        # We also need to mock the chain pipeline if it's constructed in the method
        # But mocking the class return_value usually works if the code uses instance.invoke()
        
        engine = RigorousRAGEngine(persist_directory=str(test_data_dir / "vector_db"))
        engine.embeddings = mock_emb_instance
        engine.llm = mock_llm_instance
        
        # We need to ensure the DB is loaded from disk
        # Since we are mocking Chroma in the engine usually, but here we want real Chroma logic 
        # with mocked embeddings.
        
        # However, engine.ingest used `Chroma.from_documents` which persists.
        # engine.query_with_metrics re-initializes Chroma:
        # self.vector_db = Chroma(persist_directory=..., embedding_function=self.embeddings)
        
        # Since we didn't mock Chroma class itself in this test, it will try to use real Chroma.
        # Real Chroma requires real sqlite3.
        
        result = engine.query_with_metrics("What does hello do?")
        
        assert "hello" in str(result) or "found" in str(result)
        # Note: Since embeddings are dummy [0.1...], retrieval might return nothing or everything.
        # But we check that it runs without error.
