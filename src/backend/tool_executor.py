"""
Tool Executor Module

Handles tool registration and execution for the Gemini Live API.
Extracted from intent_client.py for reusability across the application.

This module provides:
- Tool registration system with function declarations
- Tool execution with error handling
- Function response generation for Gemini sessions
"""

import asyncio
import sys
from typing import Callable, Dict, Optional, Any
from google.genai.types import FunctionDeclaration, FunctionResponse
from google import genai


class ToolExecutor:
    """
    Manages tool registration and execution for Gemini function calling.
    
    Provides a registry-based approach to register Python functions as tools,
    execute them when called by Gemini, and generate appropriate responses.
    """
    
    def __init__(self, verbose: bool = True):
        """
        Initialize the tool executor.
        
        Args:
            verbose: If True, print execution logs to console
        """
        self.tools: Dict[str, Callable] = {}
        self.declarations: Dict[str, FunctionDeclaration] = {}
        self.verbose = verbose
    
    def register_tool(
        self, 
        name: str, 
        func: Callable, 
        declaration: FunctionDeclaration
    ) -> None:
        """
        Register a tool with its function and declaration.
        
        Args:
            name: The unique name of the tool (must match function name)
            func: The async function to execute when tool is called
            declaration: FunctionDeclaration object for Gemini API
        
        Raises:
            ValueError: If tool name is already registered
        """
        if name in self.tools:
            raise ValueError(f"Tool '{name}' is already registered")
        
        if not asyncio.iscoroutinefunction(func):
            raise ValueError(f"Tool '{name}' must be an async function")
        
        self.tools[name] = func
        self.declarations[name] = declaration
        
        if self.verbose:
            print(f"Registered tool: {name}")
    
    def get_tool_declarations(self) -> list[FunctionDeclaration]:
        """
        Get all registered tool declarations for Gemini API configuration.
        
        Returns:
            List of FunctionDeclaration objects
        """
        return list(self.declarations.values())
    
    async def execute_tool(
        self, 
        function_name: str, 
        function_id: str,
        args: Optional[Dict[str, Any]] = None
    ) -> FunctionResponse:
        """
        Execute a registered tool and return a FunctionResponse.
        
        Args:
            function_name: Name of the tool to execute
            function_id: Unique ID for this function call (from Gemini)
            args: Optional dict of function arguments
            
        Returns:
            FunctionResponse object to send back to Gemini
        """
        if args is None:
            args = {}
        
        if function_name not in self.tools:
            error_msg = f"Unknown function: {function_name}"
            if self.verbose:
                print(f"[ERROR] {error_msg}", file=sys.stderr)
            
            return FunctionResponse(
                id=function_id,
                name=function_name,
                response={"result": "error: unknown function", "error": error_msg}
            )
        
        # Execute the tool function
        try:
            if self.verbose:
                print(f"\n[EXECUTING] {function_name}(args={args})")
            
            # Call the function with unpacked args
            result = await self.tools[function_name](**args)
            
            if self.verbose:
                print(f"[SUCCESS] {function_name} completed")
            
            # Return success response
            return FunctionResponse(
                id=function_id,
                name=function_name,
               response={"result": "success", "data": result}
            )
            
        except Exception as e:
            error_msg = f"Error executing function {function_name}: {e}"
            if self.verbose:
                print(f"[ERROR] {error_msg}", file=sys.stderr)
                import traceback
                traceback.print_exc()
            
            return FunctionResponse(
                id=function_id,
                name=function_name,
                response={"result": "error", "error": str(e)}
            )
    
    async def handle_tool_calls(self, session: Any) -> None:
        """
        Monitor Gemini session for tool calls and execute them.
        
        This is a long-running coroutine that should be run as a task.
        It continuously listens for tool call responses from Gemini and executes
        the corresponding tools.
        
        Args:
            session: Active Gemini Live API session
        """
        from google.genai import types
        
        try:
            while True:
                try:
                    turn = session.receive()
                    async for response in turn:
                        # Check for tool calls
                        if hasattr(response, 'tool_call') and response.tool_call:
                            if self.verbose:
                                print(f"\n[TOOL_CALL DETECTED]")
                            
                            # Process each function call
                            function_responses = []
                            if hasattr(response.tool_call, 'function_calls'):
                                for fc in response.tool_call.function_calls:
                                    function_name = fc.name
                                    function_id = fc.id
                                    
                                    # Extract arguments if present
                                    args = {}
                                    if hasattr(fc, 'args') and fc.args:
                                        args = dict(fc.args)
                                    
                                    if self.verbose:
                                        print(f"[INTENT DETECTED] Function: {function_name} (ID: {function_id})")
                                    
                                    # Execute the tool
                                    func_response = await self.execute_tool(
                                        function_name, 
                                        function_id,
                                        args
                                    )
                                    function_responses.append(func_response)
                            
                            # Send responses back to session
                            if function_responses:
                                await session.send_tool_response(function_responses=function_responses)
                                if self.verbose:
                                    print(f"[SENT {len(function_responses)} FUNCTION RESPONSE(S) BACK TO SESSION]")
                        
                except Exception as e:
                    if self.verbose:
                        print(f"Error in handle_tool_calls: {e}", file=sys.stderr)
                        import traceback
                        traceback.print_exc()
                    await asyncio.sleep(0.1)
                    continue
                    
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"Fatal error in handle_tool_calls: {e}", file=sys.stderr, flush=True)
            raise
    
    def list_tools(self) -> list[str]:
        """
        List all registered tool names.
        
        Returns:
            List of tool names
        """
        return list(self.tools.keys())
    
    def has_tool(self, name: str) -> bool:
        """
        Check if a tool is registered.
        
        Args:
            name: Tool name to check
            
        Returns:
            True if tool is registered, False otherwise
        """
        return name in self.tools


# Convenience function for creating a ToolExecutor
def create_tool_executor(verbose: bool = True) -> ToolExecutor:
    """
    Factory function to create and return a ToolExecutor instance.
    
    Args:
        verbose: If True, print execution logs to console
        
    Returns:
        Configured ToolExecutor instance
    """
    return ToolExecutor(verbose=verbose)
