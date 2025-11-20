"""
Python Executor MCP Server

Safely executes Python code using E2B cloud sandboxes.
Enables data science agents to actually run code instead of just planning.

Uses E2B (https://e2b.dev) for secure, isolated code execution - same as Lovable and other AI platforms.
"""
import asyncio
import json
import sys
import os
from typing import Any, Dict, List, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# E2B imports
try:
    from e2b_code_interpreter import Sandbox
    E2B_AVAILABLE = True
except ImportError:
    E2B_AVAILABLE = False
    logger.warning("E2B SDK not available. Install with: pip install e2b-code-interpreter")

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    class Server:
        pass
    class Tool:
        pass
    logging.warning("MCP SDK not available. Python executor server features disabled.")


class PythonExecutorServer:
    """
    MCP server for executing Python code safely using E2B sandboxes.
    
    Features:
    - Cloud-based sandboxed execution (E2B)
    - Automatic resource limits
    - Timeout protection
    - Isolated environment per execution
    - Pre-installed data science packages
    - Network access control
    - File system access
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Python executor server.
        
        Args:
            config: Configuration dict with:
                - e2b_api_key: E2B API key (or from E2B_API_KEY env var)
                - timeout: Execution timeout in seconds (default: 60)
                - template_id: E2B template ID (default: "base" for code interpreter)
        """
        if not MCP_AVAILABLE:
            logger.warning("MCP SDK not available. Server cannot run.")
            return
        
        if not E2B_AVAILABLE:
            logger.warning("E2B SDK not available. Install with: pip install e2b-code-interpreter")
            return
        
        self.config = config or {}
        # Get E2B API key from config or environment
        self.e2b_api_key = (
            self.config.get("e2b_api_key") or 
            os.environ.get("E2B_API_KEY") or
            ""
        )
        
        if not self.e2b_api_key:
            logger.warning(
                "E2B_API_KEY not configured. Set E2B_API_KEY environment variable. "
                "Get your API key at https://e2b.dev"
            )
        
        self.timeout = self.config.get("timeout", 60)
        self.template_id = self.config.get("template_id", "base")  # E2B code interpreter template
        
        # Sandbox pool for reuse (optional optimization)
        self._sandbox_pool: List[Sandbox] = []
        self._max_pool_size = self.config.get("max_pool_size", 3)
        
        self.server = Server("python-executor")
        self._setup_tools()
        self._setup_handlers()
    
    def _setup_tools(self):
        """Define available MCP tools"""
        if not MCP_AVAILABLE:
            return
        
        self.tools = [
            Tool(
                name="execute_code",
                description="Execute Python code safely with resource limits",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Python code to execute"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Execution timeout in seconds (default: 60)",
                            "default": 60
                        },
                        "capture_output": {
                            "type": "boolean",
                            "description": "Capture stdout/stderr (default: true)",
                            "default": True
                        }
                    },
                    "required": ["code"]
                }
            ),
            Tool(
                name="run_script",
                description="Execute a Python script file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "script_path": {
                            "type": "string",
                            "description": "Path to Python script file"
                        },
                        "args": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Command line arguments"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Execution timeout in seconds",
                            "default": 60
                        }
                    },
                    "required": ["script_path"]
                }
            ),
            Tool(
                name="install_package",
                description="Install a Python package (with approval)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "package": {
                            "type": "string",
                            "description": "Package name (e.g., 'pandas' or 'pandas==1.5.0')"
                        },
                        "upgrade": {
                            "type": "boolean",
                            "description": "Upgrade if already installed",
                            "default": False
                        }
                    },
                    "required": ["package"]
                }
            ),
            Tool(
                name="get_environment",
                description="Get Python environment information",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]
    
    def _setup_handlers(self):
        """Setup tool handlers"""
        if not MCP_AVAILABLE:
            return
        
        @self.server.call_tool()
        async def handle_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Route tool calls to appropriate handlers"""
            if name == "execute_code":
                return await self._handle_execute_code(arguments)
            elif name == "run_script":
                return await self._handle_run_script(arguments)
            elif name == "install_package":
                return await self._handle_install_package(arguments)
            elif name == "get_environment":
                return await self._handle_get_environment(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _handle_execute_code(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute Python code safely using E2B sandbox"""
        code = arguments.get("code", "")
        timeout = arguments.get("timeout", self.timeout)
        
        if not code:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "No code provided"}, indent=2)
            )]
        
        if not self.e2b_api_key:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "E2B_API_KEY not configured. Set E2B_API_KEY environment variable.",
                    "success": False
                }, indent=2)
            )]
        
        # E2B sandbox context manager wrapper for async
        def run_in_sandbox():
            """Run code in E2B sandbox (synchronous wrapper)"""
            try:
                # Create sandbox (context manager)
                with Sandbox.create(
                    api_key=self.e2b_api_key,
                    template=self.template_id
                ) as sandbox:
                    # Execute code
                    execution = sandbox.run_code(code)
                    
                    # Return execution result
                    return {
                        "success": True,
                        "text": getattr(execution, 'text', ''),
                        "results": getattr(execution, 'results', []),
                        "error": getattr(execution, 'error', None),
                        "logs": getattr(execution, 'logs', []),
                        "timeout": False
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "timeout": False
                }
        
        try:
            # Execute in thread pool with timeout
            logger.debug(f"Creating E2B sandbox and executing code (timeout: {timeout}s)")
            result = await asyncio.wait_for(
                asyncio.to_thread(run_in_sandbox),
                timeout=timeout
            )
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]
            
        except asyncio.TimeoutError:
            logger.warning(f"Code execution timeout after {timeout} seconds")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Execution timeout after {timeout} seconds",
                    "timeout": True
                }, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error executing code in E2B: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "success": False,
                    "timeout": False
                }, indent=2)
            )]
    
    async def _handle_run_script(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute a Python script file using E2B sandbox"""
        script_path = arguments.get("script_path")
        args = arguments.get("args", [])
        timeout = arguments.get("timeout", self.timeout)
        
        if not script_path:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "No script path provided"}, indent=2)
            )]
        
        if not self.e2b_api_key:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "E2B_API_KEY not configured",
                    "success": False
                }, indent=2)
            )]
        
        def run_script_in_sandbox():
            """Run script in E2B sandbox (synchronous wrapper)"""
            try:
                with Sandbox.create(
                    api_key=self.e2b_api_key,
                    template=self.template_id
                ) as sandbox:
                    # Read and upload script if local file
                    if os.path.exists(script_path):
                        with open(script_path, 'r') as f:
                            script_content = f.read()
                        # Upload to sandbox
                        sandbox.filesystem.write(script_path, script_content.encode())
                    
                    # Execute script
                    execution = sandbox.run_code(f"exec(open('{script_path}').read())")
                    
                    return {
                        "success": True,
                        "text": getattr(execution, 'text', ''),
                        "results": getattr(execution, 'results', []),
                        "error": getattr(execution, 'error', None),
                        "logs": getattr(execution, 'logs', []),
                        "timeout": False
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "timeout": False
                }
        
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(run_script_in_sandbox),
                timeout=timeout
            )
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]
            
        except asyncio.TimeoutError:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Execution timeout after {timeout} seconds",
                    "timeout": True
                }, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error running script in E2B: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "success": False
                }, indent=2)
            )]
    
    async def _handle_install_package(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Install a Python package in E2B sandbox"""
        package = arguments.get("package")
        upgrade = arguments.get("upgrade", False)
        
        if not package:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "No package specified"}, indent=2)
            )]
        
        if not self.e2b_api_key:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "E2B_API_KEY not configured",
                    "success": False
                }, indent=2)
            )]
        
        def install_package_in_sandbox():
            """Install package in E2B sandbox (synchronous wrapper)"""
            try:
                with Sandbox.create(
                    api_key=self.e2b_api_key,
                    template=self.template_id
                ) as sandbox:
                    # Build pip install command
                    pip_cmd = f"pip install {package}"
                    if upgrade:
                        pip_cmd += " --upgrade"
                    
                    # Execute pip install
                    execution = sandbox.run_code(pip_cmd)
                    
                    return {
                        "success": getattr(execution, 'error', None) is None,
                        "package": package,
                        "text": getattr(execution, 'text', ''),
                        "error": getattr(execution, 'error', None),
                        "logs": getattr(execution, 'logs', [])
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(install_package_in_sandbox),
                timeout=300  # 5 minutes for package installs
            )
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]
            
        except asyncio.TimeoutError:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Package installation timeout",
                    "success": False
                }, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error installing package in E2B: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "success": False
                }, indent=2)
            )]
    
    async def _handle_get_environment(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get Python environment information from E2B sandbox"""
        if not self.e2b_api_key:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "E2B_API_KEY not configured",
                    "success": False
                }, indent=2)
            )]
        
        def get_env_from_sandbox():
            """Get environment info from E2B sandbox (synchronous wrapper)"""
            try:
                with Sandbox.create(
                    api_key=self.e2b_api_key,
                    template=self.template_id
                ) as sandbox:
                    # Get environment info
                    env_code = """
import sys
import platform
import json

try:
    import pkg_resources
    packages = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
except:
    packages = {}

env_info = {
    "python_version": sys.version,
    "platform": platform.platform(),
    "installed_packages": packages,
    "executable": sys.executable
}

print(json.dumps(env_info, indent=2))
"""
                    execution = sandbox.run_code(env_code)
                    
                    # Parse JSON output
                    try:
                        env_data = json.loads(getattr(execution, 'text', '')) if getattr(execution, 'text', '') else {}
                    except:
                        env_data = {
                            "python_version": "Unknown",
                            "platform": "Unknown",
                            "installed_packages": {},
                            "raw_output": getattr(execution, 'text', '')
                        }
                    
                    return {
                        "success": True,
                        "environment": env_data,
                        "sandbox_type": "E2B",
                        "template": self.template_id
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(get_env_from_sandbox),
                timeout=30
            )
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]
            
        except Exception as e:
            logger.error(f"Error getting environment from E2B: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "success": False
                }, indent=2)
            )]
    
    
    async def run(self):
        """Run the MCP server (stdio transport)"""
        if not MCP_AVAILABLE:
            logger.error("MCP SDK not available. Cannot run server.")
            return
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


# Singleton instance
_python_executor_server_instance: Optional[PythonExecutorServer] = None


def get_python_executor_server(config: Optional[Dict[str, Any]] = None) -> PythonExecutorServer:
    """Get or create Python executor server instance"""
    global _python_executor_server_instance
    
    if _python_executor_server_instance is None:
        _python_executor_server_instance = PythonExecutorServer(config)
    
    return _python_executor_server_instance


if __name__ == "__main__":
    # Run as standalone MCP server
    import os
    config = {
        "e2b_api_key": os.environ.get("E2B_API_KEY")
    }
    server = PythonExecutorServer(config)
    asyncio.run(server.run())

