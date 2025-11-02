"""
Quality Checker Class
OOP implementation for documentation quality checks
"""
import re
from typing import Dict, List, Optional
try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False


class QualityChecker:
    """Handles all quality checks for documentation"""
    
    def __init__(
        self,
        min_words: int = 100,
        required_sections: Optional[List[str]] = None,
        min_readability_score: float = 60.0
    ):
        """
        Initialize quality checker
        
        Args:
            min_words: Minimum word count threshold
            required_sections: List of required section patterns (regex)
            min_readability_score: Minimum Flesch reading ease score
        """
        self.min_words = min_words
        self.required_sections = required_sections or [
            r"^#+\s+Project\s+Overview",
            r"^#+\s+Core\s+Features",
            r"^#+\s+Technical\s+Requirements",
            r"^#+\s+User\s+Personas",
            r"^#+\s+Business\s+Objectives",
            r"^#+\s+Constraints"
        ]
        self.min_readability_score = min_readability_score
    
    def check_word_count(self, content: str) -> Dict:
        """
        Check if content meets minimum word count
        
        Args:
            content: Text content to check
            
        Returns:
            dict with score (0-100), passed status, and word_count
        """
        word_count = len(re.findall(r'\b\w+\b', content))
        score = min(100, (word_count / self.min_words) * 100) if self.min_words > 0 else 100
        
        return {
            "score": score,
            "passed": word_count >= self.min_words,
            "word_count": word_count,
            "min_threshold": self.min_words
        }
    
    def check_sections(self, content: str) -> Dict:
        """
        Check if required sections are present
        
        Args:
            content: Markdown content to check
            
        Returns:
            dict with completeness score, found/missing sections
        """
        found_sections = []
        missing_sections = []
        
        for section_pattern in self.required_sections:
            if re.search(section_pattern, content, re.MULTILINE | re.IGNORECASE):
                found_sections.append(section_pattern)
            else:
                missing_sections.append(section_pattern)
        
        completeness_score = (len(found_sections) / len(self.required_sections) * 100) if self.required_sections else 100
        
        return {
            "completeness_score": completeness_score,
            "passed": len(missing_sections) == 0,
            "found_sections": found_sections,
            "missing_sections": missing_sections,
            "required_count": len(self.required_sections),
            "found_count": len(found_sections)
        }
    
    def check_readability(self, content: str) -> Dict:
        """
        Calculate readability score using Flesch Reading Ease
        
        Args:
            content: Text content to analyze
            
        Returns:
            dict with readability score and level
        """
        if not TEXTSTAT_AVAILABLE:
            return {
                "readability_score": 0,
                "level": "unknown",
                "passed": False,
                "note": "textstat not installed"
            }
        
        try:
            score = textstat.flesch_reading_ease(content)
            
            # Determine level
            if score >= 90:
                level = "Very Easy"
            elif score >= 80:
                level = "Easy"
            elif score >= 70:
                level = "Fairly Easy"
            elif score >= 60:
                level = "Standard"
            elif score >= 50:
                level = "Fairly Difficult"
            elif score >= 30:
                level = "Difficult"
            else:
                level = "Very Difficult"
            
            return {
                "readability_score": score,
                "level": level,
                "passed": score >= self.min_readability_score,
                "min_threshold": self.min_readability_score
            }
        except Exception as e:
            return {
                "readability_score": 0,
                "level": "error",
                "passed": False,
                "error": str(e)
            }
    
    def check_quality(self, content: str, weights: Optional[Dict[str, float]] = None) -> Dict:
        """
        Perform comprehensive quality check
        
        Args:
            content: Document content to check
            weights: Custom weights for overall score calculation
                    (default: word_count=0.2, completeness=0.5, readability=0.3)
        
        Returns:
            Comprehensive quality report
        """
        if weights is None:
            weights = {
                "word_count": 0.2,
                "completeness": 0.5,
                "readability": 0.3
            }
        
        # Run all checks
        word_count_result = self.check_word_count(content)
        sections_result = self.check_sections(content)
        readability_result = self.check_readability(content)
        
        # Calculate overall score
        overall_score = (
            word_count_result["score"] * weights["word_count"] +
            sections_result["completeness_score"] * weights["completeness"] +
            readability_result["readability_score"] * weights["readability"]
        )
        
        # Determine if passed
        passed = (
            word_count_result["passed"] and
            sections_result["passed"] and
            readability_result["passed"] and
            overall_score >= 75.0  # Minimum overall threshold
        )
        
        return {
            "overall_score": overall_score,
            "passed": passed,
            "word_count": word_count_result,
            "sections": sections_result,
            "readability": readability_result,
            "weights": weights
        }
    
    def check_file(self, filepath: str) -> Dict:
        """
        Check quality of a file
        
        Args:
            filepath: Path to file to check
            
        Returns:
            Quality report
        """
        from src.utils.file_manager import FileManager
        
        file_manager = FileManager()
        content = file_manager.read_file(filepath)
        return self.check_quality(content)

