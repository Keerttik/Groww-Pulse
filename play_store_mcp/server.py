import json
from datetime import datetime
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from play_store_mcp.scraper import fetch_reviews_from_store, get_app_info_from_store

server = Server("play-store-mcp")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="fetch_reviews",
            description="Fetches public reviews for a given Google Play app.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "string"},
                    "language": {"type": "string", "default": "en"},
                    "country": {"type": "string", "default": "in"},
                    "count": {"type": "integer", "default": 500},
                    "sort_by": {"type": "string", "default": "newest"},
                    "filter_score": {"type": "integer"}
                },
                "required": ["app_id"]
            }
        ),
        Tool(
            name="get_app_info",
            description="Returns metadata about the app.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "string"},
                    "language": {"type": "string", "default": "en"},
                    "country": {"type": "string", "default": "in"}
                },
                "required": ["app_id"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "fetch_reviews":
        try:
            reviews = await fetch_reviews_from_store(
                app_id=arguments["app_id"],
                language=arguments.get("language", "en"),
                country=arguments.get("country", "in"),
                count=arguments.get("count", 500),
                sort_by=arguments.get("sort_by", "newest"),
                filter_score=arguments.get("filter_score")
            )
            response = {
                "app_id": arguments["app_id"],
                "fetched_at": datetime.utcnow().isoformat() + "Z",
                "review_count": len(reviews),
                "reviews": [r.model_dump() for r in reviews]
            }
            return [TextContent(type="text", text=json.dumps(response))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]
            
    elif name == "get_app_info":
        try:
            info = await get_app_info_from_store(
                app_id=arguments["app_id"],
                language=arguments.get("language", "en"),
                country=arguments.get("country", "in")
            )
            return [TextContent(type="text", text=json.dumps(info))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    raise ValueError(f"Unknown tool: {name}")

async def main():
    async with stdio_server() as (read, write):
        # Pass an empty object or options to run
        from mcp.server.models import InitializationOptions
        await server.run(read, write, InitializationOptions(
            server_name="play-store-mcp",
            server_version="0.1.0",
            capabilities=server.get_capabilities()
        ))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
