"""
File Storage MCP Server

Safely accesses data files (CSV, Parquet, JSON, etc.) with size limits.
Enables data science agents to read and write data files.
"""
import asyncio
import json
import sys
import os
from typing import Any, Dict, List, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

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
    logging.warning("MCP SDK not available. File storage server features disabled.")


class FileStorageServer:
    """
    MCP server for file storage access.
    
    Features:
    - Read files (CSV, Parquet, JSON, etc.)
    - Write files (with approval)
    - List files
    - Size limits
    - Path restrictions
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize file storage server.
        
        Args:
            config: Configuration dict with:
                - allowed_paths: List of allowed directory paths
                - max_file_size_mb: Maximum file size in MB (default: 100)
                - read_only: Enforce read-only mode (default: True)
                - s3_bucket: S3 bucket name (optional)
                - s3_region: S3 region (optional)
        """
        if not MCP_AVAILABLE:
            logger.warning("MCP SDK not available. Server cannot run.")
            return
        
        self.config = config or {}
        self.allowed_paths = self.config.get("allowed_paths", ["/tmp/agent-data"])
        self.max_file_size_mb = self.config.get("max_file_size_mb", 100)
        self.max_file_size_bytes = self.max_file_size_mb * 1024 * 1024
        self.read_only = self.config.get("read_only", True)
        self.s3_bucket = self.config.get("s3_bucket")
        self.s3_region = self.config.get("s3_region", "us-east-1")
        
        # Initialize S3 client if configured
        self.s3_client = None
        if self.s3_bucket:
            try:
                import boto3
                self.s3_client = boto3.client('s3', region_name=self.s3_region)
            except ImportError:
                logger.warning("boto3 not available. S3 features disabled.")
        
        self.server = Server("file-storage")
        self._setup_tools()
        self._setup_handlers()
    
    def _is_path_allowed(self, file_path: str) -> bool:
        """Check if file path is in allowed directories"""
        path = Path(file_path).resolve()
        
        for allowed in self.allowed_paths:
            allowed_path = Path(allowed).resolve()
            try:
                path.relative_to(allowed_path)
                return True
            except ValueError:
                continue
        
        return False
    
    def _check_file_size(self, file_path: str) -> bool:
        """Check if file size is within limits"""
        try:
            size = os.path.getsize(file_path)
            return size <= self.max_file_size_bytes
        except:
            return False
    
    def _setup_tools(self):
        """Define available MCP tools"""
        if not MCP_AVAILABLE:
            return
        
        self.tools = [
            Tool(
                name="read_file",
                description="Read a file (text, JSON, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to file (local or s3://bucket/key)"
                        },
                        "encoding": {
                            "type": "string",
                            "description": "File encoding (default: utf-8)",
                            "default": "utf-8"
                        }
                    },
                    "required": ["file_path"]
                }
            ),
            Tool(
                name="read_csv",
                description="Read a CSV file into structured data",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to CSV file"
                        },
                        "n_rows": {
                            "type": "integer",
                            "description": "Number of rows to read (default: all)",
                            "default": None
                        },
                        "delimiter": {
                            "type": "string",
                            "description": "CSV delimiter (default: ,)",
                            "default": ","
                        }
                    },
                    "required": ["file_path"]
                }
            ),
            Tool(
                name="read_parquet",
                description="Read a Parquet file into structured data",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to Parquet file (local or s3://)"
                        },
                        "n_rows": {
                            "type": "integer",
                            "description": "Number of rows to read (default: all)",
                            "default": None
                        }
                    },
                    "required": ["file_path"]
                }
            ),
            Tool(
                name="list_files",
                description="List files in a directory or S3 bucket",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path or S3 prefix"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "File pattern (e.g., *.csv)"
                        }
                    },
                    "required": ["path"]
                }
            ),
            Tool(
                name="write_file",
                description="Write data to a file (requires approval if read_only)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to file"
                        },
                        "content": {
                            "type": "string",
                            "description": "File content"
                        },
                        "encoding": {
                            "type": "string",
                            "description": "File encoding (default: utf-8)",
                            "default": "utf-8"
                        }
                    },
                    "required": ["file_path", "content"]
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
            if name == "read_file":
                return await self._handle_read_file(arguments)
            elif name == "read_csv":
                return await self._handle_read_csv(arguments)
            elif name == "read_parquet":
                return await self._handle_read_parquet(arguments)
            elif name == "list_files":
                return await self._handle_list_files(arguments)
            elif name == "write_file":
                return await self._handle_write_file(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    def _is_s3_path(self, path: str) -> bool:
        """Check if path is S3 path"""
        return path.startswith("s3://")
    
    async def _handle_read_file(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Read a text file"""
        file_path = arguments.get("file_path")
        encoding = arguments.get("encoding", "utf-8")
        
        if not file_path:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "No file path provided"}, indent=2)
            )]
        
        try:
            if self._is_s3_path(file_path):
                # S3 read
                if not self.s3_client:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": "S3 not configured"}, indent=2)
                    )]
                
                # Parse s3://bucket/key
                parts = file_path.replace("s3://", "").split("/", 1)
                bucket = parts[0]
                key = parts[1] if len(parts) > 1 else ""
                
                response = self.s3_client.get_object(Bucket=bucket, Key=key)
                content = response['Body'].read().decode(encoding)
                
            else:
                # Local file read
                if not self._is_path_allowed(file_path):
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"Path not allowed: {file_path}"
                        }, indent=2)
                    )]
                
                if not self._check_file_size(file_path):
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"File too large (max: {self.max_file_size_mb}MB)"
                        }, indent=2)
                    )]
                
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "content": content,
                    "file_path": file_path,
                    "size_bytes": len(content.encode(encoding))
                }, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Error reading file: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "success": False
                }, indent=2)
            )]
    
    async def _handle_read_csv(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Read a CSV file"""
        file_path = arguments.get("file_path")
        n_rows = arguments.get("n_rows")
        delimiter = arguments.get("delimiter", ",")
        
        if not file_path:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "No file path provided"}, indent=2)
            )]
        
        try:
            import pandas as pd
            
            # Read CSV
            if n_rows:
                df = pd.read_csv(file_path, nrows=n_rows, delimiter=delimiter)
            else:
                df = pd.read_csv(file_path, delimiter=delimiter)
            
            # Convert to dict for JSON serialization
            result = {
                "success": True,
                "file_path": file_path,
                "row_count": len(df),
                "columns": list(df.columns),
                "data": df.head(1000).to_dict(orient='records'),  # Limit for JSON
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]
            
        except ImportError:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "pandas not available. Install with: pip install pandas"
                }, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error reading CSV: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "success": False
                }, indent=2)
            )]
    
    async def _handle_read_parquet(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Read a Parquet file"""
        file_path = arguments.get("file_path")
        n_rows = arguments.get("n_rows")
        
        if not file_path:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "No file path provided"}, indent=2)
            )]
        
        try:
            import pandas as pd
            
            # Read Parquet
            if n_rows:
                df = pd.read_parquet(file_path, nrows=n_rows)
            else:
                df = pd.read_parquet(file_path)
            
            # Convert to dict for JSON serialization
            result = {
                "success": True,
                "file_path": file_path,
                "row_count": len(df),
                "columns": list(df.columns),
                "data": df.head(1000).to_dict(orient='records'),  # Limit for JSON
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]
            
        except ImportError:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "pandas and pyarrow not available. Install with: pip install pandas pyarrow"
                }, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error reading Parquet: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "success": False
                }, indent=2)
            )]
    
    async def _handle_list_files(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """List files in directory"""
        path = arguments.get("path")
        pattern = arguments.get("pattern")
        
        if not path:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "No path provided"}, indent=2)
            )]
        
        try:
            if self._is_s3_path(path):
                # S3 list
                if not self.s3_client:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": "S3 not configured"}, indent=2)
                    )]
                
                parts = path.replace("s3://", "").split("/", 1)
                bucket = parts[0]
                prefix = parts[1] if len(parts) > 1 else ""
                
                response = self.s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
                files = [obj['Key'] for obj in response.get('Contents', [])]
                
            else:
                # Local list
                if not self._is_path_allowed(path):
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"Path not allowed: {path}"
                        }, indent=2)
                    )]
                
                path_obj = Path(path)
                if pattern:
                    files = [str(f) for f in path_obj.glob(pattern)]
                else:
                    files = [str(f) for f in path_obj.iterdir() if f.is_file()]
            
            result = {
                "success": True,
                "path": path,
                "files": files,
                "count": len(files)
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Error listing files: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "success": False
                }, indent=2)
            )]
    
    async def _handle_write_file(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Write data to file"""
        if self.read_only:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Write operations disabled. Read-only mode enabled."
                }, indent=2)
            )]
        
        file_path = arguments.get("file_path")
        content = arguments.get("content")
        encoding = arguments.get("encoding", "utf-8")
        
        if not file_path or content is None:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "File path and content required"}, indent=2)
            )]
        
        try:
            if self._is_s3_path(file_path):
                # S3 write
                if not self.s3_client:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": "S3 not configured"}, indent=2)
                    )]
                
                parts = file_path.replace("s3://", "").split("/", 1)
                bucket = parts[0]
                key = parts[1] if len(parts) > 1 else ""
                
                self.s3_client.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=content.encode(encoding)
                )
                
            else:
                # Local write
                if not self._is_path_allowed(file_path):
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"Path not allowed: {file_path}"
                        }, indent=2)
                    )]
                
                # Create directory if needed
                Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                
                with open(file_path, 'w', encoding=encoding) as f:
                    f.write(content)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "file_path": file_path,
                    "size_bytes": len(content.encode(encoding))
                }, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Error writing file: {e}", exc_info=True)
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
_file_storage_server_instance: Optional[FileStorageServer] = None


def get_file_storage_server(config: Optional[Dict[str, Any]] = None) -> FileStorageServer:
    """Get or create file storage server instance"""
    global _file_storage_server_instance
    
    if _file_storage_server_instance is None:
        _file_storage_server_instance = FileStorageServer(config)
    
    return _file_storage_server_instance


if __name__ == "__main__":
    # Run as standalone MCP server
    server = FileStorageServer()
    asyncio.run(server.run())

