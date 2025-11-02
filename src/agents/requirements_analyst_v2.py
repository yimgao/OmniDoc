"""
Requirements Analyst Agent (Simplified Version)
Uses Google Gemini API directly for Phase 1 MVP
"""
import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.rate_limit.queue_manager import RequestQueue

# Load environment variables
load_dotenv()

# Initialize rate limiting queue (60 requests per minute)
request_queue = RequestQueue(max_rate=60, period=60)


def write_file(filepath: str, content: str) -> str:
    """
    Write content to file
    
    Args:
        filepath: Path where file should be written
        content: Content to write
    
    Returns:
        Confirmation message
    """
    try:
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return f"✅ File written successfully to {filepath}"
    except Exception as e:
        return f"❌ Error writing file: {str(e)}"


class RequirementsAnalyst:
    """Requirements Analyst Agent using Gemini 1.5 Flash"""
    
    def __init__(self):
        """Initialize the agent with Gemini API"""
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment variables.\n"
                "Please:\n"
                "1. Get API key from https://aistudio.google.com/\n"
                "2. Create .env file with: GEMINI_API_KEY=your_key_here"
            )
        
        genai.configure(api_key=api_key)
        # Use gemini-2.0-flash (available and free tier compatible)
        # Alternative: 'gemini-2.5-flash' or 'gemini-2.0-flash'
        try:
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        except Exception:
            # Fallback to gemini-2.5-flash if 2.0 not available
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.api_key = api_key
    
    def _call_gemini(self, prompt: str) -> str:
        """
        Call Gemini API with rate limiting
        
        Args:
            prompt: Input prompt for the model
        
        Returns:
            Model response
        """
        def make_request():
            response = self.model.generate_content(prompt)
            return response.text
        
        # Apply rate limiting
        return request_queue.execute(make_request)
    
    def analyze_requirements(self, user_idea: str) -> str:
        """
        Analyze user idea and generate requirements document
        
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
        
        print(f"🤖 Requirements Analyst is analyzing: '{user_idea}'...")
        print("⏳ This may take a moment (rate limited to stay within free tier)...")
        
        # Check rate limit stats
        stats = request_queue.get_stats()
        print(f"📊 Rate limit status: {stats['requests_in_window']}/{stats['max_rate']} requests in window")
        
        try:
            requirements_doc = self._call_gemini(full_prompt)
            print("✅ Requirements document generated!")
            return requirements_doc
        except Exception as e:
            print(f"❌ Error generating requirements: {e}")
            raise
    
    def generate_and_save(self, user_idea: str, output_path: str = "docs/requirements.md") -> str:
        """
        Generate requirements and save to file
        
        Args:
            user_idea: User's project idea
            output_path: Path to save the requirements document
        
        Returns:
            Path to saved file
        """
        # Generate requirements
        requirements_doc = self.analyze_requirements(user_idea)
        
        # Save to file
        result = write_file(output_path, requirements_doc)
        print(result)
        
        # Verify file creation
        path = Path(output_path)
        if path.exists():
            file_size = path.stat().st_size
            print(f"📄 File saved: {output_path} ({file_size} bytes)")
            return str(path.absolute())
        else:
            raise FileNotFoundError(f"File was not created at {output_path}")


def generate_requirements(user_idea: str, output_dir: str = "docs") -> str:
    """
    Main function to generate requirements document
    
    Args:
        user_idea: User's project idea/requirement
        output_dir: Directory to save output
    
    Returns:
        Path to generated requirements document
    """
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Create agent and generate
    agent = RequirementsAnalyst()
    output_path = Path(output_dir) / "requirements.md"
    
    return agent.generate_and_save(user_idea, str(output_path))


if __name__ == "__main__":
    # Test with example
    test_idea = "I want to build a task management app"
    result = generate_requirements(test_idea)
    if result:
        print(f"\n✅ Success! Requirements saved to: {result}")

