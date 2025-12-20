"""
Test script to verify reranking works correctly
"""

import asyncio
from app.core.reranker import get_reranker
from llama_index.core.schema import NodeWithScore, TextNode


async def test_reranker():
    """Test the reranker with sample data"""
    print("🧪 Testing Reranker...")
    
    # Create sample nodes
    nodes = [
        NodeWithScore(
            node=TextNode(
                text="Python is a high-level programming language.",
                metadata={"filename": "doc1.txt"}
            ),
            score=0.8
        ),
        NodeWithScore(
            node=TextNode(
                text="JavaScript is used for web development.",
                metadata={"filename": "doc2.txt"}
            ),
            score=0.7
        ),
        NodeWithScore(
            node=TextNode(
                text="Python has extensive libraries for data science.",
                metadata={"filename": "doc3.txt"}
            ),
            score=0.9
        ),
    ]
    
    # Get reranker
    reranker = get_reranker(top_n=2)
    
    # Test reranking
    query = "What is Python used for?"
    
    print(f"Query: {query}")
    print(f"Input nodes: {len(nodes)}")
    
    try:
        reranked = reranker._postprocess_nodes(nodes, query_str=query)
        print(f"✅ Reranking succeeded!")
        print(f"Output nodes: {len(reranked)}")
        
        for i, node in enumerate(reranked, 1):
            print(f"  {i}. Score: {node.score:.4f} - {node.node.text[:50]}...")
            
    except Exception as e:
        print(f"❌ Reranking failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run in a fresh event loop
    asyncio.run(test_reranker())
