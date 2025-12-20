"""
Test script for the embedding service
Run after starting the service to verify it's working
"""

import httpx
import asyncio

BASE_URL = "http://localhost:8001"


async def test_health():
    """Test health endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print("Health Check:", response.json())
        assert response.status_code == 200


async def test_embeddings():
    """Test embeddings endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/embeddings",
            json={
                "texts": [
                    "What is machine learning?",
                    "Python is a programming language"
                ]
            }
        )
        data = response.json()
        print(f"\nEmbeddings Test:")
        print(f"  - Generated {len(data['embeddings'])} embeddings")
        print(f"  - Dimension: {data['dimension']}")
        print(f"  - Model: {data['model']}")
        assert response.status_code == 200
        assert len(data['embeddings']) == 2


async def test_rerank():
    """Test reranking endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/rerank",
            json={
                "query": "What is artificial intelligence?",
                "documents": [
                    "Artificial intelligence is the simulation of human intelligence by machines",
                    "Python is a high-level programming language",
                    "Machine learning is a subset of artificial intelligence",
                    "The weather is nice today"
                ],
                "top_k": 2
            }
        )
        data = response.json()
        print(f"\nReranking Test:")
        print(f"  - Top {len(data['results'])} documents:")
        for i, result in enumerate(data['results'], 1):
            print(f"    {i}. Score: {result['score']:.3f} - {result['text'][:50]}...")
        assert response.status_code == 200
        assert len(data['results']) == 2
        # Check that results are sorted by score
        assert data['results'][0]['score'] >= data['results'][1]['score']


async def test_list_models():
    """Test models endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/models")
        data = response.json()
        print(f"\nAvailable Models:")
        print(f"  - Ollama models: {data['ollama_models']}")
        print(f"  - Reranker: {data['reranker_model']}")
        assert response.status_code == 200


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Embedding & Reranking Service")
    print("=" * 60)
    
    try:
        await test_health()
        await test_embeddings()
        await test_rerank()
        await test_list_models()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
