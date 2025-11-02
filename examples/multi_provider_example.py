#!/usr/bin/env python3
"""
Example: Using Multiple LLM Providers
Demonstrates how to switch between Gemini, OpenAI, and other providers
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.requirements_analyst import RequirementsAnalyst
from src.llm.provider_factory import ProviderFactory


def example_gemini():
    """Example: Using Gemini (default)"""
    print("=" * 60)
    print("Example 1: Using Gemini (Default)")
    print("=" * 60)
    
    # Uses Gemini automatically (from .env or default)
    agent = RequirementsAnalyst()
    
    print(f"Provider: {agent.provider_name}")
    print(f"Model: {agent.model_name}")
    print()
    
    # Generate documentation
    idea = "Build a simple task management app"
    try:
        result = agent.generate_and_save(idea, "examples/gemini_requirements.md")
        print(f"✅ Generated with Gemini: {result}\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")


def example_openai():
    """Example: Using OpenAI GPT"""
    print("=" * 60)
    print("Example 2: Using OpenAI GPT")
    print("=" * 60)
    
    try:
        # Switch to OpenAI
        agent = RequirementsAnalyst(provider_name="openai")
        
        print(f"Provider: {agent.provider_name}")
        print(f"Model: {agent.model_name}")
        print()
        
        # Generate documentation
        idea = "Build a simple task management app"
        result = agent.generate_and_save(idea, "examples/openai_requirements.md")
        print(f"✅ Generated with OpenAI: {result}\n")
        
    except ValueError as e:
        print(f"⚠️  OpenAI not configured: {e}")
        print("   Set OPENAI_API_KEY in .env or install: uv pip install -e '.[openai]'\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")


def example_custom_model():
    """Example: Using custom model"""
    print("=" * 60)
    print("Example 3: Using Custom Model")
    print("=" * 60)
    
    # Use specific Gemini model
    agent = RequirementsAnalyst(
        provider_name="gemini",
        default_model="gemini-2.5-flash"  # or "gemini-2.5-pro"
    )
    
    print(f"Provider: {agent.provider_name}")
    print(f"Model: {agent.model_name}")
    print()
    
    idea = "Build a simple task management app"
    try:
        result = agent.generate_and_save(idea, "examples/custom_model_requirements.md")
        print(f"✅ Generated with custom model: {result}\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")


def example_shared_rate_limiter():
    """Example: Sharing rate limiter across providers"""
    print("=" * 60)
    print("Example 4: Shared Rate Limiter")
    print("=" * 60)
    
    from src.rate_limit.queue_manager import RequestQueue
    
    # Create shared rate limiter (useful when using multiple providers)
    shared_limiter = RequestQueue(max_rate=60, period=60)
    
    # Multiple agents can share the same limiter
    gemini_agent = RequirementsAnalyst(
        provider_name="gemini",
        rate_limiter=shared_limiter
    )
    
    try:
        openai_agent = RequirementsAnalyst(
            provider_name="openai",
            rate_limiter=shared_limiter
        )
        print("✅ Created agents with shared rate limiter")
        print(f"   Gemini agent: {gemini_agent.provider_name}")
        print(f"   OpenAI agent: {openai_agent.provider_name}\n")
    except Exception as e:
        print(f"⚠️  Could not create OpenAI agent: {e}\n")


def example_provider_factory():
    """Example: Using ProviderFactory directly"""
    print("=" * 60)
    print("Example 5: Provider Factory")
    print("=" * 60)
    
    # List available providers
    providers = ProviderFactory.get_available_providers()
    print(f"Available providers: {', '.join(providers)}")
    
    # Get config from environment
    config = ProviderFactory.get_provider_config_from_env()
    print(f"Environment config: {config}")
    print()
    
    # Create provider manually
    try:
        provider = ProviderFactory.create("gemini")
        print(f"✅ Created provider: {provider.get_provider_name()}")
        print(f"   Default model: {provider.get_default_model()}")
        print(f"   Available models: {len(provider.get_available_models())} models\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")


if __name__ == "__main__":
    print("\n🚀 Multi-Provider Examples\n")
    
    # Run examples
    example_gemini()
    example_openai()
    example_custom_model()
    example_shared_rate_limiter()
    example_provider_factory()
    
    print("=" * 60)
    print("✅ Examples complete!")
    print("=" * 60)

