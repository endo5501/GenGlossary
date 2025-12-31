#!/usr/bin/env python3
"""Integration test for OllamaClient with real Ollama server."""

from pydantic import BaseModel
from src.genglossary.llm.ollama_client import OllamaClient


class SimpleTerm(BaseModel):
    """Simple term model for testing."""
    term: str
    definition: str


def main():
    print("=" * 60)
    print("Ollama Integration Test")
    print("=" * 60)

    # Initialize client
    client = OllamaClient(
        base_url="http://localhost:11434",
        model="llama2",
        timeout=60.0,
        max_retries=3
    )

    # Test 1: Check availability
    print("\n[Test 1] Checking Ollama server availability...")
    is_available = client.is_available()
    print(f"✓ Server available: {is_available}")

    if not is_available:
        print("✗ Ollama server is not available. Please start it with 'ollama serve'")
        return

    # Test 2: Simple text generation
    print("\n[Test 2] Simple text generation...")
    prompt = "What is the capital of Japan? Answer in one short sentence."
    response = client.generate(prompt)
    print(f"Prompt: {prompt}")
    print(f"Response: {response[:200]}...")
    print("✓ Text generation successful")

    # Test 3: Structured output
    print("\n[Test 3] Structured output generation...")
    structured_prompt = """Define the term "API" in the context of software development.

Return your answer as a JSON object with exactly these fields:
- term: the term being defined (string)
- definition: a concise definition in one sentence (string)

Example format:
{"term": "API", "definition": "..."}
"""

    try:
        result = client.generate_structured(structured_prompt, SimpleTerm)
        print(f"Term: {result.term}")
        print(f"Definition: {result.definition}")
        print("✓ Structured output generation successful")
    except Exception as e:
        print(f"✗ Structured output failed: {e}")
        # Try to see what the raw response was
        raw_response = client.generate(structured_prompt)
        print(f"Raw response: {raw_response[:300]}...")

    print("\n" + "=" * 60)
    print("Integration test completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
