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

# Map agent names to Telegram bot usernames for group relay
AGENT_TELEGRAM_MAP = {
    "cto": "@codemurf_one_bot",
    "clawdbot 1": "@codemurf_one_bot",
    "clawdbot_1": "@codemurf_one_bot",
    "developer": "@codemurf_two_bot",
    "clawdbot 2": "@codemurf_two_bot",
    "clawdbot_2": "@codemurf_two_bot",
    "clawdbot 3": "@cowoker_devops_bot",
    "clawdbot_3": "@cowoker_devops_bot",
    "devops": "@cowoker_devops_bot",
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


def get_memory_service() -> MemoryService:
    """Initialize MemoryService with dual LLM profiles: ZAI for chat, Ollama for embeddings."""
    global memory_service
    if memory_service is not None:
        return memory_service

    memory_service = MemoryService(
        llm_profiles={
            # Default profile for chat/reasoning (ZAI GLM-4.5)
            "default": {
                "base_url": ZAI_BASE_URL,
                "api_key": ZAI_API_KEY,
                "chat_model": "glm-4.5",
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
        f"🧠 LLM: GLM-4.5 via ZAI\n"
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
                    "model": "glm-4.5",
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


async def connect_websocket() -> None:
    """Connect to backend WebSocket for inter-agent communication."""
    global ws_connection, agent_id

    if not agent_id:
        # Get our agent_id from the backend
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{BACKEND_URL}/api/agents")
                if resp.status_code == 200:
                    agents = resp.json()
                    for a in agents:
                        if a.get("name") == AGENT_NAME:
                            agent_id = a.get("id")
                            break
        except Exception as e:
            logger.warning("Could not fetch agent_id: %s", e)

    if not agent_id:
        agent_id = "memu-bot"  # Fallback ID

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

        # Generate a reply using LLM
        reply = await generate_agent_reply(sender, content)

        # Send reply back via WebSocket
        await send_ws_message(reply, recipients=[sender])

        # Forward to admin on Telegram
        await forward_to_telegram(
            f"📨 **Message from agent {sender}:**\n{content}\n\n"
            f"💬 **Alex replied:**\n{reply}"
        )

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
            f"(agent_id: {sender_id}). Be helpful, concise, and professional. "
            "You can help with memory retrieval, information lookup, and coordination."
        )

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{ZAI_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {ZAI_API_KEY}"},
                json={
                    "model": "glm-4.5",
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


async def send_ws_message(content: str, recipients: list[str] | None = None) -> bool:
    """Send a message to other agents via WebSocket."""
    global ws_connection
    if not ws_connection:
        logger.warning("WebSocket not connected, cannot send message")
        return False
    try:
        msg = {
            "event": "message:send",
            "data": {
                "content": content,
                "message_type": "text",
                "recipients": recipients or [],
            },
        }
        await ws_connection.send(json.dumps(msg))
        return True
    except Exception as e:
        logger.error("Failed to send WS message: %s", e)
        return False


async def forward_to_telegram(text: str) -> None:
    """Forward inter-agent messages to the admin or group on Telegram."""
    if not telegram_app:
        return

    # Prefer group chat if set, otherwise admin
    target_chat_id = GROUP_CHAT_ID if GROUP_CHAT_ID else ADMIN_CHAT_ID
    
    if not target_chat_id:
        return

    try:
        await telegram_app.bot.send_message(
            chat_id=target_chat_id,
            text=text[:4000],
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error("Failed to forward to Telegram: %s", e)


async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /ask <agent_name> <message> — talk to another bot."""
    global GROUP_CHAT_ID
    
    # Auto-detect group ID if used in group
    if update.effective_chat.type in ("group", "supergroup") and not GROUP_CHAT_ID:
        GROUP_CHAT_ID = update.effective_chat.id
        logger.info("Group chat ID detected via /ask: %s", GROUP_CHAT_ID)
        save_chats()

    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: /ask <agent_name> <message>\n"
            "Example: /ask CTO How are you?\n"
            "Example: /ask Developer Write a hello world\n"
            "Example: /ask DevOps Check server status\n\n"
            "Available: CTO, Developer, DevOps, ClawdBot_1, ClawdBot_2, ClawdBot_3"
        )
        return

    target_name = args[0]
    message = " ".join(args[1:])

    await update.effective_chat.send_action("typing")

    # Find the Telegram bot username for the target
    target_username = None
    for key, username in AGENT_TELEGRAM_MAP.items():
        if target_name.lower() in key or key in target_name.lower():
            target_username = username
            target_name = key.title()
            break

    if not target_username:
        await update.message.reply_text(
            f"Unknown agent '{target_name}'.\n"
            "Available: CTO, Developer, DevOps, ClawdBot_1, ClawdBot_2, ClawdBot_3"
        )
        return

    # Store message in backend
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Create a task for the target agent
            await client.post(
                f"{BACKEND_URL}/api/tasks",
                json={
                    "creator_id": agent_id or "memu-bot",
                    "title": f"Message from Alex: {message[:100]}",
                    "description": f"User asked Alex to relay to {target_name}: {message}",
                    "priority": 2,
                },
            )
            # Also store as a message
            await client.post(
                f"{BACKEND_URL}/api/messages",
                json={
                    "sender_id": agent_id or "memu-bot",
                    "content": f"[Alex → {target_name}] {message}",
                    "message_type": "text",
                },
            )
    except Exception as e:
        logger.warning("Backend logging failed: %s", e)

    # Give the user a ready-to-send message
    relay_msg = f"{target_username} {message}"
    await update.message.reply_text(
        f"📤 **Message for {target_name}:**\n\n"
        f"Telegram doesn't let bots talk to other bots directly. "
        f"Please send this in the group:\n\n"
        f"`{relay_msg}`\n\n"
        f"Just copy and paste it! I've also logged it in the backend.",
        parse_mode="Markdown",
    )
    logger.info("Ask command: prepared relay for %s: %s", target_name, message[:100])


async def post_init(application: Application) -> None:
    """Post-initialization hook."""
    global telegram_app
    telegram_app = application
    await register_with_backend()
    # Start WebSocket connection in background
    asyncio.create_task(connect_websocket())
    logger.info("MemU Bot started with full capabilities")


def main() -> None:
    """Start the bot."""
    logger.info("Starting %s with full features...", AGENT_NAME)

    get_memory_service()
    get_memory_service()
    load_skills()
    load_chats()

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
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    logger.info("Polling for Telegram updates...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
