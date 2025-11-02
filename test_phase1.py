#!/usr/bin/env python3
"""
Phase 1 Test Script: "Hello, Documentation!" Test
Tests the Requirements Analyst agent with a simple input
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.requirements_analyst import RequirementsAnalyst
from src.quality.quality_checker import QualityChecker
from src.utils.file_manager import FileManager


def test_hello_documentation():
    """
    Phase 1 test: Generate requirements for "Create a simple blog platform"
    """
    print("=" * 60)
    print("Phase 1 Test: 'Hello, Documentation!'")
    print("=" * 60)
    print()
    
    # Test input
    test_idea = "Create a simple blog platform"
    print(f"📝 Test Input: '{test_idea}'")
    print()
    
    try:
        # Initialize OOP components
        agent = RequirementsAnalyst()
        file_manager = FileManager()
        quality_checker = QualityChecker()
        
        # Generate requirements using OOP
        result_path = agent.generate_and_save(test_idea, output_filename="requirements.md")
        
        if not result_path:
            print("❌ FAIL: Requirements document not generated")
            return False
        
        print()
        print("=" * 60)
        print("Running Quality Checks...")
        print("=" * 60)
        print()
        
        # Run quality checks using OOP
        content = file_manager.read_file("requirements.md")
        quality_results = quality_checker.check_quality(content)
        
        # Display results
        print("📊 Quality Check Results:")
        print(f"  Overall Score: {quality_results['overall_score']:.1f}/100")
        print(f"  Status: {'✅ PASSED' if quality_results['passed'] else '⚠️  NEEDS IMPROVEMENT'}")
        print()
        
        print("  Word Count:", quality_results['word_count']['word_count'], "words")
        print("  Section Completeness:", f"{quality_results['sections']['completeness_score']:.1f}%")
        print(f"    Found: {len(quality_results['sections']['found_sections'])} sections")
        print(f"    Missing: {len(quality_results['sections']['missing_sections'])} sections")
        if quality_results['sections']['missing_sections']:
            print(f"    Missing sections: {', '.join(quality_results['sections']['missing_sections'])}")
        
        if 'readability_score' in quality_results['readability']:
            print(f"  Readability: {quality_results['readability']['readability_score']:.1f} ({quality_results['readability']['level']})")
        
        print()
        print("=" * 60)
        print("Test Verification:")
        print("=" * 60)
        
        # Verify requirements
        checks = [
            ("File created", Path(result_path).exists()),
            ("Content relevant", quality_results['word_count']['word_count'] > 50),
            ("Structure correct", len(quality_results['sections']['found_sections']) >= 3)
        ]
        
        all_passed = True
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"{status} {check_name}")
            if not check_result:
                all_passed = False
        
        print()
        if all_passed:
            print("✅ ALL CHECKS PASSED!")
            print(f"📄 Requirements document: {result_path}")
            return True
        else:
            print("⚠️  Some checks failed. Review the document and improve.")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_hello_documentation()
    sys.exit(0 if success else 1)

