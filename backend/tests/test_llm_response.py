"""
Test script to diagnose LLM response issues with Nexus Resume analysis.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.rag_provider_factory import get_llm
from app.config import settings


async def test_basic_completion():
    """Test basic LLM completion."""
    print(f"\n{'='*60}")
    print(f"Testing Groq LLM - Model: {settings.groq_model}")
    print(f"{'='*60}\n")
    
    llm = get_llm()
    
    # Test 1: Simple completion
    print("Test 1: Simple completion")
    print("-" * 40)
    try:
        response = await llm.acomplete("Say 'Hello World' in JSON format: {\"message\": \"Hello World\"}")
        print(f"Response type: {type(response)}")
        print(f"Response attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
        
        # Try different ways to extract text
        response_text = ""
        if hasattr(response, 'text'):
            response_text = response.text
            print(f"✓ Got via .text: {response_text[:100]}")
        elif hasattr(response, 'delta'):
            response_text = response.delta
            print(f"✓ Got via .delta: {response_text[:100]}")
        elif hasattr(response, 'raw'):
            raw = response.raw
            if hasattr(raw, 'choices') and raw.choices:
                choice = raw.choices[0]
                if hasattr(choice, 'message'):
                    response_text = choice.message.content
                    print(f"✓ Got via .raw.choices[0].message.content: {response_text[:100]}")
        
        if not response_text:
            print(f"✗ No response text found")
            print(f"Response object: {response}")
        else:
            print(f"\nFull response ({len(response_text)} chars):")
            print(response_text)
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: JSON response
    print(f"\n{'='*60}")
    print("Test 2: JSON response")
    print("-" * 40)
    try:
        prompt = """Return ONLY valid JSON with this structure:
{
  "test": "success",
  "data": {
    "name": "John Doe",
    "skills": ["Python", "JavaScript"]
  }
}"""
        response = await llm.acomplete(prompt)
        
        response_text = ""
        if hasattr(response, 'text'):
            response_text = response.text
        elif hasattr(response, 'delta'):
            response_text = response.delta
        elif hasattr(response, 'raw'):
            raw = response.raw
            if hasattr(raw, 'choices') and raw.choices:
                choice = raw.choices[0]
                if hasattr(choice, 'message'):
                    response_text = choice.message.content
        
        if response_text:
            print(f"✓ Got response ({len(response_text)} chars)")
            print(f"\nResponse:\n{response_text}")
            
            # Try to parse as JSON
            import json
            try:
                parsed = json.loads(response_text.strip())
                print(f"\n✓ Successfully parsed JSON:")
                print(json.dumps(parsed, indent=2))
            except json.JSONDecodeError as je:
                print(f"\n✗ Failed to parse JSON: {je}")
        else:
            print(f"✗ Empty response")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Minimal resume analysis
    print(f"\n{'='*60}")
    print("Test 3: Minimal resume analysis")
    print("-" * 40)
    try:
        prompt = """Analyze this resume and return ONLY JSON:

RESUME:
John Doe
Software Engineer
Python, JavaScript, React

JOB:
Looking for Python developer

Return JSON:
{
  "resume_analysis": {
    "name": "John Doe",
    "skills": ["Python", "JavaScript", "React"]
  },
  "job_analysis": {
    "title": "Python Developer",
    "required_skills": ["Python"]
  }
}"""
        response = await llm.acomplete(prompt)
        
        response_text = ""
        if hasattr(response, 'text'):
            response_text = response.text
        elif hasattr(response, 'delta'):
            response_text = response.delta
        elif hasattr(response, 'raw'):
            raw = response.raw
            if hasattr(raw, 'choices') and raw.choices:
                choice = raw.choices[0]
                if hasattr(choice, 'message'):
                    response_text = choice.message.content
        
        if response_text:
            print(f"✓ Got response ({len(response_text)} chars)")
            print(f"\nFirst 500 chars:\n{response_text[:500]}")
        else:
            print(f"✗ Empty response")
            print(f"Response object: {response}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("Tests complete")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(test_basic_completion())
