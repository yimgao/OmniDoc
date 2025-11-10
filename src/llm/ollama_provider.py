"""
Ollama LLM Provider
Implements BaseLLMProvider for local Ollama API
"""
import os
from typing import Optional
import requests
from requests.exceptions import ConnectionError, RequestException
from src.llm.base_provider import BaseLLMProvider
from src.utils.logger import get_logger

logger = get_logger(__name__)


class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM API provider"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Ollama provider
        
        Args:
            api_key: API key (not required for Ollama, kept for compatibility)
            default_model: Default model to use (e.g., 'dolphin3')
                          If None, loads from OLLAMA_DEFAULT_MODEL env var
            base_url: Ollama API base URL (e.g., 'http://localhost:11434')
                     If None, loads from OLLAMA_BASE_URL env var
            **kwargs: Additional Ollama-specific config
        """
        # Ollama doesn't require API key, but we keep it for base class compatibility
        super().__init__(api_key=api_key, **kwargs)
        
        # Get default model from env or parameter
        if default_model is None:
            default_model = os.getenv("OLLAMA_DEFAULT_MODEL", "dolphin3")
        
        # Get base URL from env or parameter
        if base_url is None:
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        self.default_model_name = default_model
        self.base_url = base_url.rstrip('/')  # Remove trailing slash
        
        # Test connection to Ollama server
        try:
            self._test_connection()
        except ConnectionError:
            logger.warning(
                f"Could not connect to Ollama server at {self.base_url}. "
                "Make sure Ollama is running. You can start it with: ollama serve"
            )
    
    def _test_connection(self):
        """Test connection to Ollama server"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
        except ConnectionError as e:
            raise ConnectionError(
                f"Cannot connect to Ollama server at {self.base_url}. "
                "Please ensure Ollama is running."
            ) from e
        except RequestException as e:
            raise RuntimeError(f"Error connecting to Ollama server: {str(e)}") from e
    
    def validate_config(self) -> bool:
        """
        Validate provider configuration
        Ollama doesn't require API key, so we override this to always return True
        if the server is reachable
        
        Returns:
            True if configuration is valid (server is reachable)
        """
        try:
            self._test_connection()
            return True
        except (ConnectionError, RequestException):
            return False
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text using Ollama API
        
        Args:
            prompt: Input prompt
            model: Model name (uses default if None)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate (defaults to 8192 if not provided)
                       This ensures longer outputs similar to Gemini's default behavior
            **kwargs: Additional Ollama parameters (e.g., top_p, top_k)
            
        Returns:
            Generated text
            
        Raises:
            ConnectionError: If Ollama server is not running
            RuntimeError: If API call fails
        """
        model_name = model or self.default_model_name
        
        # Prepare request payload
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        
        # Set default max_tokens if not provided
        # Ollama's default num_predict is very low (~512), which causes short outputs
        # We set a higher default (8192 tokens) to match Gemini's behavior
        # This allows for ~32,000 characters of output (4 chars per token average)
        if max_tokens is None:
            # Use default from config or environment, otherwise 8192
            default_max_tokens = os.getenv("OLLAMA_MAX_TOKENS")
            if default_max_tokens:
                max_tokens = int(default_max_tokens)
            else:
                max_tokens = 8192  # Default to 8192 tokens for longer outputs
        
        # Add max_tokens (Ollama uses num_predict)
        payload["options"]["num_predict"] = max_tokens
        
        # Add any additional options from kwargs
        if "top_p" in kwargs:
            payload["options"]["top_p"] = kwargs.pop("top_p")
        if "top_k" in kwargs:
            payload["options"]["top_k"] = kwargs.pop("top_k")
        
        # Add any remaining kwargs as options
        if kwargs:
            payload["options"].update(kwargs)
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=300  # 5 minute timeout for long generations
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Extract message content from response
            if "message" in result and "content" in result["message"]:
                return result["message"]["content"]
            elif "response" in result:
                # Fallback for /api/generate endpoint format
                return result["response"]
            else:
                raise RuntimeError(f"Unexpected Ollama API response format: {result}")
                
        except ConnectionError as e:
            raise ConnectionError(
                f"Cannot connect to Ollama server at {self.base_url}. "
                "Please ensure Ollama is running."
            ) from e
        except RequestException as e:
            raise RuntimeError(f"Ollama API error: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"Unexpected error calling Ollama API: {str(e)}") from e
    
    def get_available_models(self) -> list:
        """
        Get list of available Ollama models
        
        Returns:
            List of model names available locally
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Extract model names from response
            if "models" in result:
                return [model["name"] for model in result["models"]]
            else:
                logger.warning("Unexpected response format from Ollama /api/tags")
                return [self.default_model_name]
                
        except ConnectionError:
            logger.warning(
                f"Cannot connect to Ollama server at {self.base_url}. "
                "Returning default model only."
            )
            return [self.default_model_name]
        except RequestException as e:
            logger.warning(f"Error fetching Ollama models: {str(e)}")
            return [self.default_model_name]
        except Exception as e:
            logger.warning(f"Unexpected error fetching Ollama models: {str(e)}")
            return [self.default_model_name]
    
    def get_default_model(self) -> str:
        """Get default Ollama model"""
        return self.default_model_name

