"""
Test script to verify remote embedding service integration
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import settings
from app.services.remote_embedding_service import RemoteEmbeddingService, RemoteReranker


async def test_remote_embeddings():
    """Test remote embedding service"""
    print("\n" + "="*60)
    print("Testing Remote Embedding Service")
    print("="*60)
    
    service = RemoteEmbeddingService(
        base_url=settings.remote_embedding_service_url,
        model_name=settings.ollama_embedding_model
    )
    
    # Test embedding
    texts = ["Hello world", "Machine learning is amazing"]
    print(f"\n📝 Getting embeddings for {len(texts)} texts...")
    
    embeddings = await service._get_embeddings(texts)
    
    print(f"✅ Success!")
    print(f"   - Number of embeddings: {len(embeddings)}")
    print(f"   - Embedding dimension: {len(embeddings[0])}")
    print(f"   - First 5 values: {embeddings[0][:5]}")
    
    await service.close()


async def test_remote_reranker():
    """Test remote reranker"""
    print("\n" + "="*60)
    print("Testing Remote Reranker")
    print("="*60)
    
    reranker = RemoteReranker(
        base_url=settings.remote_embedding_service_url
    )
    
    # Test reranking
    query = "What is artificial intelligence?"
    documents = [
        "AI is the simulation of human intelligence by machines",
        "Python is a programming language",
        "Machine learning is a subset of AI",
        "The weather is nice today"
    ]
    
    print(f"\n🔍 Query: {query}")
    print(f"📄 Reranking {len(documents)} documents...")
    
    results = await reranker.rerank(
        query=query,
        documents=documents,
        top_k=2
    )
    
    print(f"\n✅ Success! Top {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"   {i}. Score: {result['score']:.4f} - {result['text'][:50]}...")
    
    await reranker.close()


async def main():
    """Run all tests"""
    print("\n🚀 Remote Embedding Service Integration Test")
    print(f"📍 Service URL: {settings.remote_embedding_service_url}")
    print(f"🔧 Remote mode: {settings.use_remote_embedding_service}")
    
    try:
        await test_remote_embeddings()
        await test_remote_reranker()
        
        print("\n" + "="*60)
        print("✅ All tests passed!")
        print("="*60)
        print("\n💡 Your backend is now configured to use Lightning.ai")
        print("   No more 2.27GB model downloads on startup! 🎉\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
