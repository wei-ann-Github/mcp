import os

from contextlib import asynccontextmanager
from dotenv import load_dotenv
import asyncpg
from mcp.server.fastmcp import FastMCP, Context

# Database config (replace with your actual settings or load from .env)
DB_URL = os.getenv("DB_URL")

@asynccontextmanager
async def lifespan(server: FastMCP):
    db = await asyncpg.connect(DB_URL)
    try:
        yield {"db": db}
    finally:
        await db.close()

# Define lifespan separately
@asynccontextmanager
async def connect_db():
    conn = await asyncpg.connect(DB_URL)
    try:
        yield {"db": conn}
    finally:
        await conn.close()

# Create the server
mcp = FastMCP("Postgres MCP Server", lifespan=connect_db)

# --- RESOURCES: Expose list of table schemas ---
@mcp.resource("pgschema://{table}")
async def get_table_schema(table: str) -> str:
    ctx = Context.current()
    db = ctx.request_context.lifespan_context["db"]
    result = await db.fetch(f"""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = $1
    """, table)
    return "\n".join(f"{row['column_name']} ({row['data_type']})" for row in result)

# --- TOOL: Run a safe, read-only SQL query ---
@mcp.tool()
async def run_sql(query: str, ctx: Context) -> str:
    if not query.strip().lower().startswith("select"):
        return "Only SELECT queries are allowed."
    db = ctx.request_context.lifespan_context["db"]
    try:
        rows = await db.fetch(query)
        return "\n".join(str(dict(r)) for r in rows)
    except Exception as e:
        return f"Error: {e}"

# --- PROMPTS: Reusable data analysis tasks ---
@mcp.prompt()
def summarize_table(table: str) -> str:
    return f"What are the most important insights in the `{table}` table?"

@mcp.prompt()
def find_trends(column: str, table: str) -> str:
    return f"Are there any patterns or trends in `{column}` from the `{table}` table?"
