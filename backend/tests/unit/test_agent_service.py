"""
Unit tests for the AgentService.
"""
import pytest

from app.services.agent_service import (
    AgentService,
    AgentConfig,
    AGENTS,
    get_agent_service,
)


class TestAgentService:
    """Test suite for AgentService."""

    def test_parse_agent_mention_valid_quick(self):
        """Test parsing valid quick agent mention."""
        message = "@quick What is 2+2?"
        agent_name, cleaned = AgentService.parse_agent_mention(message)

        assert agent_name == "quick"
        assert cleaned == "What is 2+2?"

    def test_parse_agent_mention_valid_deep(self):
        """Test parsing valid deep agent mention."""
        message = "@deep Explain quantum computing"
        agent_name, cleaned = AgentService.parse_agent_mention(message)

        assert agent_name == "deep"
        assert cleaned == "Explain quantum computing"

    def test_parse_agent_mention_valid_code(self):
        """Test parsing valid code agent mention."""
        message = "@code How to implement quicksort?"
        agent_name, cleaned = AgentService.parse_agent_mention(message)

        assert agent_name == "code"
        assert cleaned == "How to implement quicksort?"

    def test_parse_agent_mention_valid_summarize(self):
        """Test parsing valid summarize agent mention."""
        message = "@summarize Condense this document"
        agent_name, cleaned = AgentService.parse_agent_mention(message)

        assert agent_name == "summarize"
        assert cleaned == "Condense this document"

    def test_parse_agent_mention_case_insensitive(self):
        """Test that agent mentions are case-insensitive."""
        message = "@QUICK What is AI?"
        agent_name, cleaned = AgentService.parse_agent_mention(message)

        assert agent_name == "quick"
        assert cleaned == "What is AI?"

        message2 = "@Deep Tell me more"
        agent_name2, cleaned2 = AgentService.parse_agent_mention(message2)

        assert agent_name2 == "deep"
        assert cleaned2 == "Tell me more"

    def test_parse_agent_mention_no_at_symbol(self):
        """Test parsing message without @ symbol."""
        message = "What is machine learning?"
        agent_name, cleaned = AgentService.parse_agent_mention(message)

        assert agent_name is None
        assert cleaned == message

    def test_parse_agent_mention_invalid_agent(self):
        """Test parsing invalid agent mention."""
        message = "@invalid What is this?"
        agent_name, cleaned = AgentService.parse_agent_mention(message)

        assert agent_name is None
        assert cleaned == message  # Returns original message

    def test_parse_agent_mention_only_at_symbol(self):
        """Test parsing message with only @ and agent name."""
        message = "@quick"
        agent_name, cleaned = AgentService.parse_agent_mention(message)

        assert agent_name is None
        assert cleaned == message

    def test_parse_agent_mention_whitespace_handling(self):
        """Test that extra whitespace is handled correctly."""
        message = "  @quick   What is this?  "
        agent_name, cleaned = AgentService.parse_agent_mention(message)

        assert agent_name == "quick"
        assert cleaned == "What is this?"  # Strips trailing whitespace

    def test_parse_agent_mention_multiple_spaces(self):
        """Test parsing with multiple spaces between agent and query."""
        message = "@quick    What is this?"
        agent_name, cleaned = AgentService.parse_agent_mention(message)

        assert agent_name == "quick"
        assert cleaned == "What is this?"

    def test_get_agent_quick(self):
        """Test getting quick agent config."""
        config = AgentService.get_agent("quick")

        assert config.name == "quick"
        assert config.display_name == "⚡ Quick"
        assert config.model == "llama3.2:3b"
        assert config.temperature == 0.3
        assert config.rag_top_k == 3
        assert config.use_rag is True

    def test_get_agent_deep(self):
        """Test getting deep agent config."""
        config = AgentService.get_agent("deep")

        assert config.name == "deep"
        assert config.display_name == "🔬 Deep"
        assert config.model == "qwen2.5:14b"
        assert config.temperature == 0.5
        assert config.rag_top_k == 20
        assert config.max_conversation_history == 15

    def test_get_agent_code(self):
        """Test getting code agent config."""
        config = AgentService.get_agent("code")

        assert config.name == "code"
        assert config.display_name == "💻 Code"
        assert config.model == "qwen2.5-coder:14b"
        assert config.temperature == 0.2
        assert config.rag_top_k == 10
        assert "code" in config.system_prompt.lower()

    def test_get_agent_summarize(self):
        """Test getting summarize agent config."""
        config = AgentService.get_agent("summarize")

        assert config.name == "summarize"
        assert config.display_name == "📝 Summarize"
        assert config.model == "llama3.2:3b"
        assert config.temperature == 0.4
        assert config.rag_top_k == 30  # More context for summarization
        assert config.max_conversation_history == 3

    def test_get_agent_none_returns_default(self):
        """Test that None returns default agent."""
        config = AgentService.get_agent(None)

        assert config.name == "default"
        assert config.display_name == "💬 Default"
        assert config.model == "qwen2.5:14b"
        assert config.temperature == 0.7
        assert config.rag_top_k == 10

    def test_get_agent_invalid_returns_default(self):
        """Test that invalid agent name returns default."""
        config = AgentService.get_agent("nonexistent")

        assert config.name == "default"
        assert config.display_name == "💬 Default"

    def test_get_agent_empty_string_returns_default(self):
        """Test that empty string returns default agent."""
        config = AgentService.get_agent("")

        assert config.name == "default"

    def test_list_available_agents(self):
        """Test listing all available agents."""
        agents_list = AgentService.list_available_agents()

        assert len(agents_list) == 4  # quick, deep, code, summarize
        agent_names = [agent["name"] for agent in agents_list]
        assert "quick" in agent_names
        assert "deep" in agent_names
        assert "code" in agent_names
        assert "summarize" in agent_names

    def test_list_available_agents_structure(self):
        """Test that agent list has correct structure."""
        agents_list = AgentService.list_available_agents()

        for agent in agents_list:
            assert "name" in agent
            assert "display_name" in agent
            assert "description" in agent
            assert isinstance(agent["name"], str)
            assert isinstance(agent["display_name"], str)
            assert isinstance(agent["description"], str)

    def test_list_available_agents_has_display_names(self):
        """Test that all agents have display names with emojis."""
        agents_list = AgentService.list_available_agents()

        display_names = [agent["display_name"] for agent in agents_list]
        assert "⚡ Quick" in display_names
        assert "🔬 Deep" in display_names
        assert "💻 Code" in display_names
        assert "📝 Summarize" in display_names

    def test_agents_config_has_all_required_fields(self):
        """Test that all agent configs have required fields."""
        for agent_name, config in AGENTS.items():
            assert hasattr(config, "name")
            assert hasattr(config, "display_name")
            assert hasattr(config, "description")
            assert hasattr(config, "model")
            assert hasattr(config, "temperature")
            assert hasattr(config, "rag_top_k")
            assert hasattr(config, "system_prompt")
            assert hasattr(config, "use_rag")
            assert hasattr(config, "max_conversation_history")

    def test_agents_config_temperatures_in_valid_range(self):
        """Test that all agent temperatures are in valid range."""
        for config in AGENTS.values():
            assert 0.0 <= config.temperature <= 1.0

    def test_agents_config_rag_top_k_positive(self):
        """Test that all agents have positive rag_top_k."""
        for config in AGENTS.values():
            assert config.rag_top_k > 0

    def test_agents_config_system_prompts_not_empty(self):
        """Test that all agents have non-empty system prompts."""
        for config in AGENTS.values():
            assert config.system_prompt.strip() != ""
            assert len(config.system_prompt) > 10  # Reasonable length

    def test_agent_config_dataclass(self):
        """Test AgentConfig dataclass creation."""
        config = AgentConfig(
            name="test",
            display_name="Test Agent",
            description="Test description",
            model="test-model",
            temperature=0.5,
            rag_top_k=5,
            system_prompt="Test prompt",
        )

        assert config.name == "test"
        assert config.display_name == "Test Agent"
        assert config.use_rag is True  # Default value
        assert config.max_conversation_history == 10  # Default value

    def test_agent_config_custom_defaults(self):
        """Test AgentConfig with custom default values."""
        config = AgentConfig(
            name="test",
            display_name="Test",
            description="Test",
            model="test-model",
            temperature=0.5,
            rag_top_k=5,
            system_prompt="Test",
            use_rag=False,
            max_conversation_history=20,
        )

        assert config.use_rag is False
        assert config.max_conversation_history == 20

    def test_get_agent_service_returns_instance(self):
        """Test that get_agent_service returns an AgentService instance."""
        service = get_agent_service()

        assert isinstance(service, AgentService)

    def test_parse_agent_mention_with_special_characters(self):
        """Test parsing agent mention with special characters in query."""
        message = "@quick What's 2+2? Is it 4?"
        agent_name, cleaned = AgentService.parse_agent_mention(message)

        assert agent_name == "quick"
        assert cleaned == "What's 2+2? Is it 4?"

    def test_parse_agent_mention_with_newlines(self):
        """Test parsing agent mention with newlines in query."""
        message = "@deep What is\nthis?"
        agent_name, cleaned = AgentService.parse_agent_mention(message)

        assert agent_name == "deep"
        assert "is\nthis?" in cleaned

    def test_default_agent_has_balanced_params(self):
        """Test that default agent has balanced parameters."""
        config = AgentService.get_agent(None)

        # Default should be balanced
        assert config.temperature == 0.7  # Higher for creativity
        assert config.rag_top_k == 10  # Moderate context
        assert config.max_conversation_history == 10  # Moderate history
