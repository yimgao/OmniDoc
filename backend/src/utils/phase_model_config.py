"""
Phase-based Model Configuration
Allows configuring different models for different phases via environment variables
"""
import os
from typing import Optional


def get_model_for_phase(phase_number: int, provider_name: Optional[str] = None) -> Optional[str]:
    """
    Get model name for a specific phase from environment variables
    
    Supports multiple providers:
    - Ollama: OLLAMA_PHASE{N}_MODEL, falls back to OLLAMA_DEFAULT_MODEL
    - Gemini: GEMINI_PHASE{N}_MODEL, falls back to GEMINI_DEFAULT_MODEL
    - OpenAI: OPENAI_PHASE{N}_MODEL, falls back to OPENAI_DEFAULT_MODEL
    
    Priority:
    1. {PROVIDER}_PHASE{phase_number}_MODEL (phase-specific config)
    2. {PROVIDER}_DEFAULT_MODEL (provider default)
    3. None (use provider's built-in default)
    
    Args:
        phase_number: Phase number (1, 2, 3, 4, etc.)
        provider_name: Provider name (e.g., "ollama", "gemini", "openai")
                      If None, checks LLM_PROVIDER env var
    
    Returns:
        Model name to use for this phase, or None to use provider default
        
    Examples:
        >>> # Ollama: Phase 1 uses dolphin3, Phase 2 uses mixtral
        >>> get_model_for_phase(1, "ollama")  # Returns "dolphin3" if OLLAMA_PHASE1_MODEL=dolphin3
        >>> get_model_for_phase(2, "ollama")  # Returns "mixtral" if OLLAMA_PHASE2_MODEL=mixtral
        >>> 
        >>> # Gemini: Phase 1 uses flash, Phase 2 uses pro
        >>> get_model_for_phase(1, "gemini")  # Returns "gemini-2.0-flash" if GEMINI_PHASE1_MODEL=gemini-2.0-flash
        >>> get_model_for_phase(2, "gemini")  # Returns "gemini-2.0-pro" if GEMINI_PHASE2_MODEL=gemini-2.0-pro
        >>> 
        >>> # OpenAI: Phase 1 uses mini, Phase 2 uses gpt-4o
        >>> get_model_for_phase(1, "openai")  # Returns "gpt-4o-mini" if OPENAI_PHASE1_MODEL=gpt-4o-mini
        >>> get_model_for_phase(2, "openai")  # Returns "gpt-4o" if OPENAI_PHASE2_MODEL=gpt-4o
    """
    # Determine provider name
    if provider_name is None:
        provider_name = os.getenv("LLM_PROVIDER", "").lower()
    else:
        provider_name = provider_name.lower()
    
    # Map provider names to their env var prefixes
    provider_prefixes = {
        "ollama": "OLLAMA",
        "gemini": "GEMINI",
        "openai": "OPENAI"
    }
    
    if provider_name not in provider_prefixes:
        # Unknown provider, return None to use provider default
        return None
    
    prefix = provider_prefixes[provider_name]
    
    # Check for phase-specific model config
    phase_model_key = f"{prefix}_PHASE{phase_number}_MODEL"
    phase_model = os.getenv(phase_model_key)
    
    if phase_model:
        return phase_model.strip()
    
    # Fall back to provider default model
    default_model_key = f"{prefix}_DEFAULT_MODEL"
    default_model = os.getenv(default_model_key)
    if default_model:
        return default_model.strip()
    
    # No model specified - for Gemini, default to gemini-2.0-flash
    # For other providers, use provider's built-in default
    if provider_name == "gemini":
        return "gemini-2.0-flash"
    
    return None


def get_all_phase_models(provider_name: Optional[str] = None) -> dict:
    """
    Get all configured phase models as a dictionary
    
    Args:
        provider_name: Provider name (e.g., "ollama", "gemini", "openai")
                      If None, checks LLM_PROVIDER env var
    
    Returns:
        Dictionary mapping phase numbers to model names
        Example: {1: "dolphin3", 2: "mixtral", 3: "dolphin3"}
                 or {1: "gemini-2.0-flash", 2: "gemini-2.0-pro"}
                 or {1: "gpt-4o-mini", 2: "gpt-4o"}
    """
    phase_models = {}
    
    # Check for phase-specific configs (Phase 1-10)
    for phase_num in range(1, 11):
        model = get_model_for_phase(phase_num, provider_name)
        if model:
            phase_models[phase_num] = model
    
    return phase_models

