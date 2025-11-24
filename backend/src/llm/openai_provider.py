"""
OpenAI GPT LLM Provider
Implements BaseLLMProvider for OpenAI API
"""
import os
from typing import Optional
from src.llm.base_provider import BaseLLMProvider

# OpenAI will be imported only when needed
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT API provider"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "gpt-4o-mini",
        **kwargs
    ):
        """
        Initialize OpenAI provider
        
        Args:
            api_key: OpenAI API key (if None, loads from OPENAI_API_KEY env var)
            default_model: Default model to use (gpt-4o-mini, gpt-4o, gpt-3.5-turbo)
            **kwargs: Additional OpenAI-specific config
        """
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        
        super().__init__(api_key=api_key, **kwargs)
        
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI package not installed. "
                "Install with: pip install openai"
            )
        
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY not found. "
                "Please set it in .env file or pass as parameter."
            )
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=self.api_key)
        self.default_model_name = default_model
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text using OpenAI API
        
        Args:
            prompt: Input prompt
            model: Model name (uses default if None)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional OpenAI parameters
            
        Returns:
            Generated text
        """
        model_name = model or self.default_model_name
        
        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")
    
    def get_available_models(self) -> list:
        """Get list of available OpenAI models"""
        # Common OpenAI models
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
        ]
    
    def get_default_model(self) -> str:
        """Get default OpenAI model"""
        return self.default_model_name

