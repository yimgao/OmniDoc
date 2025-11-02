"""
Basic Quality Checks for Documentation
Implements word count, completeness, and readability checks
"""
import re
from pathlib import Path
try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False


def check_word_count(content, min_words=100):
    """
    Check if content meets minimum word count
    
    Args:
        content: Text content to check
        min_words: Minimum word count threshold
    
    Returns:
        dict with score (0-100) and status
    """
    word_count = len(content.split())
    score = min(100, (word_count / min_words) * 100) if min_words > 0 else 100
    
    return {
        "word_count": word_count,
        "min_threshold": min_words,
        "score": score,
        "passed": word_count >= min_words
    }


def check_sections(content, required_sections=None):
    """
    Check if required sections are present in documentation
    
    Args:
        content: Documentation content
        required_sections: List of required section headers
    
    Returns:
        dict with completeness score (0-100) and missing sections
    """
    if required_sections is None:
        # Default required sections for requirements document
        required_sections = [
            "Features", "Technical Requirements", "User Personas",
            "Business Objectives", "Constraints"
        ]
    
    # Extract headings (lines starting with # or ##)
    headings = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
    headings_lower = [h.lower() for h in headings]
    
    found_sections = []
    missing_sections = []
    
    for section in required_sections:
        section_lower = section.lower()
        # Check if section exists (fuzzy matching)
        found = any(section_lower in heading or heading in section_lower 
                   for heading in headings_lower)
        if found:
            found_sections.append(section)
        else:
            missing_sections.append(section)
    
    completeness_score = (len(found_sections) / len(required_sections)) * 100 if required_sections else 100
    
    return {
        "required_sections": required_sections,
        "found_sections": found_sections,
        "missing_sections": missing_sections,
        "completeness_score": completeness_score,
        "passed": len(missing_sections) == 0
    }


def check_readability(content):
    """
    Check readability of documentation using Flesch Reading Ease
    
    Args:
        content: Text content to analyze
    
    Returns:
        dict with readability score and level
    """
    if not TEXTSTAT_AVAILABLE:
        return {
            "score": 0,
            "level": "unknown",
            "note": "textstat not installed"
        }
    
    try:
        flesch_score = textstat.flesch_reading_ease(content)
        
        # Convert to 0-100 scale for consistency
        # Flesch Reading Ease typically ranges from 0-100, where higher is easier
        readability_score = min(100, max(0, flesch_score))
        
        # Determine readability level
        if flesch_score >= 70:
            level = "Easy"
        elif flesch_score >= 50:
            level = "Medium"
        else:
            level = "Difficult"
        
        return {
            "flesch_score": flesch_score,
            "readability_score": readability_score,
            "level": level,
            "passed": flesch_score >= 50  # Medium or easier
        }
    except Exception as e:
        return {
            "score": 0,
            "level": "error",
            "error": str(e)
        }


def check_quality(doc_path, required_sections=None):
    """
    Comprehensive quality check for a documentation file
    
    Args:
        doc_path: Path to documentation file
        required_sections: List of required sections
    
    Returns:
        dict with all quality metrics
    """
    path = Path(doc_path)
    
    if not path.exists():
        return {
            "error": f"File not found: {doc_path}",
            "passed": False
        }
    
    content = path.read_text(encoding='utf-8')
    
    # Run all checks
    word_check = check_word_count(content)
    section_check = check_sections(content, required_sections)
    readability_check = check_readability(content)
    
    # Calculate overall score (weighted)
    overall_score = (
        word_check["score"] * 0.3 +
        section_check["completeness_score"] * 0.5 +
        readability_check.get("readability_score", 50) * 0.2
    )
    
    return {
        "file": str(doc_path),
        "word_count": word_check,
        "sections": section_check,
        "readability": readability_check,
        "overall_score": overall_score,
        "passed": overall_score >= 75  # Threshold from plan
    }

