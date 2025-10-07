import asyncio
import os
import json
from contextlib import asynccontextmanager
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route
import uvicorn

# Create MCP server instance
mcp_server = Server("filesystem-mcp-server")

@mcp_server.list_tools()
async def list_tools():
    """List available filesystem tools"""
    return [
        Tool(
            name="read_file",
            description="Read contents of a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"}
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="write_file",
            description="Write content to a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["path", "content"]
            }
        ),
        Tool(
            name="list_directory",
            description="List contents of a directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path", "default": "."}
                }
            }
        ),
        Tool(
            name="create_directory",
            description="Create a new directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to create"}
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="delete_file",
            description="Delete a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to delete"}
                },
                "required": ["path"]
            }
        )
    ]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool execution"""
    try:
        if name == "read_file":
            with open(arguments["path"], 'r', encoding='utf-8') as f:
                return [TextContent(type="text", text=f.read())]
        
        elif name == "write_file":
            with open(arguments["path"], 'w', encoding='utf-8') as f:
                f.write(arguments["content"])
            return [TextContent(type="text", text=f"Wrote to {arguments['path']}")]
        
        elif name == "list_directory":
            path = arguments.get("path", ".")
            items = os.listdir(path)
            return [TextContent(type="text", text=json.dumps(items, indent=2))]
        
        elif name == "create_directory":
            os.makedirs(arguments["path"], exist_ok=True)
            return [TextContent(type="text", text=f"Created {arguments['path']}")]
        
        elif name == "delete_file":
            os.remove(arguments["path"])
            return [TextContent(type="text", text=f"Deleted {arguments['path']}")]
        
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

# Create the SSE transport - this handles both /sse and /messages endpoints
sse = SseServerTransport("/messages")

async def handle_sse(request):
    """Handle SSE connections"""
    async with sse.connect_sse(
        request.scope,
        request.receive, 
        request._send
    ) as streams:
        await mcp_server.run(
            streams[0],
            streams[1], 
            mcp_server.create_initialization_options()
        )

async def handle_messages(request):
    """Handle message posts"""
    await sse.handle_post_message(
        request.scope,
        request.receive,
        request._send
    )

@asynccontextmanager
async def lifespan(app):
    """Application lifespan manager"""
    print("🚀 Server starting up...")
    yield
    print("👋 Server shutting down...")

# Create Starlette application
app = Starlette(
    debug=True,
    lifespan=lifespan,
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
    ]
)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🔧 MCP Filesystem Server")
    print(f"📍 Host: {host}:{port}")
    print(f"🔗 SSE: http://{host}:{port}/sse")
    print(f"📬 Messages: http://{host}:{port}/messages")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )