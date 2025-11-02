"""
Requirements Analyst Agent
Uses OOP structure with BaseAgent inheritance
"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.utils.file_manager import FileManager
from src.rate_limit.queue_manager import RequestQueue
from pathlib import Path


class RequirementsAnalyst(BaseAgent):
    """
    Requirements Analyst Agent
    
    Analyzes user ideas and generates structured requirements documents
    """
    
    def __init__(
        self,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        rate_limiter: Optional[RequestQueue] = None,
        file_manager: Optional[FileManager] = None,
        api_key: Optional[str] = None,
        **provider_kwargs
    ):
        """
        Initialize Requirements Analyst
        
        Args:
            provider_name: LLM provider name ("gemini", "openai", etc.) - defaults to env var or "gemini"
            model_name: Model name override (provider-specific)
            rate_limiter: Shared rate limiter (optional)
            file_manager: File manager instance (optional)
            api_key: API key (optional, loads from env vars if not provided)
            **provider_kwargs: Additional provider-specific configuration
        
        Examples:
            >>> # Use default Gemini
            >>> agent = RequirementsAnalyst()
            
            >>> # Use OpenAI
            >>> agent = RequirementsAnalyst(provider_name="openai")
            
            >>> # Use specific GPT model
            >>> agent = RequirementsAnalyst(
            ...     provider_name="openai",
            ...     default_model="gpt-4o"
            ... )
        """
        # Initialize base agent with provider support
        super().__init__(
            provider_name=provider_name,
            model_name=model_name,
            rate_limiter=rate_limiter,
            api_key=api_key,
            **provider_kwargs
        )
        
        # Initialize file manager
        self.file_manager = file_manager or FileManager(base_dir="docs")
    
    def generate(self, user_idea: str) -> str:
        """
        Generate requirements document from user idea
        
        Args:
            user_idea: User's project idea/requirement
            
        Returns:
            Generated requirements document (Markdown)
        """
        system_prompt = """You are a Requirements Analyst specializing in extracting structured requirements from user ideas.

Analyze the user's project idea and create a comprehensive requirements document in Markdown format.

The document must include these sections:
1. ## Project Overview - Brief description of the project
2. ## Core Features - List of main features and functionality  
3. ## Technical Requirements - Technical specifications and constraints
4. ## User Personas - Target users and their needs
5. ## Business Objectives - Business goals and success metrics
6. ## Constraints and Assumptions - Limitations and assumptions

Format requirements:
- Use clear Markdown headings (## for main sections)
- Use bullet points for lists
- Be thorough, clear, and professional
- Each section should have substantial content (at least 3-5 points)
- Use proper Markdown formatting

Now, analyze the following user idea:"""
        
        full_prompt = f"{system_prompt}\n\nUser Idea: {user_idea}\n\nGenerate the complete requirements document:"
        
        print(f"🤖 {self.agent_name} is analyzing: '{user_idea}'...")
        print("⏳ This may take a moment (rate limited to stay within free tier)...")
        
        # Check rate limit stats
        stats = self.get_stats()
        print(f"📊 Rate limit status: {stats['requests_in_window']}/{stats['max_rate']} requests in window")
        
        try:
            requirements_doc = self._call_llm(full_prompt)
            print("✅ Requirements document generated!")
            return requirements_doc
        except Exception as e:
            print(f"❌ Error generating requirements: {e}")
            raise
    
    def generate_and_save(
        self,
        user_idea: str,
        output_filename: str = "requirements.md"
    ) -> str:
        """
        Generate requirements and save to file
        
        Args:
            user_idea: User's project idea
            output_filename: Filename to save (will be saved in base_dir)
            
        Returns:
            Absolute path to saved file
        """
        # Generate requirements
        requirements_doc = self.generate(user_idea)
        
        # Save to file
        try:
            file_path = self.file_manager.write_file(output_filename, requirements_doc)
            file_size = self.file_manager.get_file_size(output_filename)
            print(f"✅ File written successfully to {file_path}")
            print(f"📄 File saved: {output_filename} ({file_size} bytes)")
            return file_path
        except Exception as e:
            print(f"❌ Error writing file: {e}")
            raise
