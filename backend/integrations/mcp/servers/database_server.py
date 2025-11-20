"""
Database Access MCP Server

Safely executes SQL queries with read-only access and resource limits.
Enables data science agents to access databases for analysis.
"""
import asyncio
import json
import sys
import os
from typing import Any, Dict, List, Optional
import logging
from urllib.parse import quote_plus

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
    logging.warning("MCP SDK not available. Database server features disabled.")

try:
    from sqlalchemy import create_engine, text, inspect
    from sqlalchemy.pool import QueuePool
    from sqlalchemy.exc import SQLAlchemyError
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning("SQLAlchemy not available. Database features disabled.")


class DatabaseServer:
    """
    MCP server for database access.
    
    Features:
    - Read-only SQL queries
    - Query timeout protection
    - Row limits
    - Schema inspection
    - Connection pooling
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize database server.
        
        Args:
            config: Configuration dict with:
                - database_url: Database connection string
                - query_timeout: Query timeout in seconds (default: 30)
                - max_rows: Maximum rows to return (default: 10000)
                - read_only: Enforce read-only mode (default: True)
                - max_connections: Max connection pool size (default: 5)
        """
        if not MCP_AVAILABLE:
            logger.warning("MCP SDK not available. Server cannot run.")
            return
        
        if not SQLALCHEMY_AVAILABLE:
            logger.warning("SQLAlchemy not available. Server cannot run.")
            return
        
        self.config = config or {}
        self.database_url = self.config.get("database_url") or os.environ.get("DATABASE_URL")
        self.query_timeout = self.config.get("query_timeout", 30)
        self.max_rows = self.config.get("max_rows", 10000)
        self.read_only = self.config.get("read_only", True)
        self.max_connections = self.config.get("max_connections", 5)
        
        if not self.database_url:
            logger.warning("No database URL provided. Database server will not function.")
            self.engine = None
        else:
            # Create engine with connection pooling
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=self.max_connections,
                max_overflow=2,
                pool_pre_ping=True,  # Verify connections before using
                echo=False
            )
        
        self.server = Server("database")
        self._setup_tools()
        self._setup_handlers()
    
    def _setup_tools(self):
        """Define available MCP tools"""
        if not MCP_AVAILABLE:
            return
        
        self.tools = [
            Tool(
                name="execute_query",
                description="Execute a SELECT SQL query (read-only)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SQL SELECT query"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Query timeout in seconds (default: 30)",
                            "default": 30
                        },
                        "max_rows": {
                            "type": "integer",
                            "description": "Maximum rows to return (default: 10000)",
                            "default": 10000
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_schema",
                description="Get schema information for a table",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table"
                        },
                        "schema": {
                            "type": "string",
                            "description": "Schema name (optional)"
                        }
                    },
                    "required": ["table_name"]
                }
            ),
            Tool(
                name="list_tables",
                description="List all tables in the database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "schema": {
                            "type": "string",
                            "description": "Schema name (optional)"
                        }
                    }
                }
            ),
            Tool(
                name="get_table_sample",
                description="Get sample rows from a table",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of rows (default: 10)",
                            "default": 10
                        },
                        "schema": {
                            "type": "string",
                            "description": "Schema name (optional)"
                        }
                    },
                    "required": ["table_name"]
                }
            ),
            Tool(
                name="describe_table",
                description="Get detailed table metadata",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table"
                        },
                        "schema": {
                            "type": "string",
                            "description": "Schema name (optional)"
                        }
                    },
                    "required": ["table_name"]
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
            if name == "execute_query":
                return await self._handle_execute_query(arguments)
            elif name == "get_schema":
                return await self._handle_get_schema(arguments)
            elif name == "list_tables":
                return await self._handle_list_tables(arguments)
            elif name == "get_table_sample":
                return await self._handle_get_table_sample(arguments)
            elif name == "describe_table":
                return await self._handle_describe_table(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    def _validate_query(self, query: str) -> bool:
        """Validate that query is read-only"""
        if not self.read_only:
            return True
        
        query_upper = query.strip().upper()
        
        # Check for dangerous operations
        dangerous_keywords = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
            'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return False
        
        # Must start with SELECT
        if not query_upper.startswith('SELECT'):
            return False
        
        return True
    
    async def _handle_execute_query(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute a SQL query"""
        if not self.engine:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "Database not configured"}, indent=2)
            )]
        
        query = arguments.get("query", "").strip()
        timeout = arguments.get("timeout", self.query_timeout)
        max_rows = arguments.get("max_rows", self.max_rows)
        
        if not query:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "No query provided"}, indent=2)
            )]
        
        # Validate query
        if not self._validate_query(query):
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Query contains non-SELECT operations. Read-only mode enforced."
                }, indent=2)
            )]
        
        try:
            # Add LIMIT if not present and query might return many rows
            # (Simple check - in production, use SQL parser)
            if "LIMIT" not in query.upper() and max_rows:
                query = f"{query.rstrip(';')} LIMIT {max_rows + 1}"
            
            # Execute query with timeout
            async with asyncio.timeout(timeout):
                with self.engine.connect() as conn:
                    result = conn.execute(text(query))
                    rows = result.fetchall()
                    
                    # Check if we hit the limit
                    truncated = len(rows) > max_rows
                    if truncated:
                        rows = rows[:max_rows]
                    
                    # Convert to list of dicts
                    columns = result.keys()
                    data = [dict(zip(columns, row)) for row in rows]
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "rows": data,
                            "row_count": len(data),
                            "truncated": truncated,
                            "columns": list(columns)
                        }, indent=2, default=str)
                    )]
                    
        except asyncio.TimeoutError:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Query timeout after {timeout} seconds",
                    "success": False
                }, indent=2)
            )]
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "success": False
                }, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error executing query: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "success": False
                }, indent=2)
            )]
    
    async def _handle_get_schema(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get table schema"""
        if not self.engine:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "Database not configured"}, indent=2)
            )]
        
        table_name = arguments.get("table_name")
        schema = arguments.get("schema")
        
        if not table_name:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "No table name provided"}, indent=2)
            )]
        
        try:
            inspector = inspect(self.engine)
            
            # Get columns
            columns = inspector.get_columns(table_name, schema=schema)
            
            # Get primary keys
            pk_constraint = inspector.get_pk_constraint(table_name, schema=schema)
            primary_keys = pk_constraint.get('constrained_columns', [])
            
            # Get foreign keys
            foreign_keys = inspector.get_foreign_keys(table_name, schema=schema)
            
            # Get indexes
            indexes = inspector.get_indexes(table_name, schema=schema)
            
            result = {
                "table_name": table_name,
                "schema": schema,
                "columns": [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col.get("nullable", True),
                        "default": str(col.get("default")) if col.get("default") else None
                    }
                    for col in columns
                ],
                "primary_keys": primary_keys,
                "foreign_keys": foreign_keys,
                "indexes": [{"name": idx["name"], "columns": idx["column_names"]} for idx in indexes]
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]
            
        except Exception as e:
            logger.error(f"Error getting schema: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "success": False
                }, indent=2)
            )]
    
    async def _handle_list_tables(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """List all tables"""
        if not self.engine:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "Database not configured"}, indent=2)
            )]
        
        schema = arguments.get("schema")
        
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names(schema=schema)
            
            result = {
                "tables": tables,
                "count": len(tables),
                "schema": schema
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Error listing tables: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "success": False
                }, indent=2)
            )]
    
    async def _handle_get_table_sample(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get sample rows from table"""
        if not self.engine:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "Database not configured"}, indent=2)
            )]
        
        table_name = arguments.get("table_name")
        limit = arguments.get("limit", 10)
        schema = arguments.get("schema")
        
        if not table_name:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "No table name provided"}, indent=2)
            )]
        
        try:
            # Build query
            if schema:
                full_table_name = f"{schema}.{table_name}"
            else:
                full_table_name = table_name
            
            query = f"SELECT * FROM {full_table_name} LIMIT {limit}"
            
            # Use execute_query handler
            return await self._handle_execute_query({
                "query": query,
                "timeout": self.query_timeout,
                "max_rows": limit
            })
            
        except Exception as e:
            logger.error(f"Error getting table sample: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "success": False
                }, indent=2)
            )]
    
    async def _handle_describe_table(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get detailed table metadata"""
        # This is similar to get_schema but with more details
        return await self._handle_get_schema(arguments)
    
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
_database_server_instance: Optional[DatabaseServer] = None


def get_database_server(config: Optional[Dict[str, Any]] = None) -> DatabaseServer:
    """Get or create database server instance"""
    global _database_server_instance
    
    if _database_server_instance is None:
        _database_server_instance = DatabaseServer(config)
    
    return _database_server_instance


if __name__ == "__main__":
    # Run as standalone MCP server
    import os
    config = {
        "database_url": os.environ.get("DATABASE_URL")
    }
    server = DatabaseServer(config)
    asyncio.run(server.run())

