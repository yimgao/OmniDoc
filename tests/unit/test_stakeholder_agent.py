"""
Unit Tests: StakeholderCommunicationAgent
Fast, isolated tests for stakeholder communication agent
"""
import pytest
from src.agents.stakeholder_communication_agent import StakeholderCommunicationAgent


@pytest.mark.unit
class TestStakeholderCommunicationAgent:
    """Test StakeholderCommunicationAgent class"""
    
    def test_agent_initialization(self, mock_llm_provider, file_manager):
        """Test agent initialization"""
        agent = StakeholderCommunicationAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        assert agent.agent_name == "StakeholderCommunicationAgent"
        assert agent.file_manager is not None
    
    def test_generate_stakeholder_doc(self, mock_llm_provider, file_manager, sample_requirements_summary):
        """Test generating stakeholder documentation"""
        agent = StakeholderCommunicationAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        result = agent.generate(sample_requirements_summary)
        
        assert result is not None
        assert len(result) > 0
    
    def test_generate_stakeholder_doc_with_pm(self, mock_llm_provider, file_manager, sample_requirements_summary):
        """Test generating stakeholder documentation with PM summary"""
        agent = StakeholderCommunicationAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        pm_summary = "## Project Timeline\n3 months with 3 milestones"
        result = agent.generate(sample_requirements_summary, pm_summary)
        
        assert result is not None
        assert len(result) > 0
    
    def test_generate_and_save(self, mock_llm_provider, file_manager, sample_requirements_summary):
        """Test generating and saving stakeholder documentation"""
        agent = StakeholderCommunicationAgent(
            llm_provider=mock_llm_provider,
            file_manager=file_manager
        )
        
        file_path = agent.generate_and_save(sample_requirements_summary, output_filename="stakeholder.md")
        
        assert file_path is not None
        assert file_manager.file_exists("stakeholder.md")

