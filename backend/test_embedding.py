"""Test script to check embedding dimension."""
import asyncio
from app.services.ollama_service import get_ollama_service

async def test_embedding():
    ollama = get_ollama_service()
    
    # Test embedding
    text = "This is a test"
    embedding = await ollama.generate_embedding(text)
    
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
    
    return len(embedding)

if __name__ == "__main__":
    dim = asyncio.run(test_embedding())
    print(f"\nEmbedding model dimension: {dim}")
