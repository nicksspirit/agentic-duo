"""
Unit tests for ToolExecutor

Tests tool registration, execution, error handling, and session integration.
"""

import asyncio
import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, AsyncMock, patch
from google.genai.types import FunctionDeclaration

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tool_executor import ToolExecutor


# Test fixtures
@pytest.fixture
def tool_executor():
    """Create a ToolExecutor instance for testing."""
    return ToolExecutor(verbose=False)  # Disable verbose for clean test output


@pytest.fixture
def sample_tool():
    """Create a sample async tool function."""
    async def sample_func(message: str = "test"):
        """Sample tool for testing."""
        return f"Executed with: {message}"
    
    return sample_func


@pytest.fixture
def sample_declaration():
    """Create a sample FunctionDeclaration."""
    return FunctionDeclaration(
        name="sample_func",
        description="A sample test function"
    )


# Tests
@pytest.mark.asyncio
async def test_tool_executor_initialization():
    """Test that ToolExecutor initializes correctly."""
    executor = ToolExecutor(verbose=True)
    
    assert executor.verbose is True
    assert len(executor.tools) == 0
    assert len(executor.declarations) == 0


@pytest.mark.asyncio
async def test_register_tool(tool_executor, sample_tool, sample_declaration):
    """Test registering a tool."""
    tool_executor.register_tool("sample_func", sample_tool, sample_declaration)
    
    assert tool_executor.has_tool("sample_func")
    assert "sample_func" in tool_executor.list_tools()
    assert len(tool_executor.get_tool_declarations()) == 1


@pytest.mark.asyncio
async def test_register_duplicate_tool_raises_error(tool_executor, sample_tool, sample_declaration):
    """Test that registering a duplicate tool raises an error."""
    tool_executor.register_tool("sample_func", sample_tool, sample_declaration)
    
    with pytest.raises(ValueError, match="already registered"):
        tool_executor.register_tool("sample_func", sample_tool, sample_declaration)


@pytest.mark.asyncio
async def test_register_non_async_tool_raises_error(tool_executor, sample_declaration):
    """Test that registering a non-async function raises an error."""
    def sync_func():
        return "sync"
    
    with pytest.raises(ValueError, match="must be an async function"):
        tool_executor.register_tool("sync_func", sync_func, sample_declaration)


@pytest.mark.asyncio
async def test_execute_tool_success(tool_executor, sample_tool, sample_declaration):
    """Test executing a registered tool successfully."""
    tool_executor.register_tool("sample_func", sample_tool, sample_declaration)
    
    response = await tool_executor.execute_tool(
        function_name="sample_func",
        function_id="test_id_123",
        args={"message": "hello"}
    )
    
    assert response.id == "test_id_123"
    assert response.name == "sample_func"
    assert response.response["result"] == "success"
    assert "Executed with: hello" in str(response.response["data"])


@pytest.mark.asyncio
async def test_execute_unknown_tool(tool_executor):
    """Test executing a tool that doesn't exist."""
    response = await tool_executor.execute_tool(
        function_name="unknown_tool",
        function_id="test_id_456",
        args={}
    )
    
    assert response.id == "test_id_456"
    assert response.name == "unknown_tool"
    assert response.response["result"] == "error: unknown function"


@pytest.mark.asyncio
async def test_execute_tool_with_error(tool_executor, sample_declaration):
    """Test executing a tool that raises an exception."""
    async def error_tool():
        raise ValueError("Intentional error")
    
    tool_executor.register_tool("error_tool", error_tool, sample_declaration)
    
    response = await tool_executor.execute_tool(
        function_name="error_tool",
        function_id="test_id_789",
        args={}
    )
    
    assert response.id == "test_id_789"
    assert response.response["result"] == "error"
    assert "Intentional error" in response.response["error"]


@pytest.mark.asyncio
async def test_list_tools(tool_executor, sample_tool, sample_declaration):
    """Test listing registered tools."""
    async def tool1():
        return "tool1"
    
    async def tool2():
        return "tool2"
    
    decl1 = FunctionDeclaration(name="tool1", description="First tool")
    decl2 = FunctionDeclaration(name="tool2", description="Second tool")
    
    tool_executor.register_tool("tool1", tool1, decl1)
    tool_executor.register_tool("tool2", tool2, decl2)
    
    tools = tool_executor.list_tools()
    assert len(tools) == 2
    assert "tool1" in tools
    assert "tool2" in tools


@pytest.mark.asyncio
async def test_has_tool(tool_executor, sample_tool, sample_declaration):
    """Test checking if a tool exists."""
    assert not tool_executor.has_tool("sample_func")
    
    tool_executor.register_tool("sample_func", sample_tool, sample_declaration)
    
    assert tool_executor.has_tool("sample_func")
    assert not tool_executor.has_tool("nonexistent_tool")


@pytest.mark.asyncio
async def test_get_tool_declarations(tool_executor, sample_tool):
    """Test getting all tool declarations."""
    decl1 = FunctionDeclaration(name="tool1", description="First")
    decl2 = FunctionDeclaration(name="tool2", description="Second")
    
    async def tool1():
        return "1"
    async def tool2():
        return "2"
    
    tool_executor.register_tool("tool1", tool1, decl1)
    tool_executor.register_tool("tool2", tool2, decl2)
    
    declarations = tool_executor.get_tool_declarations()
    assert len(declarations) == 2
    assert all(isinstance(d, FunctionDeclaration) for d in declarations)
