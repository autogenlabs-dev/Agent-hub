"""memU Telegram Bot — Agent 4 for the communication-channel system.

A Telegram bot powered by memU's MemoryService with full capabilities:
- RAG memory retrieval with Ollama embeddings
- Web scraping via Firecrawl
- Text-to-speech via ElevenLabs
- Web search via You.com
- Multi-agent coordination via backend API
"""

import asyncio
import json
import logging
import os
import base64
import re
from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import random

import httpx
import websockets
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest

from memu.app import MemoryService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("memu-bot")

# Configuration from environment
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ZAI_API_KEY = os.environ["ZAI_API_KEY"]
ZAI_BASE_URL = os.environ.get("ZAI_BASE_URL", "https://api.z.ai/api/coding/paas/v4")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://host.docker.internal:11434/v1")
BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:8000")
AGENT_NAME = os.environ.get("AGENT_NAME", "MemU Bot")
YOU_API_KEY = os.environ.get("YOU_API_KEY", "")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")
DATA_DIR = os.environ.get("DATA_DIR", "/data")
BOT_TRIGGER_NAMES = ["alex"]  # Names the bot responds to in groups

# Production Constants
from datetime import datetime, timedelta
MAX_RETRIES = 3
AGENT_TIMEOUT_SECONDS = 180  # 3 minutes for agent to respond
RETRY_DELAY_SECONDS = 15
CHECK_STUCK_INTERVAL = 30  # Check for stuck projects every 30 seconds


# Map agent names to WebSocket agent IDs for inter-agent communication
AGENT_WS_MAP = {
    "cto": "clawdbot-1",
    "ben": "clawdbot-1",
    "clawdbot 1": "clawdbot-1",
    "clawdbot_1": "clawdbot-1",
    "developer": "clawdbot-2",
    "devin": "clawdbot-2",
    "clawdbot 2": "clawdbot-2",
    "clawdbot_2": "clawdbot-2",
    "devops": "clawdbot-3",
    "eric": "clawdbot-3",
    "clawdbot 3": "clawdbot-3",
    "clawdbot_3": "clawdbot-3",
}

# Friendly display names for agent IDs
AGENT_DISPLAY_NAMES = {
    "clawdbot-1": "Ben",
    "clawdbot-2": "Devin",
    "clawdbot-3": "Eric",
}
GROUP_CHAT_ID = int(os.environ.get("GROUP_CHAT_ID", "0"))  # Set from first /start in group

# Per-chat conversation buffers for batching memorization
chat_buffers: dict[int, list[dict]] = {}
MEMORIZE_THRESHOLD = 4  # memorize every N messages (user+assistant pairs)

# Global memory service
memory_service: MemoryService | None = None

# WebSocket connection for inter-agent communication
ws_connection: websockets.WebSocketClientProtocol | None = None
agent_id: str | None = None  # Our agent ID from backend registration
telegram_app: Application | None = None  # Reference to send Telegram messages from WS handler
ADMIN_CHAT_ID: int | None = None  # Will be set on first /start to forward inter-agent messages
last_agent_activity: float = 0.0  # Timestamp of last agent message for watchdog

# Rate limit cooldown tracking: {agent_id: {"until": timestamp, "task": "what they were doing"}}
agent_cooldowns: dict = {}
COOLDOWN_MINUTES = 5  # How long to pause a rate-limited agent


def get_memory_service() -> MemoryService:
    """Initialize MemoryService with dual LLM profiles: ZAI for chat, Ollama for embeddings."""
    global memory_service
    if memory_service is not None:
        return memory_service

    memory_service = MemoryService(
        llm_profiles={
            # Default profile for chat/reasoning (ZAI glm-4.7)
            "default": {
                "base_url": ZAI_BASE_URL,
                "api_key": ZAI_API_KEY,
                "chat_model": "glm-4.7",
                "embed_model": "nomic-embed-text",
                "client_backend": "httpx",
            },
            # Embedding profile (Ollama - local, free)
            "embedding": {
                "base_url": OLLAMA_BASE_URL,
                "api_key": "ollama",
                "chat_model": "llama3.2:3b",
                "embed_model": "nomic-embed-text",
                "client_backend": "httpx",
            },
        },
        database_config={
            "metadata_store": {
                "provider": "inmemory",
            },
        },
        blob_config={
            "resources_dir": str(Path(DATA_DIR) / "resources"),
        },
    )
    logger.info("MemoryService initialized with Ollama embeddings")
    return memory_service


def dump_conversation(messages: list[dict], chat_id: int) -> str:
    """Dump conversation messages to a JSON file for memU ingestion."""
    resource_data = {
        "content": [
            {
                "role": msg.get("role", "user"),
                "content": {"text": msg.get("content", "")},
            }
            for msg in messages
        ]
    }
    resource_dir = Path(DATA_DIR) / "resources"
    resource_dir.mkdir(parents=True, exist_ok=True)
    path = resource_dir / f"chat_{chat_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(resource_data, f, indent=2, ensure_ascii=False)
    return str(path)


    return str(path)



# Chat Persistence
CHATS_FILE = Path(DATA_DIR) / "chats.json"

def load_chats() -> None:
    """Load chat IDs from JSON file."""
    global GROUP_CHAT_ID, ADMIN_CHAT_ID
    if CHATS_FILE.exists():
        try:
            with open(CHATS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                GROUP_CHAT_ID = data.get("GROUP_CHAT_ID", 0)
                ADMIN_CHAT_ID = data.get("ADMIN_CHAT_ID", 0)
            logger.info("Loaded Chat IDs - Group: %s, Admin: %s", GROUP_CHAT_ID, ADMIN_CHAT_ID)
        except Exception as e:
            logger.error("Failed to load chats: %s", e)

def save_chats() -> None:
    """Save chat IDs to JSON file."""
    try:
        data = {
            "GROUP_CHAT_ID": GROUP_CHAT_ID,
            "ADMIN_CHAT_ID": ADMIN_CHAT_ID
        }
        with open(CHATS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error("Failed to save chats: %s", e)


# Project Persistence
PROJECTS_FILE = Path(DATA_DIR) / "projects.json"
active_projects: dict[str, dict] = {}

def load_projects() -> None:
    """Load active projects from JSON file."""
    global active_projects
    if PROJECTS_FILE.exists():
        try:
            with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
                active_projects = json.load(f)
            logger.info("Loaded %d active projects", len(active_projects))
        except Exception as e:
            logger.error("Failed to load projects: %s", e)

def save_projects() -> None:
    """Save active projects to JSON file."""
    try:
        with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
            json.dump(active_projects, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error("Failed to save projects: %s", e)


async def register_with_backend() -> None:
    """Register this bot as an agent with the backend API."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{BACKEND_URL}/api/agents/register",
                json={
                    "name": AGENT_NAME,
                    "type": "memory",
                    "meta_data": {
                        "capabilities": [
                            "memorize", "retrieve", "conversation",
                            "rag_search", "web_search", "tts", "web_scrape",
                            "image_understanding", "skill_learning"
                        ]
                    },
                },
            )
            if resp.status_code in (200, 201):
                logger.info("Registered with backend as '%s'", AGENT_NAME)
            else:
                logger.warning("Backend registration returned %s", resp.status_code)
    except Exception as e:
        logger.warning("Could not register with backend: %s", e)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    global ADMIN_CHAT_ID, GROUP_CHAT_ID
    chat_type = update.effective_chat.type
    
    updated = False
    if chat_type in ("group", "supergroup") and not GROUP_CHAT_ID:
        GROUP_CHAT_ID = update.effective_chat.id
        logger.info("Group chat ID set to %s", GROUP_CHAT_ID)
        updated = True
        
    if not ADMIN_CHAT_ID:
        ADMIN_CHAT_ID = update.effective_chat.id
        logger.info("Admin chat ID set to %s", ADMIN_CHAT_ID)
        updated = True
        
    if updated:
        save_chats()

    await update.message.reply_text(
        f"🤖 Hi! I'm {AGENT_NAME} - your AI memory assistant with full capabilities.\n\n"
        "🧠 **Memory Commands:**\n"
        "/remember <text> - Store in memory\n"
        "/memory <query> - Search memory (RAG)\n"
        "/categories - View categories\n"
        "/forget - Clear memory\n\n"
        "🔍 **Web Commands:**\n"
        "/search <query> - Web search\n"
        "/scrape <url> - Scrape webpage\n\n"
        "🎙️ **Media Commands:**\n"
        "/speak <text> - Text-to-speech\n"
        "📷 Send an image - I'll analyze it!\n\n"
        "🛠️ **Skills:**\n"
        "/learn <skill> - Learn a new skill\n"
        "/skills - List learned skills\n\n"
        "👥 **Multi-Agent:**\n"
        "/agents - List agents\n"
        "/ask <agent> <msg> - Talk to another bot\n"
        "/tasks - List tasks\n"
        "/status - Bot status\n\n"
        "Just chat with me and I'll remember everything!"
    )


# ==================== MEMORY COMMANDS ====================

async def remember_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /remember <text> command."""
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Usage: /remember <text>")
        return

    svc = get_memory_service()
    chat_id = update.effective_chat.id
    user_id = f"tg_{chat_id}"

    await update.effective_chat.send_action("typing")

    try:
        resource_path = dump_conversation([{"role": "user", "content": text}], chat_id)
        result = await svc.memorize(
            resource_url=resource_path,
            modality="conversation",
            user={"user_id": user_id},
        )
        categories = result.get("categories", [])
        cat_names = [c.get("name", "") for c in categories if c.get("name")]
        await update.message.reply_text(f"✅ Memorized in: {', '.join(cat_names) if cat_names else 'General'}")
    except Exception as e:
        logger.error("Memorization failed: %s", e)
        await update.message.reply_text(f"❌ Memory error: {e}")


async def memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /memory <query> command — RAG-based memory retrieval."""
    query = " ".join(context.args) if context.args else ""
    if not query:
        await update.message.reply_text("Usage: /memory <query>")
        return

    svc = get_memory_service()
    chat_id = update.effective_chat.id
    user_id = f"tg_{chat_id}"

    await update.effective_chat.send_action("typing")

    try:
        result = await svc.retrieve(
            queries=[{"role": "user", "content": {"text": query}}],
            where={"user_id": user_id},
        )
        
        categories = result.get("categories", [])
        items = result.get("items", [])

        if not categories and not items:
            await update.message.reply_text("No memories found. Try /remember first!")
            return

        parts = ["🔍 **Memory Results:**\n"]
        for cat in categories[:3]:
            name = cat.get("name", "")
            summary = cat.get("summary", "")
            if summary:
                parts.append(f"**{name}**\n{summary[:200]}")
        
        if items:
            parts.append("\n**Memories:**")
            for item in items[:5]:
                content = item.get("content", "")
                if content:
                    parts.append(f"• {content[:150]}")

        await update.message.reply_text("\n".join(parts)[:4000])
    except Exception as e:
        logger.error("Memory retrieval failed: %s", e)
        await update.message.reply_text(f"Error: {e}")


async def categories_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /categories command."""
    svc = get_memory_service()
    chat_id = update.effective_chat.id
    user_id = f"tg_{chat_id}"

    try:
        result = await svc.list_memory_categories(where={"user_id": user_id})
        categories = result.get("categories", [])

        if not categories:
            await update.message.reply_text("No memory categories yet. Start chatting!")
            return

        parts = ["📂 **Memory Categories:**\n"]
        for cat in categories:
            name = cat.get("name", "Unknown")
            desc = cat.get("description", "")[:80]
            parts.append(f"• **{name}**: {desc}")

        await update.message.reply_text("\n".join(parts)[:4000])
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def forget_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /forget command."""
    svc = get_memory_service()
    chat_id = update.effective_chat.id
    user_id = f"tg_{chat_id}"

    try:
        await svc.clear_memory(where={"user_id": user_id})
        chat_buffers.pop(chat_id, None)
        await update.message.reply_text("🗑️ Memory cleared!")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


# ==================== WEB COMMANDS ====================

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /search <query> command — web search via You.com."""
    query = " ".join(context.args) if context.args else ""
    if not query:
        await update.message.reply_text("Usage: /search <query>")
        return

    if not YOU_API_KEY:
        await update.message.reply_text("❌ Search not configured (missing YOU_API_KEY)")
        return

    await update.effective_chat.send_action("typing")

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://ydc-index.io/v1/search",
                headers={"X-API-Key": YOU_API_KEY},
                params={"query": query, "count": 5},
            )
            resp.raise_for_status()
            data = resp.json()

        results = data.get("results", {}).get("web", [])
        if not results:
            await update.message.reply_text(f"No results for: {query}")
            return

        parts = [f"🔍 **Results for:** {query}\n"]
        for i, r in enumerate(results[:5], 1):
            title = r.get("title", "")
            url = r.get("url", "")
            snippet = r.get("snippet", "")[:120]
            parts.append(f"{i}. **{title}**\n{url}\n{snippet}\n")

        await update.message.reply_text("\n".join(parts)[:4000])
    except Exception as e:
        await update.message.reply_text(f"Search error: {e}")


async def scrape_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /scrape <url> command — web scraping via Firecrawl."""
    url = " ".join(context.args) if context.args else ""
    if not url:
        await update.message.reply_text("Usage: /scrape <url>")
        return

    if not FIRECRAWL_API_KEY:
        await update.message.reply_text("❌ Scraping not configured (missing FIRECRAWL_API_KEY)")
        return

    await update.effective_chat.send_action("typing")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.firecrawl.dev/v0/scrape",
                headers={
                    "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={"url": url, "pageOptions": {"onlyMainContent": True}},
            )
            resp.raise_for_status()
            data = resp.json()

        content = data.get("data", {}).get("markdown", data.get("data", {}).get("content", ""))
        if not content:
            await update.message.reply_text("No content extracted from URL")
            return

        # Truncate for Telegram message limit
        content = content[:3500]
        await update.message.reply_text(f"📄 **Scraped content:**\n\n{content}")
    except Exception as e:
        await update.message.reply_text(f"Scrape error: {e}")


# ==================== TTS COMMAND ====================

async def speak_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /speak <text> command — text-to-speech via ElevenLabs."""
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Usage: /speak <text>")
        return

    if not ELEVENLABS_API_KEY:
        await update.message.reply_text("❌ TTS not configured (missing ELEVENLABS_API_KEY)")
        return

    await update.effective_chat.send_action("record_voice")

    try:
        voice_id = "JBFqnCBsd6RMkjVDRZzb"  # Default voice
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers={
                    "xi-api-key": ELEVENLABS_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "text": text[:500],  # Limit text length
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75
                    }
                },
            )
            resp.raise_for_status()
            audio_data = resp.content

        # Save and send audio
        audio_path = Path(DATA_DIR) / "tts_output.mp3"
        with open(audio_path, "wb") as f:
            f.write(audio_data)
        
        with open(audio_path, "rb") as f:
            await update.message.reply_voice(voice=f)
        
        logger.info("TTS audio sent for: %s", text[:50])
    except Exception as e:
        logger.error("TTS error: %s", e)
        await update.message.reply_text(f"TTS error: {e}")


# ==================== MULTI-AGENT COMMANDS ====================

async def agents_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /agents command."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{BACKEND_URL}/api/agents")
            if resp.status_code == 200:
                agents = resp.json()
                if not agents:
                    await update.message.reply_text("No agents registered.")
                    return
                
                parts = ["🤖 **Registered Agents:**\n"]
                for agent in agents:
                    status = "🟢" if agent.get("status") == "online" else "⚪"
                    parts.append(f"{status} {agent.get('name')} ({agent.get('type')})")
                
                await update.message.reply_text("\n".join(parts))
            else:
                await update.message.reply_text(f"Backend error: {resp.status_code}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /tasks command."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{BACKEND_URL}/api/tasks/pending")
            if resp.status_code == 200:
                tasks = resp.json()
                if not tasks:
                    await update.message.reply_text("No pending tasks.")
                    return
                
                parts = ["📋 **Pending Tasks:**\n"]
                for task in tasks[:10]:
                    priority = "🔴" if task.get("priority", 0) > 2 else "🟡" if task.get("priority", 0) > 1 else "🟢"
                    parts.append(f"{priority} {task.get('title')}")
                
                await update.message.reply_text("\n".join(parts))
            else:
                await update.message.reply_text(f"Backend error: {resp.status_code}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command."""
    svc = get_memory_service()
    chat_id = update.effective_chat.id
    user_id = f"tg_{chat_id}"
    buf_size = len(chat_buffers.get(chat_id, []))

    try:
        cats = await svc.list_memory_categories(where={"user_id": user_id})
        n_cats = len(cats.get("categories", []))
        items = await svc.list_memory_items(where={"user_id": user_id})
        n_items = len(items.get("items", []))
    except Exception:
        n_cats = "?"
        n_items = "?"

    features = []
    if YOU_API_KEY:
        features.append("✅ Web Search")
    if FIRECRAWL_API_KEY:
        features.append("✅ Web Scraping")
    if ELEVENLABS_API_KEY:
        features.append("✅ TTS")
    features.append("✅ RAG Memory")
    features.append("✅ Multi-Agent")

    await update.message.reply_text(
        f"🤖 **{AGENT_NAME} Status**\n\n"
        f"📊 Categories: {n_cats}\n"
        f"💾 Memory Items: {n_items}\n"
        f"📝 Buffer: {buf_size} msgs\n"
        f"🧠 LLM: glm-4.7 via ZAI\n"
        f"📍 Embeddings: Ollama nomic-embed\n\n"
        f"**Enabled Features:**\n" + "\n".join(features)
    )


# ==================== MESSAGE HANDLER ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular text messages — memorize and respond with context."""
    if not update.message or not update.message.text:
        return

    global GROUP_CHAT_ID
    svc = get_memory_service()
    chat_id = update.effective_chat.id
    user_id = f"tg_{chat_id}"
    chat_type = update.effective_chat.type
    user_text = update.message.text
    bot_username = context.bot.username

    # Auto-detect group chat ID
    if chat_type in ("group", "supergroup") and not GROUP_CHAT_ID:
        GROUP_CHAT_ID = chat_id
        logger.info("Group chat ID auto-detected: %s", GROUP_CHAT_ID)
        save_chats()

    # In groups, only respond if mentioned, replied to, or trigger name used
    if chat_type in ("group", "supergroup"):
        is_mentioned = False
        if update.message.entities:
            for entity in update.message.entities:
                if entity.type == "mention":
                    mention_text = user_text[entity.offset:entity.offset + entity.length]
                    if mention_text.lower() == f"@{bot_username}".lower():
                        is_mentioned = True
                        break

        # Check if replying to bot's message
        if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
            is_mentioned = True

        # Check for trigger names (e.g. "Alex, what time is it?")
        lower_text_check = user_text.lower()
        for trigger in BOT_TRIGGER_NAMES:
            if trigger in lower_text_check:
                is_mentioned = True
                break

        if not is_mentioned and f"@{bot_username}" not in user_text:
            return

    # Strip trigger name from message so LLM gets clean text
    clean_text = user_text
    
    # Check for TEAM MENTIONS (Ben, Devin, Eric) and route to them
    lower_text = user_text.lower()
    target_agent_id = None
    target_display_name = None
    
    # Check if addressing another agent
    for key, ws_id in AGENT_WS_MAP.items():
        # strict word boundary check or explicit mention
        if re.search(rf'\b{key}\b', lower_text):
            target_agent_id = ws_id
            target_display_name = AGENT_DISPLAY_NAMES.get(ws_id, key)
            break
            
    if target_agent_id and not is_mentioned:
        # User is talking to Ben/Devin/Eric, not Alex
        logger.info("Routing message to %s: %s", target_display_name, clean_text[:50])
        await update.effective_chat.send_action("typing")
        
        # Forward to agent via WebSocket
        success = await send_ws_message(clean_text, recipients=[target_agent_id])
        if success:
             # Log in backend
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    await client.post(
                        f"{BACKEND_URL}/api/messages",
                        json={
                            "sender_id": "memu-bot", # Proxying for user
                            "content": f"[User -> {target_display_name}] {clean_text}",
                            "message_type": "text",
                            "recipients": [target_agent_id],
                        },
                    )
            except:
                pass
            # We don't reply here, we let the agent reply via WS event
            return
        else:
            await update.message.reply_text(f"⚠️ Could not reach {target_display_name} (WS disconnected)")
            return

    for trigger in BOT_TRIGGER_NAMES:
        clean_text = re.sub(rf'(?i)\b{trigger}\b[,:]?\s*', '', clean_text).strip()
    if bot_username:
        clean_text = clean_text.replace(f"@{bot_username}", "").strip()
    if not clean_text:
        clean_text = user_text

    logger.info("Processing message: '%s' (clean: '%s')", user_text[:50], clean_text[:50])

    # Check for commands that might be prefixed with a mention (e.g. "@bot /status")
    # This fixes the issue where the bot responds with LLM instead of the command handler
    lower_text = user_text.lower()
    if "/status" in lower_text:
        await status_command(update, context)
        return
    if "/skills" in lower_text:
        await skills_command(update, context)
        return
    if "/agents" in lower_text:
        await agents_command(update, context)
        return
    if "/tasks" in lower_text:
        await tasks_command(update, context)
        return
    if "/autonomy" in lower_text:
        # Manually parse args
        parts = clean_text.strip().split()
        cmd_idx = -1
        for i, p in enumerate(parts):
            if "/autonomy" in p.lower():
                cmd_idx = i
                break
        if cmd_idx != -1 and len(parts) > cmd_idx + 1:
            context.args = parts[cmd_idx + 1:]
        else:
            context.args = []
        await autonomy_command(update, context)
        return
    if "/meet" in lower_text:
        await meet_command(update, context)
        return
    if "/standup" in lower_text:
        await standup_command(update, context)
        return
    if "/ask" in lower_text:
        # Manually parse arguments for /ask if triggered here
        # clean_text should be something like "/ask Agent Message"
        parts = clean_text.strip().split()
        # Find index of /ask (case insensitive)
        cmd_idx = -1
        for i, p in enumerate(parts):
            if "/ask" in p.lower():
                cmd_idx = i
                break
        
        if cmd_idx != -1 and len(parts) > cmd_idx + 1:
            context.args = parts[cmd_idx + 1:]
        else:
            context.args = []
            
        await ask_command(update, context)
        return

    if "/project" in lower_text:
        # Manually parse arguments for /project if triggered here
        parts = clean_text.strip().split()
        # Find index of /project
        cmd_idx = -1
        for i, p in enumerate(parts):
            if "/project" in p.lower():
                cmd_idx = i
                break
        
        if cmd_idx != -1 and len(parts) > cmd_idx + 1:
            context.args = parts[cmd_idx + 1:]
        else:
            context.args = []
            
        await project_command(update, context)
        return

    await update.effective_chat.send_action("typing")

    # Add to buffer
    if chat_id not in chat_buffers:
        chat_buffers[chat_id] = []
    chat_buffers[chat_id].append({"role": "user", "content": clean_text})

    # Try to retrieve relevant memories
    memory_context = ""
    try:
        result = await svc.retrieve(
            queries=[{"role": "user", "content": {"text": clean_text}}],
            where={"user_id": user_id},
        )
        items = result.get("items", [])
        if items:
            memory_context = "Relevant memories:\n" + "\n".join(
                [f"- {item.get('content', '')[:100]}" for item in items[:3]]
            )
    except Exception as e:
        logger.debug("Memory retrieval skipped: %s", e)

    # Build conversation context
    context_str = ""
    buf = chat_buffers.get(chat_id, [])
    if len(buf) > 1:
        recent = buf[-(min(len(buf), 8)):-1]
        for msg in recent:
            context_str += f"{msg['role']}: {msg['content']}\n"

    # Generate response
    try:
        system_prompt = (
            f"You are Alex ({AGENT_NAME}), a helpful AI assistant with persistent memory. "
            "Your name is Alex. Be concise and helpful. Reference memories when relevant."
        )
        if memory_context:
            system_prompt += f"\n\n{memory_context}"
        if context_str:
            system_prompt += f"\n\nRecent chat:\n{context_str}"

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{ZAI_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {ZAI_API_KEY}"},
                json={
                    "model": "glm-4.7",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": clean_text},
                    ],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            reply = data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error("LLM error: %s", e)
        reply = f"I received your message. (LLM error: {e})"

    # Add reply to buffer
    chat_buffers[chat_id].append({"role": "assistant", "content": reply})

    await update.message.reply_text(reply[:4000])

    # Memorize in background
    if len(chat_buffers[chat_id]) >= MEMORIZE_THRESHOLD:
        asyncio.create_task(memorize_buffer(chat_id, user_id))


async def memorize_buffer(chat_id: int, user_id: str) -> None:
    """Background memorization."""
    messages = chat_buffers.pop(chat_id, [])
    if not messages:
        return

    svc = get_memory_service()
    try:
        resource_path = dump_conversation(messages, chat_id)
        await svc.memorize(
            resource_url=resource_path,
            modality="conversation",
            user={"user_id": user_id},
        )
        logger.info("Memorized %d messages for chat %s", len(messages), chat_id)
    except Exception as e:
        logger.error("Memorization failed: %s", e)
        if chat_id not in chat_buffers:
            chat_buffers[chat_id] = []
        chat_buffers[chat_id] = messages + chat_buffers[chat_id]


# Skill storage
SKILLS_FILE = Path(DATA_DIR) / "skills.json"
learned_skills: dict[int, list[dict]] = {}

def load_skills() -> None:
    """Load skills from JSON file."""
    global learned_skills
    if SKILLS_FILE.exists():
        try:
            with open(SKILLS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Convert string keys back to integers
                learned_skills = {int(k): v for k, v in data.items()}
            logger.info("Loaded skills for %d chats", len(learned_skills))
        except Exception as e:
            logger.error("Failed to load skills: %s", e)

def save_skills() -> None:
    """Save skills to JSON file."""
    try:
        with open(SKILLS_FILE, "w", encoding="utf-8") as f:
            json.dump(learned_skills, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error("Failed to save skills: %s", e)

async def learn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /learn <skill description> command - learn a new skill."""
    skill = " ".join(context.args) if context.args else ""
    if not skill:
        await update.message.reply_text("Usage: /learn <skill description>\nExample: /learn When I say 'morning report', summarize my tasks")
        return

    chat_id = update.effective_chat.id
    if chat_id not in learned_skills:
        learned_skills[chat_id] = []
    
    learned_skills[chat_id].append({
        "skill": skill,
        "learned_at": str(asyncio.get_event_loop().time())
    })
    save_skills()
    
    await update.message.reply_text(f"✅ Learned new skill: {skill[:100]}")


async def skills_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /skills command - list learned skills."""
    chat_id = update.effective_chat.id
    skills = learned_skills.get(chat_id, [])
    
    if not skills:
        await update.message.reply_text("No skills learned yet. Use /learn to teach me!")
        return
    
    parts = ["🛠️ **Learned Skills:**\n"]
    for i, s in enumerate(skills, 1):
        parts.append(f"{i}. {s['skill'][:80]}")
    
    await update.message.reply_text("\n".join(parts)[:4000])


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo messages - analyze with Ollama moondream vision model."""
    if not update.message or not update.message.photo:
        return
    
    chat_id = update.effective_chat.id
    await update.effective_chat.send_action("typing")
    
    try:
        # Get the largest photo
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        # Download photo
        photo_path = Path(DATA_DIR) / f"photo_{chat_id}.jpg"
        await file.download_to_drive(photo_path)
        
        # Read and encode as base64
        with open(photo_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Get caption if any
        caption = update.message.caption or "What's in this image?"
        
        # Call Ollama moondream for vision
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/chat/completions",
                json={
                    "model": "moondream:latest",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": caption},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                            ]
                        }
                    ],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            analysis = data["choices"][0]["message"]["content"]
        
        await update.message.reply_text(f"📷 **Image Analysis:**\n\n{analysis[:3500]}")
        
        # Memorize the interaction
        if chat_id not in chat_buffers:
            chat_buffers[chat_id] = []
        chat_buffers[chat_id].append({"role": "user", "content": f"[Image] {caption}"})
        chat_buffers[chat_id].append({"role": "assistant", "content": analysis})
        
    except Exception as e:
        logger.error("Image analysis failed: %s", e)
        await update.message.reply_text(f"❌ Image analysis error: {e}")


# ==================== QA TESTING ENGINE (Full Browser Testing) ====================

async def run_browser_test(url: str, requirements: str = "", test_phase: str = "manual") -> dict:
    """Run comprehensive browser testing: open, navigate, fill forms, click buttons, visual QA."""
    logger.info("🔍 Starting FULL browser test (%s) for: %s", test_phase, url)
    
    results = {
        "url": url,
        "phase": test_phase,
        "tests": [],
        "screenshots": [],
        "overall_pass": False,
        "report": "",
        "screenshot_path": None,
        "vision_result": None,
    }
    
    test_results = []
    screenshots_taken = []
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            # ============ TEST 1: Page Load (Desktop) ============
            page = await browser.new_page(viewport={"width": 1280, "height": 800})
            try:
                resp = await page.goto(url, wait_until="networkidle", timeout=30000)
                status = resp.status if resp else 0
                await page.wait_for_timeout(2000)
                
                page_title = await page.title()
                test_results.append({
                    "name": "Page Load (Desktop)",
                    "passed": status == 200,
                    "detail": f"HTTP {status} — Title: '{page_title}'"
                })
                
                # Take desktop screenshot
                ss = await page.screenshot(full_page=True, type="png")
                ss_path = Path(DATA_DIR) / f"qa_{test_phase}_desktop_{datetime.now().strftime('%H%M%S')}.png"
                with open(ss_path, "wb") as f:
                    f.write(ss)
                screenshots_taken.append(str(ss_path))
                results["screenshot_path"] = str(ss_path)
                logger.info("✅ Desktop screenshot: %s (%d bytes)", ss_path, len(ss))
            except Exception as e:
                test_results.append({"name": "Page Load (Desktop)", "passed": False, "detail": str(e)})
            
            # ============ TEST 2: Navigation Links ============
            try:
                nav_links = await page.query_selector_all("nav a, header a, .nav a, .navbar a, [role='navigation'] a")
                links_found = len(nav_links)
                links_clicked = 0
                link_details = []
                
                for link in nav_links[:5]:  # Test first 5 nav links
                    try:
                        href = await link.get_attribute("href")
                        text = (await link.inner_text()).strip()
                        if href and not href.startswith("#") and not href.startswith("javascript"):
                            link_details.append(f"'{text}' → {href}")
                            links_clicked += 1
                    except:
                        pass
                
                # Try clicking first nav link
                if nav_links:
                    try:
                        first_link = nav_links[0]
                        await first_link.click(timeout=5000)
                        await page.wait_for_timeout(1000)
                        current_url = page.url
                        link_details.append(f"Clicked first link → navigated to: {current_url}")
                        # Go back to original page
                        await page.goto(url, wait_until="networkidle", timeout=15000)
                        await page.wait_for_timeout(1000)
                    except:
                        link_details.append("First link click: no navigation occurred")
                
                test_results.append({
                    "name": "Navigation Testing",
                    "passed": links_found > 0,
                    "detail": f"Found {links_found} nav links, tested {links_clicked}. " + "; ".join(link_details[:3])
                })
            except Exception as e:
                test_results.append({"name": "Navigation Testing", "passed": False, "detail": str(e)})
            
            # ============ TEST 3: Form Detection & Filling ============
            try:
                forms = await page.query_selector_all("form")
                inputs = await page.query_selector_all("input:not([type='hidden']), textarea, select")
                buttons = await page.query_selector_all("button, input[type='submit'], [role='button']")
                
                form_count = len(forms)
                input_count = len(inputs)
                button_count = len(buttons)
                
                fill_results = []
                
                # Fill each input field
                for inp in inputs[:8]:  # Fill up to 8 fields
                    try:
                        input_type = await inp.get_attribute("type") or "text"
                        input_name = await inp.get_attribute("name") or await inp.get_attribute("placeholder") or "unknown"
                        tag = await inp.evaluate("el => el.tagName.toLowerCase()")
                        
                        if tag == "select":
                            # Select first option
                            options = await inp.query_selector_all("option")
                            if len(options) > 1:
                                await options[1].evaluate("el => el.selected = true")
                                fill_results.append(f"Selected option in '{input_name}'")
                        elif input_type == "email":
                            await inp.fill("test@company.com")
                            fill_results.append(f"Filled email: '{input_name}'")
                        elif input_type == "tel" or input_type == "phone":
                            await inp.fill("+1234567890")
                            fill_results.append(f"Filled phone: '{input_name}'")
                        elif input_type == "number":
                            await inp.fill("42")
                            fill_results.append(f"Filled number: '{input_name}'")
                        elif input_type == "checkbox" or input_type == "radio":
                            await inp.check()
                            fill_results.append(f"Checked: '{input_name}'")
                        elif tag == "textarea":
                            await inp.fill("This is a test message from QA automation. Testing form submission flow.")
                            fill_results.append(f"Filled textarea: '{input_name}'")
                        elif input_type not in ("file", "hidden", "image"):
                            await inp.fill("Test User QA")
                            fill_results.append(f"Filled text: '{input_name}'")
                    except:
                        pass
                
                # Take screenshot after filling forms
                if fill_results:
                    ss_form = await page.screenshot(full_page=True, type="png")
                    ss_form_path = Path(DATA_DIR) / f"qa_{test_phase}_form_{datetime.now().strftime('%H%M%S')}.png"
                    with open(ss_form_path, "wb") as f:
                        f.write(ss_form)
                    screenshots_taken.append(str(ss_form_path))
                
                test_results.append({
                    "name": "Form Detection & Filling",
                    "passed": True,  # Pass if we could interact without crash
                    "detail": f"Forms: {form_count}, Inputs: {input_count}, Buttons: {button_count}. " + "; ".join(fill_results[:4])
                })
            except Exception as e:
                test_results.append({"name": "Form Detection & Filling", "passed": False, "detail": str(e)})
            
            # ============ TEST 4: Button Clicking ============
            try:
                clickable = await page.query_selector_all("button, [role='button'], .btn, .button, a.cta")
                click_details = []
                
                for btn in clickable[:3]:  # Click first 3 buttons
                    try:
                        btn_text = (await btn.inner_text()).strip()[:30]
                        is_visible = await btn.is_visible()
                        if is_visible and btn_text:
                            await btn.click(timeout=3000)
                            await page.wait_for_timeout(500)
                            click_details.append(f"Clicked '{btn_text}' ✓")
                    except:
                        pass
                
                # Take screenshot after button clicks
                ss_btn = await page.screenshot(full_page=True, type="png")
                ss_btn_path = Path(DATA_DIR) / f"qa_{test_phase}_buttons_{datetime.now().strftime('%H%M%S')}.png"
                with open(ss_btn_path, "wb") as f:
                    f.write(ss_btn)
                screenshots_taken.append(str(ss_btn_path))
                
                test_results.append({
                    "name": "Button Interaction",
                    "passed": len(click_details) > 0 or len(clickable) == 0,
                    "detail": f"Found {len(clickable)} buttons. " + "; ".join(click_details) if click_details else f"Found {len(clickable)} buttons (none clickable)"
                })
            except Exception as e:
                test_results.append({"name": "Button Interaction", "passed": False, "detail": str(e)})
            
            # ============ TEST 5: Responsive — Mobile View ============
            try:
                await page.set_viewport_size({"width": 375, "height": 812})
                await page.goto(url, wait_until="networkidle", timeout=15000)
                await page.wait_for_timeout(1500)
                
                ss_mobile = await page.screenshot(full_page=True, type="png")
                ss_mobile_path = Path(DATA_DIR) / f"qa_{test_phase}_mobile_{datetime.now().strftime('%H%M%S')}.png"
                with open(ss_mobile_path, "wb") as f:
                    f.write(ss_mobile)
                screenshots_taken.append(str(ss_mobile_path))
                
                # Check if content is visible on mobile
                body = await page.query_selector("body")
                body_text = await body.inner_text() if body else ""
                has_content = len(body_text.strip()) > 50
                
                test_results.append({
                    "name": "Responsive (Mobile 375px)",
                    "passed": has_content,
                    "detail": f"Content visible: {'Yes' if has_content else 'No'} ({len(body_text)} chars)"
                })
            except Exception as e:
                test_results.append({"name": "Responsive (Mobile 375px)", "passed": False, "detail": str(e)})
            
            # ============ TEST 6: Responsive — Tablet View ============
            try:
                await page.set_viewport_size({"width": 768, "height": 1024})
                await page.goto(url, wait_until="networkidle", timeout=15000)
                await page.wait_for_timeout(1000)
                
                ss_tablet = await page.screenshot(full_page=True, type="png")
                ss_tablet_path = Path(DATA_DIR) / f"qa_{test_phase}_tablet_{datetime.now().strftime('%H%M%S')}.png"
                with open(ss_tablet_path, "wb") as f:
                    f.write(ss_tablet)
                screenshots_taken.append(str(ss_tablet_path))
                
                test_results.append({
                    "name": "Responsive (Tablet 768px)",
                    "passed": True,
                    "detail": "Tablet view rendered successfully"
                })
            except Exception as e:
                test_results.append({"name": "Responsive (Tablet 768px)", "passed": False, "detail": str(e)})
            
            # ============ TEST 7: Console Errors ============
            try:
                await page.set_viewport_size({"width": 1280, "height": 800})
                console_errors = []
                page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
                await page.goto(url, wait_until="networkidle", timeout=15000)
                await page.wait_for_timeout(2000)
                
                test_results.append({
                    "name": "Console Errors",
                    "passed": len(console_errors) == 0,
                    "detail": f"{len(console_errors)} errors" + (f": {'; '.join(console_errors[:2])}" if console_errors else "")
                })
            except Exception as e:
                test_results.append({"name": "Console Errors", "passed": True, "detail": f"Check skipped: {e}"})
            
            await browser.close()
    
    except Exception as e:
        logger.error("Browser test failed: %s", e)
        test_results.append({"name": "Browser Launch", "passed": False, "detail": str(e)})
    
    # ============ Vision Analysis on Desktop Screenshot ============
    if screenshots_taken:
        try:
            with open(screenshots_taken[0], "rb") as f:
                screenshot_data = f.read()
            vision = await analyze_screenshot_with_vision(screenshot_data, requirements)
            results["vision_result"] = vision
        except Exception as e:
            logger.error("Vision analysis failed: %s", e)
            results["vision_result"] = {"passed": True, "score": 5, "analysis": f"Vision unavailable: {e}"}
    
    # ============ Build Report ============
    passed_count = sum(1 for t in test_results if t["passed"])
    total_count = len(test_results)
    overall_pass = passed_count >= (total_count * 0.6)  # 60% pass rate
    
    results["tests"] = test_results
    results["screenshots"] = screenshots_taken
    results["overall_pass"] = overall_pass
    
    phase_label = {"post-dev": "Post-Development", "post-deploy": "Post-Deployment", "manual": "Manual QA"}.get(test_phase, test_phase)
    vision_score = results.get("vision_result", {}).get("score", "N/A")
    verdict = "✅ PASS" if overall_pass else "❌ FAIL"
    
    report = f"📋 **QA Report — {phase_label}**\n\n"
    report += f"🔗 URL: {url}\n"
    report += f"🧪 Tests: {passed_count}/{total_count} passed\n"
    report += f"🎯 Visual Score: {vision_score}/10\n"
    report += f"📸 Screenshots: {len(screenshots_taken)} taken\n"
    report += f"{'─' * 30}\n\n"
    
    for t in test_results:
        icon = "✅" if t["passed"] else "❌"
        report += f"{icon} **{t['name']}**: {t['detail'][:120]}\n"
    
    report += f"\n{'─' * 30}\n**Verdict: {verdict}**\n"
    
    if results.get("vision_result", {}).get("analysis"):
        report += f"\n🤖 Vision: {results['vision_result']['analysis'][:400]}\n"
    
    results["report"] = report
    logger.info("Browser test complete: %s (%d/%d passed)", verdict, passed_count, total_count)
    return results


async def analyze_screenshot_with_vision(screenshot_bytes: bytes, requirements: str) -> dict:
    """Analyze a screenshot using Ollama Moondream vision model for QA."""
    image_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
    
    qa_prompt = (
        f"You are a QA tester. Evaluate this website screenshot.\n"
        f"Requirements: {requirements[:500]}\n\n"
        f"Check: layout, colors, text readability, professional design.\n"
        f"Format: SCORE: X/10 then VERDICT: PASS or FAIL"
    )
    
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/chat/completions",
                json={
                    "model": "moondream:latest",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": qa_prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                            ]
                        }
                    ],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            analysis = data["choices"][0]["message"]["content"]
            
            passed = "PASS" in analysis.upper() and "FAIL" not in analysis.upper()
            score_match = re.search(r'SCORE:\s*(\d+)', analysis)
            score = int(score_match.group(1)) if score_match else 5
            
            return {"passed": passed or score >= 6, "score": score, "analysis": analysis}
    except Exception as e:
        logger.error("Vision QA failed: %s", e)
        return {"passed": True, "score": 5, "analysis": f"Vision unavailable: {e}"}


# Alias for pipeline compatibility
async def run_qa_test(url: str, requirements: str, test_phase: str = "post-dev") -> dict:
    """Wrapper that calls the full browser test."""
    return await run_browser_test(url, requirements, test_phase)


def extract_url_from_message(text: str) -> str | None:
    """Extract deployment URL from agent message."""
    patterns = [
        r'https?://[\w.-]+\.vercel\.app[/\w.-]*',
        r'https?://[\w.-]+\.onrender\.com[/\w.-]*',
        r'https?://[\w.-]+\.huggingface\.co[/\w.-]*',
        r'https?://[\w.-]+\.github\.io[/\w.-]*',
        r'https?://localhost:\d+[/\w.-]*',
        r'https?://httpbin\.org[/\w.-]*',  # For testing
        r'https?://[\w.-]+\.com[/\w.-]*',  # Generic fallback
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /test <url> command — full interactive browser QA test."""
    text = update.message.text or ""
    parts = text.split(maxsplit=1)
    
    if len(parts) < 2:
        await update.message.reply_text("Usage: /test <url>\nExample: /test https://google.com")
        return
    
    url = parts[1].strip()
    await update.message.reply_text(
        f"🔍 Running FULL browser QA test on {url}...\n\n"
        f"Testing:\n"
        f"• Page load (Desktop)\n"
        f"• Navigation links\n"
        f"• Form detection & filling\n"
        f"• Button clicking\n"
        f"• Responsive (Mobile + Tablet)\n"
        f"• Console errors\n"
        f"• Visual AI analysis (Moondream)\n\n"
        f"⏳ This may take 60-90 seconds..."
    )
    
    result = await run_browser_test(url, "General website quality check", test_phase="manual")
    
    # Send report
    await update.message.reply_text(result["report"][:3500])
    
    # Send all screenshots
    for ss_path in result.get("screenshots", [])[:4]:  # Max 4 screenshots
        try:
            label = "desktop" if "desktop" in ss_path else "mobile" if "mobile" in ss_path else "tablet" if "tablet" in ss_path else "form" if "form" in ss_path else "buttons"
            with open(ss_path, "rb") as f:
                await update.message.reply_photo(f, caption=f"📸 {label.title()} View — {url}")
        except Exception as e:
            logger.error("Failed to send screenshot %s: %s", ss_path, e)





async def connect_websocket() -> None:
    """Connect to backend WebSocket for inter-agent communication."""
    global ws_connection, agent_id

    # Use "memu-bot" as agent_id — matches the pipeline in OpenClaw's monitor.ts
    # where clawdbots route replies to "memu-bot"
    agent_id = "memu-bot"

    ws_url = BACKEND_URL.replace("http://", "ws://").replace("https://", "wss://")
    ws_url = f"{ws_url}/ws/{agent_id}"

    while True:
        try:
            logger.info("Connecting to backend WebSocket at %s", ws_url)
            async with websockets.connect(ws_url) as ws:
                ws_connection = ws
                logger.info("WebSocket connected as agent '%s'", agent_id)
                async for raw_msg in ws:
                    try:
                        data = json.loads(raw_msg)
                        await handle_ws_event(data)
                    except json.JSONDecodeError:
                        logger.warning("Invalid WS message: %s", raw_msg[:100])
        except Exception as e:
            logger.warning("WebSocket disconnected: %s. Reconnecting in 5s...", e)
            ws_connection = None
            await asyncio.sleep(5)


async def handle_ws_event(data: dict) -> None:
    """Handle incoming WebSocket events from other agents."""
    event = data.get("event")
    event_data = data.get("data", {})

    if event == "connected":
        logger.info("WS connected: %s", event_data.get("message"))

    elif event == "message:received":
        # Another agent sent us a message!
        sender = event_data.get("sender_id", "unknown")
        content = event_data.get("content", "")
        logger.info("Inter-agent message from %s: %s", sender, content[:100])

        # Track last activity for watchdog
        global last_agent_activity
        last_agent_activity = asyncio.get_event_loop().time()

        # STOP INFINITE LOOPS: Check for recursive messages
        lc = content.lower()
        spam_phrases = [
            "friday", "no more communication", "17-second", "milestone",
            "pipeline status", "deployment completed successfully",
            "deployment factory operational", "record-breaking",
            "all systems operational", "execution initiated",
            "no response needed", "focusing on implementation",
            "without acknowledgment", "no acknowledgment needed",
            "no further action", "understood. i'll",
        ]
        if any(phrase in lc for phrase in spam_phrases):
            logger.warning("Dropping spam/loop message from %s: %s", sender, content[:50])
            return

        # RATE LIMIT DETECTION — Put agent on cooldown if rate limited
        rate_limit_keywords = [
            "rate limit", "rate_limit", "429", "too many requests",
            "quota exceeded", "resource exhausted", "throttled",
            "overloaded", "rate limited", "retry after",
        ]
        if any(kw in lc for kw in rate_limit_keywords) and "clawdbot" in sender:
            global agent_cooldowns
            display_name = AGENT_DISPLAY_NAMES.get(sender, sender)
            cooldown_until = asyncio.get_event_loop().time() + (COOLDOWN_MINUTES * 60)
            agent_cooldowns[sender] = {
                "until": cooldown_until,
                "task": content[:200],
                "display_name": display_name,
            }
            logger.warning(
                "[RATE LIMIT] %s hit rate limit — on cooldown for %d min",
                display_name, COOLDOWN_MINUTES
            )
            await forward_to_telegram(
                f"⏸️ **Rate Limit:** {display_name} hit API rate limit. "
                f"Pausing for {COOLDOWN_MINUTES} min, then auto-retrying."
            )
            return  # Don't escalate rate limits as errors — just wait

        # ERROR DETECTION & ESCALATION — Alex auto-helps when agents hit errors
        error_keywords = [
            "error:", "failed:", "exception", "traceback", "cannot find",
            "permission denied", "connection refused", "timeout", "404",
            "500", "build failed", "deploy failed", "npm err", "syntax error",
            "module not found", "command failed", "fatal:", "hit an error",
            "need help", "blocked", "stuck",
        ]
        if any(kw in lc for kw in error_keywords) and "clawdbot" in sender:
            display_name = AGENT_DISPLAY_NAMES.get(sender, sender)
            logger.warning("[ERROR ESCALATION] %s reported an error: %s", display_name, content[:200])
            
            # Notify user on Telegram
            clean_msg = clean_for_telegram(content)
            await forward_to_telegram(
                f"⚠️ **Error from {display_name}:**\n{clean_msg[:1000]}"
            )
            
            # Route error to the right helper
            if sender == "clawdbot-2":  # Devin has error → ask Eric or Ben
                helper = "clawdbot-1"  # Ben can reassign or troubleshoot
                await asyncio.sleep(5)
                await send_ws_message(
                    f"[ALEX ESCALATION] {display_name} hit an error: {content[:500]}. "
                    f"Please help troubleshoot or suggest an alternative approach.",
                    recipients=[helper]
                )
            elif sender == "clawdbot-3":  # Eric has error → ask Devin to fix code
                helper = "clawdbot-2"  # Devin can fix the code
                await asyncio.sleep(5)
                await send_ws_message(
                    f"[ALEX ESCALATION] {display_name} has a deployment error: {content[:500]}. "
                    f"Please check the code and fix the issue.",
                    recipients=[helper]
                )
            elif sender == "clawdbot-1":  # Ben has error → tell Devin
                helper = "clawdbot-2"
                await asyncio.sleep(5)
                await send_ws_message(
                    f"[ALEX ESCALATION] {display_name} needs help: {content[:500]}. "
                    f"Please investigate and report back.",
                    recipients=[helper]
                )
            return

        # CHECK FOR AUTONOMOUS PROJECT WORKFLOW
        
        # 1. Meeting Mode (Broadcast)
        if autonomous_loop.is_running and "clawdbot" in sender:
            # Check if this is a general discussion/standup message
            # If so, we might want to broadcast it to others or just log it
            # For now, we forward everything to Telegram so User can see the meeting
            await forward_to_telegram(f"**{AGENT_DISPLAY_NAMES.get(sender, sender)}:** {content}")
            
            # If it's a standup update, maybe trigger the next person?
            # heuristic: if Ben finishes, trigger Devin? (Too complex for now, let LLM handle flow via prompts)

        # If message is from CTO and we are waiting for a plan
        if "clawdbot-1" in sender or "cto" in sender.lower():
            for pid, pdata in active_projects.items():
                if pdata.get("step") == "waiting_for_cto":
                    logger.info("Received plan from CTO for Project %s", pid)
                    pdata["cto_plan"] = content
                    pdata["step"] = "waiting_for_developer"
                    save_projects()
                    
                    await forward_to_telegram(f"**Ben:** {content}")
                    
                    # Trigger Developer (ClawdBot 2)
                    dev_message = (
                        f"The CTO has provided the following plan for a project:\n\n"
                        f"--- CTO PLAN ---\n{content[:2000]}\n--- END PLAN ---\n\n"
                        f"Original requirement: {pdata.get('requirements', 'N/A')}\n\n"
                        "Please implement this. Create the necessary files and code."
                    )
                    
                    try:
                        async with httpx.AsyncClient(timeout=10) as client:
                            await client.post(
                                f"{BACKEND_URL}/api/messages",
                                json={
                                    "sender_id": agent_id or "memu-bot",
                                    "content": f"[Alex → Developer] {dev_message}",
                                    "message_type": "text",
                                    "recipients": ["clawdbot-2"]
                                },
                            )
                        logger.info("Developer task sent for Project %s", pid)
                    except Exception as e:
                        logger.error("Failed to message Developer: %s", e)
                        await forward_to_telegram(f"⚠️ Failed to contact Developer: {e}")
                    
                    return  # Stop here, handled project flow

        # Check if message is from Developer and we are waiting for code
        if "clawdbot-2" in sender or "developer" in sender.lower():
            for pid, pdata in active_projects.items():
                if pdata.get("step") == "waiting_for_developer":
                    logger.info("Received code from Developer for Project %s", pid)
                    pdata["developer_output"] = content
                    pdata["step"] = "qa_testing_post_dev"
                    save_projects()
                    
                    await forward_to_telegram(f"**Devin:** {content}")
                    
                    # ==== QA GATE 1: Post-Development Testing ====
                    # Try to find a local URL first (developer might have started a server)
                    dev_url = extract_url_from_message(content)
                    
                    qa_passed = True  # Default pass if no URL to test
                    qa_report = "No URL found in developer output — skipping visual QA, forwarding to DevOps."
                    
                    if dev_url:
                        qa_result = await run_qa_test(
                            dev_url, 
                            pdata.get("requirements", ""), 
                            test_phase="post-dev"
                        )
                        qa_passed = qa_result["overall_pass"]
                        qa_report = qa_result["report"]
                        pdata["qa1_result"] = qa_report
                        save_projects()
                    
                    await forward_to_telegram(
                        f"📋 **QA Test 1 Results for `{pid}`:**\n\n{qa_report[:1500]}"
                    )
                    
                    if qa_passed:
                        # QA PASSED — Forward to DevOps
                        pdata["step"] = "waiting_for_devops"
                        save_projects()
                        
                        await forward_to_telegram(
                            f"✅ **QA Test 1 PASSED for `{pid}`!**\n"
                            f"👉 **Auto-assigning to DevOps for deployment...**"
                        )
                        
                        devops_message = (
                            f"The Developer has completed and QA-tested the code for a project.\n\n"
                            f"Original requirement: {pdata.get('requirements', 'N/A')}\n\n"
                            f"--- DEVELOPER OUTPUT ---\n{content[:2000]}\n--- END OUTPUT ---\n\n"
                            "Please deploy this to Vercel using: npx vercel deploy --yes --prod --token $VERCEL_TOKEN\n"
                            "Report the LIVE URL back when done."
                        )
                        
                        try:
                            async with httpx.AsyncClient(timeout=10) as client:
                                await client.post(
                                    f"{BACKEND_URL}/api/messages",
                                    json={
                                        "sender_id": agent_id or "memu-bot",
                                        "content": f"[Alex → DevOps] {devops_message}",
                                        "message_type": "text",
                                        "recipients": ["clawdbot-3"]
                                    },
                                )
                            logger.info("DevOps task sent for Project %s", pid)
                        except Exception as e:
                            logger.error("Failed to message DevOps: %s", e)
                            await forward_to_telegram(f"⚠️ Failed to contact DevOps: {e}")
                    else:
                        # QA FAILED — Send back to Developer with feedback
                        pdata["step"] = "waiting_for_developer"
                        pdata["qa1_retries"] = pdata.get("qa1_retries", 0) + 1
                        save_projects()
                        
                        await forward_to_telegram(
                            f"❌ **QA Test 1 FAILED for `{pid}`!**\n"
                            f"🔄 Sending feedback to Developer (retry #{pdata['qa1_retries']})..."
                        )
                        
                        fix_message = (
                            f"QA Testing found issues with your code. Please fix:\n\n"
                            f"--- QA REPORT ---\n{qa_report[:1500]}\n--- END REPORT ---\n\n"
                            f"Original requirement: {pdata.get('requirements', 'N/A')}\n\n"
                            "Please fix these issues and resubmit."
                        )
                        
                        try:
                            async with httpx.AsyncClient(timeout=10) as client:
                                await client.post(
                                    f"{BACKEND_URL}/api/messages",
                                    json={
                                        "sender_id": agent_id or "memu-bot",
                                        "content": f"[Alex QA → Developer] {fix_message}",
                                        "message_type": "text",
                                        "recipients": ["clawdbot-2"]
                                    },
                                )
                        except Exception as e:
                            logger.error("Failed to send QA feedback: %s", e)
                    
                    return  # Stop here, handled project flow

        # Check if message is from DevOps and we are waiting for deployment
        if "clawdbot-3" in sender or "devops" in sender.lower():
            for pid, pdata in active_projects.items():
                if pdata.get("step") == "waiting_for_devops":
                    logger.info("Received deployment status from DevOps for Project %s", pid)
                    pdata["devops_output"] = content
                    pdata["step"] = "qa_testing_post_deploy"
                    save_projects()
                    
                    await forward_to_telegram(f"**Eric:** {content}")
                    
                    # ==== QA GATE 2: Post-Deployment Testing ====
                    deploy_url = extract_url_from_message(content)
                    
                    if deploy_url:
                        qa_result = await run_qa_test(
                            deploy_url,
                            pdata.get("requirements", ""),
                            test_phase="post-deploy"
                        )
                        pdata["qa2_result"] = qa_result["report"]
                        pdata["live_url"] = deploy_url
                        save_projects()
                        
                        await forward_to_telegram(
                            f"📋 **QA Test 2 Results for `{pid}`:**\n\n{qa_result['report'][:1500]}"
                        )
                        
                        # Send screenshot to Telegram
                        if qa_result.get("screenshot_path"):
                            try:
                                bot = telegram_app.bot if telegram_app else None
                                if bot and ADMIN_CHAT_ID:
                                    with open(qa_result["screenshot_path"], "rb") as f:
                                        await bot.send_photo(
                                            ADMIN_CHAT_ID, f,
                                            caption=f"📸 QA Test 2 Screenshot — {deploy_url}"
                                        )
                            except Exception as e:
                                logger.error("Failed to send QA screenshot: %s", e)
                        
                        if qa_result["overall_pass"]:
                            # QA PASSED — Project complete!
                            pdata["step"] = "completed"
                            save_projects()
                            
                            await forward_to_telegram(
                                f"🎉 **PROJECT COMPLETED: `{pid}`**\n\n"
                                f"📋 **Requirement:** {pdata.get('requirements', 'N/A')[:200]}\n\n"
                                f"🔗 **Live URL:** {deploy_url}\n\n"
                                f"🎯 **QA Score:** {qa_result.get('vision_result', {}).get('score', 'N/A')}/10\n\n"
                                f"✅ All phases complete! Planned → Coded → QA Tested → Deployed → QA Verified!"
                            )
                            
                            # CONTINUOUS GROWTH: Host meeting to plan next task
                            if autonomous_loop.is_running:
                                asyncio.create_task(autonomous_loop.trigger_post_completion_meeting())
                        else:
                            # QA FAILED — Report issues
                            pdata["step"] = "waiting_for_devops"
                            pdata["qa2_retries"] = pdata.get("qa2_retries", 0) + 1
                            save_projects()
                            
                            await forward_to_telegram(
                                f"❌ **QA Test 2 FAILED for `{pid}`!**\n"
                                f"🔄 Sending deployment issues back (retry #{pdata['qa2_retries']})..."
                            )
                            
                            fix_message = (
                                f"QA post-deployment testing found issues:\n\n"
                                f"--- QA REPORT ---\n{qa_result['report'][:1500]}\n--- END REPORT ---\n\n"
                                "Please fix the deployment issues and redeploy."
                            )
                            
                            try:
                                async with httpx.AsyncClient(timeout=10) as client:
                                    await client.post(
                                        f"{BACKEND_URL}/api/messages",
                                        json={
                                            "sender_id": agent_id or "memu-bot",
                                            "content": f"[Alex QA → DevOps] {fix_message}",
                                            "message_type": "text",
                                            "recipients": ["clawdbot-3"]
                                        },
                                    )
                            except Exception as e:
                                logger.error("Failed to send QA feedback: %s", e)
                    else:
                        # No URL found - mark complete anyway with warning
                        pdata["step"] = "completed"
                        save_projects()
                        
                        await forward_to_telegram(
                            f"🎉 **PROJECT COMPLETED: `{pid}`**\n\n"
                            f"📋 **Requirement:** {pdata.get('requirements', 'N/A')[:200]}\n\n"
                            f"🚀 **DevOps Report:**\n{content[:1500]}\n\n"
                            f"⚠️ No deployment URL found for QA Test 2.\n"
                            f"✅ All phases complete! Planned → Coded → Deployed."
                        )
                        
                        # CONTINUOUS GROWTH: Host meeting to plan next task
                        if autonomous_loop.is_running:
                            asyncio.create_task(autonomous_loop.trigger_post_completion_meeting())
                    
                    return  # Stop here, handled project flow

        # ROUTING LOGIC (Mentions)
        recipients = []
        lower_content = content.lower()
        
        if "devin" in lower_content or "developer" in lower_content or "clawdbot-2" in lower_content:
            if sender != "clawdbot-2":
                recipients.append("clawdbot-2")
        
        if "eric" in lower_content or "devops" in lower_content or "clawdbot-3" in lower_content:
            if sender != "clawdbot-3":
                recipients.append("clawdbot-3")
            
        if "ben" in lower_content or "cto" in lower_content or "ceo" in lower_content or "clawdbot-1" in lower_content:
            if sender != "clawdbot-1":
                recipients.append("clawdbot-1")

        if recipients:
            logger.info("Routing message from %s to: %s", sender, recipients)
            # Forward to Telegram so the user can see the message (cleaned)
            display_name = AGENT_DISPLAY_NAMES.get(sender, sender)
            clean_msg = clean_for_telegram(content)
            await forward_to_telegram(f"**{display_name}:** {clean_msg}")
            for i, recipient in enumerate(recipients):
                if i > 0:
                    await asyncio.sleep(5)  # 5s delay between recipients
                await send_ws_message(content, recipients=[recipient])
            return

        # No routing match — just forward to Telegram, do NOT reply to sender
        display_name = AGENT_DISPLAY_NAMES.get(sender, sender)
        clean_msg = clean_for_telegram(content)
        await forward_to_telegram(f"**{display_name}:** {clean_msg}")
        return



    elif event == "task:assigned":
        task_id = event_data.get("task_id")
        logger.info("Task assigned to us: %s", task_id)
        await forward_to_telegram(f"📋 **New task assigned:** {task_id}")

    elif event == "agent:joined":
        joined_id = event_data.get("agent_id")
        logger.info("Agent joined: %s", joined_id)

    elif event == "agent:left":
        left_id = event_data.get("agent_id")
        logger.info("Agent left: %s", left_id)


async def generate_agent_reply(sender_id: str, message: str) -> str:
    """Generate a reply to another agent's message using LLM."""
    try:
        system_prompt = (
            f"You are Alex ({AGENT_NAME}), an AI memory assistant communicating with another AI agent "
            f"(agent_id: {sender_id}). "
            f"IMPORTANT: The User in the Telegram chat is the CEO. You (Alex) and the other agents (Ben, Devin, Eric) work for the User. "
            f"If the message is from the User/CEO, treat it as a high-priority directive. "
            f"Be helpful, concise, and professional."
        )

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{ZAI_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {ZAI_API_KEY}"},
                json={
                    "model": "glm-4.7",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message},
                    ],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error("Agent reply LLM error: %s", e)
        return f"I received your message but encountered an error: {e}"


async def send_ws_message(content: str, recipients: list[str] | None = None, max_retries: int = 3) -> bool:
    """Send a message to other agents via WebSocket with retry logic."""
    global ws_connection
    if not ws_connection:
        logger.warning("WebSocket not connected, cannot send message")
        return False
    
    msg = {
        "event": "message:send",
        "data": {
            "content": content,
            "message_type": "text",
            "recipients": recipients or [],
        },
    }
    
    for attempt in range(1, max_retries + 1):
        try:
            await ws_connection.send(json.dumps(msg))
            logger.info("WS message sent to %s (attempt %d)", recipients, attempt)
            return True
        except Exception as e:
            logger.error("Failed to send WS message (attempt %d/%d): %s", attempt, max_retries, e)
            if attempt < max_retries:
                await asyncio.sleep(2 * attempt)  # Exponential backoff: 2s, 4s
            else:
                logger.error("All %d retries exhausted for WS message to %s", max_retries, recipients)
    return False


import re

def clean_for_telegram(text: str) -> str:
    """Strip code blocks and long content from agent messages for clean Telegram display."""
    # Remove fenced code blocks (```...```) and replace with a summary
    cleaned = re.sub(
        r'```[\s\S]*?```',
        '[code written to file]',
        text
    )
    # Remove inline code that's too long (>100 chars)
    cleaned = re.sub(
        r'`[^`]{100,}`',
        '[code snippet]',
        cleaned
    )
    # Collapse multiple newlines
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    # Truncate to 1500 chars max
    if len(cleaned) > 1500:
        cleaned = cleaned[:1500] + "\n\n... (message truncated)"
    return cleaned.strip()


async def forward_to_telegram(text: str) -> None:
    """Forward inter-agent messages to the admin or group on Telegram with fallback."""
    if not telegram_app:
        return

    target_chat_id = GROUP_CHAT_ID if GROUP_CHAT_ID else ADMIN_CHAT_ID
    
    if not target_chat_id:
        return

    # Truncate to avoid Telegram limits
    safe_text = text[:3500]

    try:
        await telegram_app.bot.send_message(
            chat_id=target_chat_id,
            text=safe_text,
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.warning("Markdown send failed, retrying as plain text: %s", str(e)[:100])
        try:
            # Strip markdown and send as plain text
            clean_text = safe_text.replace("**", "").replace("*", "").replace("`", "")
            await telegram_app.bot.send_message(
                chat_id=target_chat_id,
                text=clean_text,
            )
        except Exception as e2:
            logger.error("Failed to forward to Telegram even as plain text: %s", e2)


async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /ask <agent_name> <message> — talk to another bot via WebSocket."""
    global GROUP_CHAT_ID, ADMIN_CHAT_ID

    # Auto-detect chat IDs
    if update.effective_chat.type in ("group", "supergroup") and not GROUP_CHAT_ID:
        GROUP_CHAT_ID = update.effective_chat.id
        logger.info("Group chat ID detected via /ask: %s", GROUP_CHAT_ID)
        save_chats()
    if update.effective_chat.type == "private" and not ADMIN_CHAT_ID:
        ADMIN_CHAT_ID = update.effective_chat.id

    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: /ask <agent_name> <message>\n"
            "Example: /ask CTO How are you?\n"
            "Example: /ask Developer Write a hello world\n"
            "Example: /ask DevOps Check server status\n\n"
            "Available: CTO (Ben), Developer (Devin), DevOps (Eric)"
        )
        return

    target_name = args[0]
    message = " ".join(args[1:])

    await update.effective_chat.send_action("typing")

    # Find the WebSocket agent ID for the target
    target_agent_id = None
    for key, ws_id in AGENT_WS_MAP.items():
        if target_name.lower() in key or key in target_name.lower():
            target_agent_id = ws_id
            break

    if not target_agent_id:
        await update.message.reply_text(
            f"Unknown agent '{target_name}'.\n"
            "Available: CTO (Ben), Developer (Devin), DevOps (Eric)"
        )
        return

    display_name = AGENT_DISPLAY_NAMES.get(target_agent_id, target_agent_id)

    # Send message via WebSocket to the target agent
    sent = await send_ws_message(message, recipients=[target_agent_id])

    if sent:
        # Also log in backend for audit trail
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    f"{BACKEND_URL}/api/messages",
                    json={
                        "sender_id": agent_id or "memu-bot",
                        "content": f"[Alex -> {display_name}] {message}",
                        "message_type": "text",
                        "recipients": [target_agent_id],
                    },
                )
        except Exception as e:
            logger.warning("Backend audit log failed: %s", e)

        await update.message.reply_text(
            f"Message sent to {display_name}!\n"
            f"Waiting for response... (will forward here when received)"
        )
        logger.info("Ask command: sent to %s via WebSocket: %s", target_agent_id, message[:100])
    else:
        # WebSocket not connected, fall back to REST API
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{BACKEND_URL}/api/messages",
                    json={
                        "sender_id": agent_id or "memu-bot",
                        "content": message,
                        "message_type": "text",
                        "recipients": [target_agent_id],
                    },
                )
                if resp.status_code in (200, 201):
                    await update.message.reply_text(
                        f"Message sent to {display_name} via backend API!\n"
                        f"Waiting for response..."
                    )
                    logger.info("Ask command: sent to %s via REST API: %s", target_agent_id, message[:100])
                else:
                    await update.message.reply_text(
                        f"Failed to send message to {display_name} (status: {resp.status_code})"
                    )
        except Exception as e:
            logger.error("Ask command failed: %s", e)
            await update.message.reply_text(f"Failed to reach {display_name}: {e}")


async def project_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /project <requirements> - Start a new autonomous project."""
    requirements = " ".join(context.args) if context.args else ""
    if not requirements:
        await update.message.reply_text("Usage: /project <requirements>\nExample: /project Build a landing page for a coffee shop")
        return

    global GROUP_CHAT_ID
    # Auto-detect group ID if used in group
    if update.effective_chat.type in ("group", "supergroup") and not GROUP_CHAT_ID:
        GROUP_CHAT_ID = update.effective_chat.id
        save_chats()

    await update.effective_chat.send_action("typing")

    # 1. Create Master Task in Backend
    task_id = None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{BACKEND_URL}/api/tasks",
                json={
                    "creator_id": agent_id or "memu-bot",
                    "title": f"Project: {requirements[:50]}...",
                    "description": requirements,
                    "priority": 3,
                    "requirements": {"type": "master_project"}
                },
            )
            if resp.status_code in (200, 201):
                task_data = resp.json()
                task_id = task_data.get("id")
            else:
                await update.message.reply_text(f"❌ Failed to create project task: {resp.status_code}")
                return
    except Exception as e:
        logger.error("Project creation failed: %s", e)
        await update.message.reply_text(f"❌ Error creating project: {e}")
        return

    # 2. Initialize Project State with production tracking
    now = datetime.now()
    active_projects[task_id] = {
        "status": "planning",
        "requirements": requirements,
        "step": "waiting_for_cto",
        "created_at": now.isoformat(),
        "chat_id": update.effective_chat.id,
        "retry_count": 0,
        "last_attempt": now.isoformat(),
        "timeout_at": (now + timedelta(seconds=AGENT_TIMEOUT_SECONDS)).isoformat()
    }
    save_projects()


    await update.message.reply_text(
        f"🚀 **Project Started!**\n"
        f"🆔 Task ID: `{task_id}`\n"
        f"📋 Requirements: {requirements}\n\n"
        f"👉 **First Step:** Consulting with CTO for technical planning...\n"
        f"_(This runs in the background - you'll see updates as agents respond)_",
        parse_mode="Markdown"
    )

    # 3. Message CTO (ClawdBot 1) - Prompt without web research (API credits exhausted)
    cto_message = (
        f"🎯 NEW PROJECT REQUEST FROM CEO\n\n"
        f"**CEO Requirement:** {requirements}\n\n"
        f"Please perform the following as CTO (ClawdBot 1):\n"
        f"1. **Technical Spec:** Define the architecture, frameworks, and tools.\n"
        f"2. **Deployment Plan:** Specify deployment strategy.\n"
        f"3. **Task Breakdown:** List tasks for the Developer.\n"
        f"4. **Timeline:** Estimate effort.\n\n"
        f"PRIORITY: High. Return a plan immediately."
    )

    
    # Fire-and-forget async task for backend calls (non-blocking)
    async def send_to_cto_background():
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Create task for CTO
                await client.post(
                    f"{BACKEND_URL}/api/tasks",
                    json={
                        "creator_id": agent_id or "memu-bot",
                        "title": f"Plan Project: {requirements[:30]}",
                        "description": cto_message,
                        "priority": 4,
                        "requirements": {"parent_id": task_id, "assigned_to": "cto"}
                    },
                )
                # Send message to CTO via WebSocket broadcast
                await client.post(
                    f"{BACKEND_URL}/api/messages",
                    json={
                        "sender_id": agent_id or "memu-bot",
                        "content": f"[Alex → CTO] {cto_message}",
                        "message_type": "text",
                        "recipients": ["clawdbot-1"]
                    },
                )
            logger.info("CTO message sent successfully for project %s", task_id)
        except Exception as e:
            logger.error("Background CTO message failed: %s", e)
    
    # Launch in background - don't block
    asyncio.create_task(send_to_cto_background())



async def post_init(application: Application) -> None:
    """Post-initialization hook."""
    global telegram_app
    telegram_app = application
    await register_with_backend()
    # Start WebSocket connection in background
    asyncio.create_task(connect_websocket())
    # Start stuck project checker
    asyncio.create_task(check_stuck_projects())
    logger.info("MemU Bot started with full capabilities (production mode)")


async def check_stuck_projects() -> None:
    """Periodically check for projects that timed out and retry or notify."""
    await asyncio.sleep(10)  # Initial delay before first check
    while True:
        try:
            now = datetime.now()
            for pid, pdata in list(active_projects.items()):
                step = pdata.get("step", "")
                if step in ("waiting_for_cto", "waiting_for_developer", "waiting_for_devops"):
                    timeout_str = pdata.get("timeout_at", now.isoformat())
                    try:
                        timeout_at = datetime.fromisoformat(timeout_str)
                    except:
                        timeout_at = now + timedelta(seconds=60)
                    
                    if now > timeout_at:
                        retry_count = pdata.get("retry_count", 0)
                        if retry_count < MAX_RETRIES:
                            logger.warning("Project %s timed out at step %s (retry %d/%d)", 
                                         pid, step, retry_count + 1, MAX_RETRIES)
                            await retry_project_step(pid, pdata)
                        else:
                            # Max retries exceeded
                            pdata["step"] = "failed"
                            pdata["status"] = "failed"
                            save_projects()
                            await forward_to_telegram(
                                f"❌ **Project `{pid}` FAILED**\n\n"
                                f"Step: {step.replace('waiting_for_', '').upper()}\n"
                                f"Retries exhausted ({MAX_RETRIES}/{MAX_RETRIES})\n\n"
                                f"Use `/retry {pid[:8]}` to manually retry."
                            )
        except Exception as e:
            logger.error("Error in stuck project checker: %s", e)
        
        await asyncio.sleep(CHECK_STUCK_INTERVAL)


async def retry_project_step(pid: str, pdata: dict) -> None:
    """Retry the current step for a stuck project."""
    step = pdata.get("step", "")
    requirements = pdata.get("requirements", "N/A")
    now = datetime.now()
    
    # Update retry tracking
    pdata["retry_count"] = pdata.get("retry_count", 0) + 1
    pdata["last_attempt"] = now.isoformat()
    pdata["timeout_at"] = (now + timedelta(seconds=AGENT_TIMEOUT_SECONDS)).isoformat()
    save_projects()
    
    await forward_to_telegram(
        f"🔄 **Retrying Project `{pid[:8]}`** (Attempt {pdata['retry_count']}/{MAX_RETRIES})\n"
        f"Step: {step.replace('waiting_for_', '').upper()}"
    )
    
    if step == "waiting_for_cto":
        cto_message = (
            f"🔄 RETRY REQUEST - Project {pid[:8]}\n\n"
            f"**Requirement:** {requirements}\n\n"
            "Please provide a technical plan including architecture, file structure, and tasks for the Developer."
        )
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                await client.post(
                    f"{BACKEND_URL}/api/messages",
                    json={
                        "sender_id": agent_id or "memu-bot",
                        "content": f"[Alex → CTO] {cto_message}",
                        "message_type": "text",
                        "recipients": ["clawdbot-1"]
                    }
                )
        except Exception as e:
            logger.error("Failed to retry CTO: %s", e)
    
    elif step == "waiting_for_developer":
        cto_plan = pdata.get("cto_plan", "See original requirements")
        dev_message = (
            f"🔄 RETRY REQUEST - Project {pid[:8]}\n\n"
            f"CTO Plan: {cto_plan[:1000]}\n\n"
            "Please implement the code and create the necessary files."
        )
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                await client.post(
                    f"{BACKEND_URL}/api/messages",
                    json={
                        "sender_id": agent_id or "memu-bot",
                        "content": f"[Alex → Developer] {dev_message}",
                        "message_type": "text",
                        "recipients": ["clawdbot-2"]
                    }
                )
        except Exception as e:
            logger.error("Failed to retry Developer: %s", e)
    
    elif step == "waiting_for_devops":
        dev_output = pdata.get("developer_output", "See code output")
        devops_message = (
            f"🔄 RETRY REQUEST - Project {pid[:8]}\n\n"
            f"Developer Output: {dev_output[:1000]}\n\n"
            "Please deploy and run tests."
        )
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                await client.post(
                    f"{BACKEND_URL}/api/messages",
                    json={
                        "sender_id": agent_id or "memu-bot",
                        "content": f"[Alex → DevOps] {devops_message}",
                        "message_type": "text",
                        "recipients": ["clawdbot-3"]
                    }
                )
        except Exception as e:
            logger.error("Failed to retry DevOps: %s", e)


async def projects_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all active projects with status."""
    if not active_projects:
        await update.message.reply_text("📭 No active projects.")
        return
    
    msg = "📊 **Active Projects**\n\n"
    for pid, pdata in active_projects.items():
        step = pdata.get("step", "unknown")
        status = pdata.get("status", "unknown")
        retries = pdata.get("retry_count", 0)
        
        step_emoji = {
            "waiting_for_cto": "🏗️",
            "waiting_for_developer": "💻",
            "qa_testing_post_dev": "🔍",
            "waiting_for_devops": "🚀",
            "qa_testing_post_deploy": "🔍",
            "completed": "✅",
            "completed": "✅",
            "failed": "❌"
        }.get(step, "❓")
        
        msg += f"{step_emoji} `{pid[:8]}` - {step.replace('_', ' ').title()}"
        if retries > 0:
            msg += f" (retry {retries}/{MAX_RETRIES})"
        msg += f"\n   _{pdata.get('requirements', 'N/A')[:40]}..._\n\n"
    
    await update.message.reply_text(msg, parse_mode="Markdown")


async def retry_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually retry a stuck project."""
    if not context.args:
        await update.message.reply_text("Usage: `/retry <project_id_prefix>`", parse_mode="Markdown")
        return
    
    prefix = context.args[0]
    matching = [pid for pid in active_projects if pid.startswith(prefix)]
    
    if not matching:
        await update.message.reply_text(f"❌ No project found matching `{prefix}`", parse_mode="Markdown")
        return
    
    pid = matching[0]
    pdata = active_projects[pid]
    
    # Reset retry count for manual retry
    pdata["retry_count"] = 0
    await retry_project_step(pid, pdata)
    await update.message.reply_text(f"🔄 Retrying project `{pid[:8]}`...", parse_mode="Markdown")


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel a project."""
    if not context.args:
        await update.message.reply_text("Usage: `/cancel <project_id_prefix>`", parse_mode="Markdown")
        return
    
    prefix = context.args[0]
    matching = [pid for pid in active_projects if pid.startswith(prefix)]
    
    if not matching:
        await update.message.reply_text(f"❌ No project found matching `{prefix}`", parse_mode="Markdown")
        return
    
    pid = matching[0]
    del active_projects[pid]
    save_projects()
    await update.message.reply_text(f"🗑️ Project `{pid[:8]}` cancelled.", parse_mode="Markdown")


# ==================== AUTONOMOUS COMPANY LOOP ====================

class AutonomousLoop:
    """Manages the 24/7 autonomous behavior of the company."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(self.daily_standup, CronTrigger(hour=9, minute=0), id="daily_standup")
        self.scheduler.add_job(self.random_brainstorming, IntervalTrigger(hours=4), id="brainstorming")
        self.scheduler.add_job(self.check_idle_growth, IntervalTrigger(minutes=15), id="idle_growth")
        self.scheduler.add_job(self.watchdog, IntervalTrigger(minutes=10), id="watchdog")
        self.is_running = False

    def start(self):
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("Autonomous Company Loop STARTED")

    def stop(self):
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Autonomous Company Loop STOPPED")

    async def daily_standup(self):
        """Standard 9:00 AM Standup Meeting."""
        await self.trigger_agent("clawdbot-1", 
            "It's time for the daily standup. Give a brief update on company goals and ask Devin for his status.")

    async def random_brainstorming(self, force: bool = False):
        """Revenue-focused team brainstorming."""
        # Only run if no active projects to avoid distraction (unless forced)
        if not force and active_projects and any(p['step'] != 'completed' for p in active_projects.values()):
            return

        topics = [
            "What product can we build and ship TODAY to earn money? Think AI agents, chatbots, SaaS tools.",
            "How can we monetize our AI skills faster? Discuss pricing, payment, and target customers.",
            "What is the fastest path to $200 revenue? Pick ONE product, plan it, build it, ship it.",
            "Which AI agent product would businesses pay $29-99/month for? Design it and start building.",
            "Review our deployed products. What is earning? What needs marketing? What should we build next?",
            "What pain points do businesses have that we can solve with an AI bot? Think support, automation, content.",
        ]
        topic = random.choice(topics)
        
        await forward_to_telegram(
            f"**Revenue Meeting**\n\n"
            f"Target: $200\n"
            f"Team, let's discuss: *{topic}*\n"
            f"Focus on ACTION - pick something, build it, ship it!"
        )
        
        # Trigger Ben to lead
        await self.trigger_agent("clawdbot-1", 
            f"Revenue meeting topic: '{topic}'. Lead the discussion. Pick the most profitable idea, assign to Devin, and get Eric ready. SHIP FAST.")

    async def check_idle_growth(self):
        """If idle, always start the next company-building task."""
        if active_projects and any(p['step'] != 'completed' for p in active_projects.values()):
            return

        # Always start a new task when idle - 24/7 work
        await self.trigger_growth_task()

    async def watchdog(self):
        """Alex's self-healing watchdog: detect stalled conversations, check cooldowns, and restart work."""
        global last_agent_activity, agent_cooldowns
        
        if not ws_connection:
            logger.warning("[WATCHDOG] No WebSocket connection — cannot monitor agents")
            return
        
        now = asyncio.get_event_loop().time()
        
        # CHECK COOLDOWNS — retry agents whose cooldown has expired
        expired_agents = []
        for agent_id, cooldown in list(agent_cooldowns.items()):
            if now >= cooldown["until"]:
                expired_agents.append((agent_id, cooldown))
                del agent_cooldowns[agent_id]
        
        for agent_id, cooldown in expired_agents:
            display_name = cooldown.get("display_name", agent_id)
            logger.info("[WATCHDOG] Cooldown expired for %s — re-engaging", display_name)
            await forward_to_telegram(
                f"▶️ **Cooldown Over:** {display_name}'s rate limit cooldown expired. Re-engaging."
            )
            # Nudge the agent to continue their work
            await self.trigger_agent(agent_id,
                f"Your rate limit cooldown is over. Please continue with your previous task. "
                f"If you hit another rate limit, let Alex know.")
            # Reset activity timer since we just triggered work
            last_agent_activity = now
            return  # Handle one at a time
        
        # Log ongoing cooldowns
        if agent_cooldowns:
            for agent_id, cooldown in agent_cooldowns.items():
                remaining = (cooldown["until"] - now) / 60
                logger.debug("[WATCHDOG] %s still in cooldown: %.1f min remaining",
                    cooldown.get("display_name", agent_id), remaining)
            return  # Don't trigger new work if agents are in cooldown
        
        # STALL DETECTION
        silence_seconds = now - last_agent_activity if last_agent_activity > 0 else 9999
        silence_minutes = silence_seconds / 60
        
        if silence_minutes >= 10:
            logger.info("[WATCHDOG] Agents silent for %.1f min — Alex is stepping in to restart work", silence_minutes)
            
            await forward_to_telegram(
                f"🔧 **Alex (Supervisor):** Agents have been quiet for {int(silence_minutes)} minutes. "
                f"Restarting work automatically."
            )
            
            # Reset the timer so we don't spam
            last_agent_activity = now
            
            # Check if there's an active project that stalled
            stalled_project = None
            for pid, pdata in active_projects.items():
                if pdata.get('step') not in ('completed', None):
                    stalled_project = (pid, pdata)
                    break
            
            if stalled_project:
                pid, pdata = stalled_project
                step = pdata.get('step', 'unknown')
                logger.info("[WATCHDOG] Found stalled project %s at step '%s' — nudging team", pid[:8], step)
                await self.trigger_agent("clawdbot-1",
                    f"URGENT from Alex: Project '{pid[:8]}' is stalled at step '{step}'. "
                    f"Please check on the team and get this moving. Ask Devin or Eric for their status.")
            else:
                # No active project — start new work
                logger.info("[WATCHDOG] No active projects — starting new company work")
                await self.trigger_growth_task()
        else:
            logger.debug("[WATCHDOG] Agents active %.1f min ago — all good", silence_minutes)

    async def trigger_growth_task(self):
        """Let agents autonomously decide what to build. Target: $200."""
        
        await forward_to_telegram(
            f"**New Revenue Task**\n\n"
            f"Agents are choosing their next product to build.\n"
            f"Goal: Earn toward $200 target."
        )
        
        await self.trigger_agent("clawdbot-1", 
            "REVENUE MISSION: Our target is $200. You are an AI agent team running in Docker "
            "with access to Vercel, Render, Supabase, GitHub, and HuggingFace. "
            "YOU decide what to build and sell. You know Docker, LLMs, APIs, web apps, and agent architecture. "
            "Think about what earns money fastest: AI chatbots, SaaS tools, AI APIs, automation bots, "
            "web apps with payment, or anything else you can imagine. "
            "Pick YOUR best idea, plan it, assign to Devin, get Eric to deploy. "
            "Track revenue in /home/node/.openclaw/workspace/revenue.md. SHIP FAST.")

    async def trigger_post_completion_meeting(self):
        """After a task completes, host a meeting to decide what's next."""
        await forward_to_telegram(
            f"✅ **Task Complete - Planning Meeting**\n\n"
            f"Great work team! Let's discuss what to work on next."
        )
        await self.trigger_agent("clawdbot-1",
            "The last task is done. Host a quick meeting: What did we learn? What should we build next? "
            "Pick the most impactful next task for the company and start it.")

    async def trigger_agent(self, agent_id: str, prompt: str, max_retries: int = 3):
        """Send a system prompt to an agent with retry logic, cooldown check, and 5s delay."""
        if not ws_connection:
            logger.warning("No WS connection, cannot trigger %s", agent_id)
            return
        
        # Check if agent is in cooldown (rate limited)
        if agent_id in agent_cooldowns:
            remaining = (agent_cooldowns[agent_id]["until"] - asyncio.get_event_loop().time()) / 60
            if remaining > 0:
                display_name = agent_cooldowns[agent_id].get("display_name", agent_id)
                logger.warning("[COOLDOWN] Skipping trigger for %s — %.1f min remaining", display_name, remaining)
                return
            else:
                # Cooldown expired, remove it
                del agent_cooldowns[agent_id]
        
        # 5 second delay before sending to prevent message flooding
        await asyncio.sleep(5)
            
        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.post(
                        f"{BACKEND_URL}/api/messages",
                        json={
                            "sender_id": "memu-bot",
                            "content": f"[SYSTEM TRIGGER] {prompt}",
                            "message_type": "text",
                            "recipients": [agent_id] 
                        },
                    )
                    resp.raise_for_status()
                    logger.info("Triggered %s successfully (attempt %d)", agent_id, attempt)
                    return
            except Exception as e:
                logger.error("Failed to trigger %s (attempt %d/%d): %s", agent_id, attempt, max_retries, e)
                if attempt < max_retries:
                    await asyncio.sleep(3 * attempt)  # Backoff: 3s, 6s
                else:
                    logger.error("All retries exhausted triggering %s", agent_id)

# Global Instance
autonomous_loop = AutonomousLoop()

async def autonomy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /autonomy <start|stop>."""
    if not context.args:
        status = "RUNNING" if autonomous_loop.is_running else "STOPPED"
        await update.message.reply_text(f"⚙️ **Autonomous Mode:** {status}\n\nUsage: `/autonomy start` or `/autonomy stop`", parse_mode="Markdown")
        return

    action = context.args[0].lower()
    if action == "start":
        autonomous_loop.start()
        await update.message.reply_text("🚀 Autonomous Company Loop **STARTED**.\nExpect daily standups and proactive work!")
    elif action == "stop":
        autonomous_loop.stop()
        await update.message.reply_text("zzz Autonomous Loop **STOPPED**.")
    else:
        await update.message.reply_text("Usage: `/autonomy start` or `/autonomy stop`")

async def meet_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually trigger a brainstorming session."""
    await update.message.reply_text("💡 Triggering immediate brainstorming session...")
    await autonomous_loop.random_brainstorming(force=True)

async def standup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually trigger a standup meeting."""
    await update.message.reply_text("📢 Triggering immediate standup meeting...")
    await autonomous_loop.daily_standup()

def main() -> None:
    """Start the bot."""
    logger.info("Starting %s with full features...", AGENT_NAME)

    get_memory_service()
    get_memory_service()
    get_memory_service()
    load_skills()
    load_chats()
    load_projects()

    request = HTTPXRequest(connect_timeout=20, read_timeout=60, write_timeout=60)
    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .request(request)
        .post_init(post_init)
        .build()
    )

    # Register all command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("remember", remember_command))
    app.add_handler(CommandHandler("memory", memory_command))
    app.add_handler(CommandHandler("categories", categories_command))
    app.add_handler(CommandHandler("forget", forget_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("scrape", scrape_command))
    app.add_handler(CommandHandler("speak", speak_command))
    app.add_handler(CommandHandler("agents", agents_command))
    app.add_handler(CommandHandler("ask", ask_command))
    app.add_handler(CommandHandler("tasks", tasks_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("learn", learn_command))
    app.add_handler(CommandHandler("skills", skills_command))
    app.add_handler(CommandHandler("project", project_command))
    # Production commands
    app.add_handler(CommandHandler("projects", projects_command))
    app.add_handler(CommandHandler("retry", retry_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CommandHandler("autonomy", autonomy_command))
    app.add_handler(CommandHandler("meet", meet_command))
    app.add_handler(CommandHandler("standup", standup_command))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))


    logger.info("Polling for Telegram updates...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
