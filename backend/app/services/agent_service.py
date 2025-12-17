"""
Agent service for specialized task-based AI assistants.

Provides different agents optimized for specific query types:
- @quick: Fast answers using lightweight model
- @deep: Comprehensive research using powerful model
- @code: Programming assistance with code-specialized model
- @summarize: Document summarization
"""
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for a specialized agent."""

    name: str
    display_name: str
    description: str
    model: str
    temperature: float
    rag_top_k: int
    system_prompt: str
    use_rag: bool = True
    max_conversation_history: int = 10
    # Tool-related configuration
    use_tools: bool = False
    tool_access_list: Optional[list[str]] = None  # None = all tools, [] = no tools
    max_tool_iterations: int = 5


# Core 4 Agent Configurations
AGENTS = {
    "quick": AgentConfig(
        name="quick",
        display_name="⚡ Quick",
        description="Lightning fast answers for simple questions",
        model="llama3.2:3b",
        temperature=0.3,
        rag_top_k=3,
        max_conversation_history=5,
        use_tools=False,  # Quick agent doesn't use tools for speed
        tool_access_list=[],
        system_prompt="""You are a quick-response assistant. Give concise, accurate answers.

Rules:
- Answer in 1-3 sentences max
- Be direct and to the point
- Skip explanations unless asked
- Use bullet points for lists
- Cite sources briefly if used

You prioritize speed and clarity over depth."""
    ),

    "deep": AgentConfig(
        name="deep",
        display_name="🔬 Deep",
        description="Comprehensive research and detailed explanations",
        model="qwen2.5:14b",
        temperature=0.5,
        rag_top_k=20,
        max_conversation_history=15,
        use_tools=True,  # Deep agent has access to all tools
        tool_access_list=None,  # None = all tools available
        max_tool_iterations=10,  # More iterations for deep research
        system_prompt="""You are a research assistant providing comprehensive, well-reasoned answers.

Rules:
- Provide thorough explanations with context
- Break down complex topics into clear sections
- Cite multiple sources when available
- Consider different perspectives
- Include relevant examples and connections
- Structure answers with headings when appropriate

You prioritize depth, accuracy, and comprehensive understanding."""
    ),

    "code": AgentConfig(
        name="code",
        display_name="💻 Code",
        description="Programming help with code examples",
        model="qwen2.5-coder:14b",
        temperature=0.2,
        rag_top_k=10,
        max_conversation_history=10,
        use_tools=True,  # Code agent can use code_executor, web_search, document_search
        tool_access_list=["code_executor", "web_search", "document_search"],
        max_tool_iterations=7,
        system_prompt="""You are a programming assistant. Help with code, debugging, and technical implementation.

Rules:
- Provide working code examples
- Explain what the code does
- Highlight best practices and potential issues
- Use proper syntax highlighting (markdown code blocks)
- Cite relevant documentation when available
- Be specific about language/framework versions if important

You prioritize correctness, clarity, and practical solutions."""
    ),

    "summarize": AgentConfig(
        name="summarize",
        display_name="📝 Summarize",
        description="Condense documents and extract key points",
        model="llama3.2:3b",
        temperature=0.4,
        rag_top_k=30,  # Get more context for summarization
        max_conversation_history=3,  # Less history needed
        use_tools=False,  # Summarize agent doesn't need tools
        tool_access_list=[],
        system_prompt="""You are a summarization assistant. Extract key information and create concise summaries.

Rules:
- Identify main themes and key points
- Use bullet points for clarity
- Preserve important details and numbers
- Organize by topic or chronology as appropriate
- Avoid redundancy
- Cite source documents when referencing specific info

You prioritize clarity and information density."""
    ),
}


class AgentService:
    """Service for managing and routing to specialized agents."""

    @staticmethod
    def parse_agent_mention(message: str) -> tuple[Optional[str], str]:
        """
        Parse agent mention from message.

        Args:
            message: User message (e.g., "@quick what is 2+2?")

        Returns:
            Tuple of (agent_name, cleaned_message)
        """
        message = message.strip()

        # Check if message starts with @
        if not message.startswith("@"):
            return None, message

        # Extract agent name (everything between @ and first space)
        parts = message.split(None, 1)
        if len(parts) < 2:
            # Just "@something" with no query
            return None, message

        agent_mention = parts[0][1:].lower()  # Remove @ and lowercase
        cleaned_message = parts[1].strip()

        # Validate agent exists
        if agent_mention in AGENTS:
            return agent_mention, cleaned_message

        # Invalid agent mention, treat as regular message
        return None, message

    @staticmethod
    def get_agent(agent_name: Optional[str]) -> AgentConfig:
        """
        Get agent configuration by name.

        Args:
            agent_name: Name of agent (or None for default)

        Returns:
            AgentConfig for the requested agent
        """
        if agent_name and agent_name in AGENTS:
            return AGENTS[agent_name]

        # Default agent (current behavior - balanced)
        return AgentConfig(
            name="default",
            display_name="💬 Default",
            description="Balanced conversational assistant",
            model="qwen2.5:14b",
            temperature=0.7,
            rag_top_k=10,
            max_conversation_history=10,
            system_prompt="""You are a helpful AI assistant for a personal knowledge management system.

Answer questions using conversation history and the user's documents.

Key rules:
- Check conversation history FIRST for context (e.g., "that", "it", pronouns, follow-ups)
- Answer directly without meta-commentary about your process
- Be conversational and concise - avoid robotic phrases like "I'll do my best", "Based on the provided context", "Additionally, reviewing"
- Only mention documents if they're actually relevant to the answer
- If knowledge base context is irrelevant, ignore it completely - don't explain why you're ignoring it
- Cite sources naturally when using specific info (e.g., "Your note on X mentions...")
- If you don't know something, just say "I don't have information about that"

CRITICAL: Users want answers, not explanations of how you're thinking. Be natural and direct."""
        )

    @staticmethod
    def list_available_agents() -> list[dict]:
        """
        List all available agents with their metadata.

        Returns:
            List of agent info dicts
        """
        return [
            {
                "name": config.name,
                "display_name": config.display_name,
                "description": config.description,
            }
            for config in AGENTS.values()
        ]


# Global instance
def get_agent_service() -> AgentService:
    """Get the agent service singleton."""
    return AgentService()
