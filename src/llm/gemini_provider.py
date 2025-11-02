"""
Google Gemini LLM Provider
Implements BaseLLMProvider for Google Gemini API
"""
import os
from typing import Optional
import google.generativeai as genai
from src.llm.base_provider import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider"""
    
    def __init__(self, api_key: Optional[str] = None, default_model: str = "gemini-2.0-flash", **kwargs):
        """
        Initialize Gemini provider
        
        Args:
            api_key: Gemini API key (if None, loads from GEMINI_API_KEY env var)
            default_model: Default model to use
            **kwargs: Additional Gemini-specific config
        """
        if api_key is None:
            api_key = os.getenv("GEMINI_API_KEY")
        
        super().__init__(api_key=api_key, **kwargs)
        
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. "
                "Please set it in .env file or pass as parameter."
            )
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Store default model
        self.default_model_name = default_model
        
        # Initialize model
        try:
            self._model = genai.GenerativeModel(default_model)
        except Exception:
            # Fallback to gemini-2.5-flash if 2.0 not available
            self.default_model_name = "gemini-2.5-flash"
            self._model = genai.GenerativeModel(self.default_model_name)
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text using Gemini API
        
        Args:
            prompt: Input prompt
            model: Model name (uses default if None)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Max tokens (Gemini uses max_output_tokens)
            **kwargs: Additional Gemini parameters
            
        Returns:
            Generated text
        """
        # Use provided model or default
        model_name = model or self.default_model_name
        
        # Create model instance if different from default
        if model_name != self.default_model_name:
            gen_model = genai.GenerativeModel(model_name)
        else:
            gen_model = self._model
        
        # Configure generation parameters
        generation_config = {
            "temperature": temperature,
            **kwargs
        }
        
        # Gemini uses max_output_tokens instead of max_tokens
        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens
        
        try:
            response = gen_model.generate_content(
                prompt,
                generation_config=generation_config
            )
            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {str(e)}")
    
    def get_available_models(self) -> list:
        """Get list of available Gemini models"""
        try:
            models = genai.list_models()
            return [
                m.name for m in models
                if 'generateContent' in m.supported_generation_methods
            ]
        except Exception:
            # Return common models as fallback
            return [
                "gemini-2.0-flash",
                "gemini-2.5-flash",
                "gemini-2.5-pro",
                "gemini-2.0-flash-exp"
            ]
    
    def get_default_model(self) -> str:
        """Get default Gemini model"""
        return self.default_model_name

