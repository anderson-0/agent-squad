"""
Agent-Squad MCP Server (Stream J)

MCP server that exposes Agent-Squad capabilities as tools.

This allows external systems (like Claude Code) to interact with
Agent-Squad workflows via the Model Context Protocol.
"""
import asyncio
import json
import sys
from typing import Any, Dict, List, Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Create mock types for development
    class Server:
        pass
    class Tool:
        pass
    logging.warning("MCP SDK not available. MCP server features disabled.")



class AgentSquadMCPServer:
    """
    MCP server exposing Agent-Squad capabilities.
    
    Tools available:
    - spawn_task: Spawn a new dynamic task
    - check_workflow_health: Get workflow health metrics
    - get_coherence_score: Get agent coherence score
    - create_workflow_branch: Create a workflow branch from discovery
    - discover_opportunities: Run discovery analysis
    - get_kanban_board: Get Kanban board state
    """
    
    def __init__(self):
        """Initialize Agent-Squad MCP server"""
        if not MCP_AVAILABLE:
            logger.warning("MCP SDK not available. Server cannot run.")
            return
        
        self.server = Server("agent-squad")
        self._setup_tools()
        self._setup_handlers()
    
    def _setup_tools(self):
        """Define available MCP tools"""
        if not MCP_AVAILABLE:
            return
        
        self.tools = [
            Tool(
                name="spawn_task",
                description="Spawn a new dynamic task in a workflow",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "execution_id": {"type": "string", "description": "Task execution ID"},
                        "agent_id": {"type": "string", "description": "Agent ID spawning the task"},
                        "phase": {"type": "string", "enum": ["investigation", "building", "validation"]},
                        "title": {"type": "string", "description": "Task title"},
                        "description": {"type": "string", "description": "Task description"},
                        "rationale": {"type": "string", "description": "Why this task was created"},
                        "blocking_task_ids": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["execution_id", "agent_id", "phase", "title", "description"],
                },
            ),
            Tool(
                name="check_workflow_health",
                description="Check workflow health metrics",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "execution_id": {"type": "string", "description": "Task execution ID"},
                    },
                    "required": ["execution_id"],
                },
            ),
            Tool(
                name="get_coherence_score",
                description="Get agent coherence score from PM Guardian",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "execution_id": {"type": "string", "description": "Task execution ID"},
                        "agent_id": {"type": "string", "description": "Agent ID"},
                        "phase": {"type": "string", "enum": ["investigation", "building", "validation"]},
                    },
                    "required": ["execution_id", "agent_id", "phase"],
                },
            ),
            Tool(
                name="create_workflow_branch",
                description="Create a workflow branch from a discovery",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "execution_id": {"type": "string", "description": "Task execution ID"},
                        "branch_name": {"type": "string", "description": "Branch name"},
                        "discovery_id": {"type": "string", "description": "Discovery ID"},
                        "initial_task_title": {"type": "string"},
                        "initial_task_description": {"type": "string"},
                        "agent_id": {"type": "string"},
                    },
                    "required": ["execution_id", "branch_name", "agent_id", "initial_task_title", "initial_task_description"],
                },
            ),
            Tool(
                name="discover_opportunities",
                description="Run discovery analysis for opportunities",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "execution_id": {"type": "string", "description": "Task execution ID"},
                        "agent_id": {"type": "string", "description": "Agent ID"},
                        "phase": {"type": "string", "enum": ["investigation", "building", "validation"]},
                    },
                    "required": ["execution_id", "agent_id", "phase"],
                },
            ),
            Tool(
                name="get_kanban_board",
                description="Get Kanban board state for a workflow",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "execution_id": {"type": "string", "description": "Task execution ID"},
                    },
                    "required": ["execution_id"],
                },
            ),
        ]
    
    def _setup_handlers(self):
        """Setup tool handlers"""
        if not MCP_AVAILABLE:
            return
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools"""
            return self.tools
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            try:
                if name == "spawn_task":
                    return await self._handle_spawn_task(arguments)
                elif name == "check_workflow_health":
                    return await self._handle_check_workflow_health(arguments)
                elif name == "get_coherence_score":
                    return await self._handle_get_coherence_score(arguments)
                elif name == "create_workflow_branch":
                    return await self._handle_create_workflow_branch(arguments)
                elif name == "discover_opportunities":
                    return await self._handle_discover_opportunities(arguments)
                elif name == "get_kanban_board":
                    return await self._handle_get_kanban_board(arguments)
                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": f"Unknown tool: {name}"}),
                    )]
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}", exc_info=True)
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)}),
                )]
    
    async def _handle_spawn_task(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle spawn_task tool call"""
        from backend.models.workflow import WorkflowPhase
        from backend.agents.task_spawning import get_agent_task_spawner
        from backend.core.database import get_async_session
        
        execution_id = UUID(arguments["execution_id"])
        agent_id = UUID(arguments["agent_id"])
        phase = WorkflowPhase(arguments["phase"])
        title = arguments["title"]
        description = arguments["description"]
        rationale = arguments.get("rationale")
        blocking_task_ids = [
            UUID(tid) for tid in arguments.get("blocking_task_ids", [])
        ]
        
        # Get database session using context manager
        from backend.core.database import get_db_context
        
        async with get_db_context() as db:
            spawner = get_agent_task_spawner()
            
            if phase == WorkflowPhase.INVESTIGATION:
                task = await spawner.spawn_investigation_task(
                    db=db,
                    execution_id=execution_id,
                    agent_id=agent_id,
                    title=title,
                    description=description,
                    rationale=rationale,
                    blocking_task_ids=blocking_task_ids,
                )
            elif phase == WorkflowPhase.BUILDING:
                task = await spawner.spawn_building_task(
                    db=db,
                    execution_id=execution_id,
                    agent_id=agent_id,
                    title=title,
                    description=description,
                    rationale=rationale,
                    blocking_task_ids=blocking_task_ids,
                )
            else:  # VALIDATION
                task = await spawner.spawn_validation_task(
                    db=db,
                    execution_id=execution_id,
                    agent_id=agent_id,
                    title=title,
                    description=description,
                    rationale=rationale,
                    blocking_task_ids=blocking_task_ids,
                )
            
            result = {
                "task_id": str(task.id),
                "title": task.title,
                "phase": task.phase,
                "status": task.status,
                "created_at": task.created_at.isoformat(),
            }
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    async def _handle_check_workflow_health(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle check_workflow_health tool call"""
        from backend.agents.guardian import get_workflow_health_monitor
        from backend.core.database import get_async_session
        
        execution_id = UUID(arguments["execution_id"])
        
        # Get database session using context manager
        from backend.core.database import get_db_context
        
        async with get_db_context() as db:
            monitor = get_workflow_health_monitor()
            health = await monitor.calculate_health(db=db, execution_id=execution_id)
            
            result = health.to_dict()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    async def _handle_get_coherence_score(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle get_coherence_score tool call"""
        from backend.agents.guardian import get_coherence_scorer
        from backend.models.workflow import WorkflowPhase
        from backend.core.database import get_async_session
        
        execution_id = UUID(arguments["execution_id"])
        agent_id = UUID(arguments["agent_id"])
        phase = WorkflowPhase(arguments["phase"])
        
        # Get database session using context manager
        from backend.core.database import get_db_context
        
        async with get_db_context() as db:
            scorer = get_coherence_scorer()
            score = await scorer.calculate_coherence(
                db=db,
                agent_id=agent_id,
                execution_id=execution_id,
                phase=phase,
            )
            
            result = score.to_dict()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    async def _handle_create_workflow_branch(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle create_workflow_branch tool call"""
        from backend.agents.branching.branching_engine import get_branching_engine
        from backend.agents.discovery import Discovery
        from backend.models.workflow import WorkflowPhase
        from backend.core.database import get_async_session
        
        execution_id = UUID(arguments["execution_id"])
        agent_id = UUID(arguments["agent_id"])
        branch_name = arguments["branch_name"]
        initial_task_title = arguments["initial_task_title"]
        initial_task_description = arguments["initial_task_description"]
        discovery_id = arguments.get("discovery_id")
        
        # Get database session using context manager
        from backend.core.database import get_db_context
        
        async with get_db_context() as db:
            # Create mock discovery (in real implementation, retrieve from DB)
            discovery = Discovery(
                type="optimization",
                description="Branch created via MCP",
                value_score=0.7,
                suggested_phase=WorkflowPhase.INVESTIGATION,
                confidence=0.8,
                context={"discovery_id": discovery_id or ""},
            )
            
            branching_engine = get_branching_engine()
            branch = await branching_engine.create_branch_from_discovery(
                db=db,
                execution_id=execution_id,
                discovery=discovery,
                branch_name=branch_name,
                initial_task_title=initial_task_title,
                initial_task_description=initial_task_description,
                agent_id=agent_id,
            )
            
            result = {
                "branch_id": str(branch.id),
                "branch_name": branch.branch_name,
                "phase": branch.branch_phase,
                "status": branch.status,
                "created_at": branch.created_at.isoformat(),
            }
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    async def _handle_discover_opportunities(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle discover_opportunities tool call"""
        from backend.agents.discovery.discovery_engine import DiscoveryEngine, WorkContext, get_discovery_engine
        from backend.models.workflow import WorkflowPhase
        from backend.models.message import AgentMessage
        from backend.core.database import get_async_session
        from sqlalchemy import select
        
        execution_id = UUID(arguments["execution_id"])
        agent_id = UUID(arguments["agent_id"])
        phase = WorkflowPhase(arguments["phase"])
        
        # Get database session using context manager
        from backend.core.database import get_db_context
        
        async with get_db_context() as db:
            # Load context
            message_stmt = (
                select(AgentMessage)
                .where(
                    AgentMessage.task_execution_id == execution_id,
                    AgentMessage.sender_id == agent_id,
                )
                .order_by(AgentMessage.created_at.desc())
                .limit(20)
            )
            from sqlalchemy.ext.asyncio import AsyncSession
            result = await db.execute(message_stmt)
            recent_messages = list(result.scalars().all())
            
            from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
            engine = PhaseBasedWorkflowEngine()
            all_tasks = await engine.get_tasks_for_execution(db=db, execution_id=execution_id)
            recent_tasks = [t for t in all_tasks if t.spawned_by_agent_id == agent_id][:10]
            
            context = WorkContext(
                execution_id=execution_id,
                agent_id=agent_id,
                phase=phase,
                recent_messages=recent_messages,
                recent_tasks=recent_tasks,
            )
            
            discovery_engine = get_discovery_engine()
            suggestions = await discovery_engine.discover_and_suggest_tasks(
                db=db,
                context=context,
            )
            
            result = {
                "suggestions": [
                    {
                        "title": s.title,
                        "description": s.description,
                        "phase": s.phase.value,
                        "estimated_value": s.estimated_value,
                        "priority": s.priority,
                    }
                    for s in suggestions
                ],
                "count": len(suggestions),
            }
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    async def _handle_get_kanban_board(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle get_kanban_board tool call"""
        from backend.agents.orchestration.phase_based_engine import PhaseBasedWorkflowEngine
        from backend.core.database import get_async_session
        
        execution_id = UUID(arguments["execution_id"])
        
        # Get database session using context manager
        from backend.core.database import get_db_context
        
        async with get_db_context() as db:
            engine = PhaseBasedWorkflowEngine()
            all_tasks = await engine.get_tasks_for_execution(
                db=db,
                execution_id=execution_id,
                include_dependencies=True,
            )
            
            # Organize by phase
            columns = {
                "investigation": [],
                "building": [],
                "validation": [],
            }
            
            for task in all_tasks:
                columns[task.phase].append({
                    "id": str(task.id),
                    "title": task.title,
                    "status": task.status,
                    "created_at": task.created_at.isoformat(),
                })
            
            result = {
                "execution_id": str(execution_id),
                "columns": columns,
                "total_tasks": len(all_tasks),
            }
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
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
_agent_squad_server_instance: Optional[AgentSquadMCPServer] = None


def get_agent_squad_server() -> AgentSquadMCPServer:
    """Get singleton Agent-Squad MCP server instance"""
    global _agent_squad_server_instance
    if _agent_squad_server_instance is None:
        _agent_squad_server_instance = AgentSquadMCPServer()
    return _agent_squad_server_instance


def main():
    """Entry point for running MCP server"""
    import asyncio
    
    server = get_agent_squad_server()
    if MCP_AVAILABLE:
        asyncio.run(server.run())
    else:
        logger.error("MCP SDK not available. Install with: pip install mcp")
        sys.exit(1)


if __name__ == "__main__":
    main()

