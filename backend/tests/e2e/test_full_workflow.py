"""
End-to-End Tests: Complete Documentation Generation
Full system tests (may require API keys)
"""
import pytest


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.requires_api
class TestFullWorkflow:
    """End-to-end tests for complete workflow"""
    
    def test_full_workflow_with_real_api(self, api_key_available, temp_db, temp_dir):
        """Test complete workflow with real API (if available)"""
        if not api_key_available["any"]:
            pytest.skip("No API keys available")
        
        from src.coordination.coordinator import WorkflowCoordinator
        from src.context.context_manager import ContextManager
        from pathlib import Path
        
        context_manager = ContextManager(db_path=temp_db)
        coordinator = WorkflowCoordinator(context_manager=context_manager)
        
        try:
            results = coordinator.generate_all_docs(
                "Create a simple task management application"
            )
            
            # Verify results
            assert results.get("project_id") is not None
            assert "requirements" in results["files"]
            assert "pm_documentation" in results["files"]
            
            # Verify files exist
            assert Path(results["files"]["requirements"]).exists()
            assert Path(results["files"]["pm_documentation"]).exists()
            
            # Verify file sizes
            req_size = Path(results["files"]["requirements"]).stat().st_size
            pm_size = Path(results["files"]["pm_documentation"]).stat().st_size
            
            assert req_size > 1000  # Should have substantial content
            assert pm_size > 1000
            
        finally:
            context_manager.close()

