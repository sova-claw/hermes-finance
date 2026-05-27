"""Telegram bot handlers."""
import json
from typing import Any

import anthropic
import structlog
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import FSInputFile, Message

from hermess_api.core.config import settings
from hermess_api.domains.insights import queries
from hermess_api.domains.insights.tools import TOOLS, dispatch
from hermess_api.domains.sync.monobank import run_sync

log = structlog.get_logger(__name__)
router = Router()
claude = anthropic.Anthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT = """You are Hermess, a personal finance assistant with real-time access to the user's bank data from Monobank.

You can call tools to get account balances, spending breakdowns, trends, and generate charts.
Always answer in the same language the user writes in.
Be concise, friendly, and give actionable financial insights.
When showing amounts, include the currency (UAH, USD, EUR).
"""


def _owner_only(message: Message) -> bool:
    if message.from_user and message.from_user.id != settings.telegram_owner_id:
        return False
    return True


async def _ask_claude(user_message: str) -> tuple[str, list[str]]:
    """Send message to Claude with tool use. Returns (text_response, chart_paths)."""
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_message}]
    chart_paths: list[str] = []

    while True:
        response = claude.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            text = " ".join(
                block.text for block in response.content if hasattr(block, "text")
            )
            return text, chart_paths

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                log.info("tool_call", tool=block.name, input=block.input)
                try:
                    result = dispatch(block.name, block.input)
                    if isinstance(result, dict) and "file_path" in result:
                        chart_paths.append(result["file_path"])
                        tool_result_content = "Chart generated successfully."
                    else:
                        tool_result_content = json.dumps(result)
                except Exception as exc:
                    log.error("tool_error", tool=block.name, error=str(exc))
                    tool_result_content = f"Error: {exc}"

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": tool_result_content,
                })
            messages.append({"role": "user", "content": tool_results})
            continue

        # Unexpected stop reason
        break

    return "Sorry, I couldn't process that request.", chart_paths


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    if not _owner_only(message):
        return
    await message.answer(
        "👋 Hi! I'm Hermess, your personal finance assistant.\n\n"
        "I have access to your Monobank data. Try asking:\n"
        "• How much did I spend this month?\n"
        "• Show me a spending breakdown\n"
        "• What's my account balance?\n\n"
        "Commands:\n"
        "/status — account balances\n"
        "/sync — sync Monobank now\n"
        "/report — monthly summary with chart"
    )


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    if not _owner_only(message):
        return
    balances = queries.get_account_balances()
    if not balances:
        await message.answer("No accounts synced yet. Run /sync first.")
        return
    lines = [f"*{a['name']}*: {a['balance']:,.2f} {a['currency']}" for a in balances]
    await message.answer("\n".join(lines), parse_mode="Markdown")


@router.message(Command("sync"))
async def cmd_sync(message: Message) -> None:
    if not _owner_only(message):
        return
    await message.answer("🔄 Syncing Monobank... this may take a few minutes.")
    try:
        imported = run_sync()
        await message.answer(f"✅ Sync complete. {imported} new transactions imported.")
    except Exception as exc:
        log.error("sync_failed", error=str(exc))
        await message.answer(f"❌ Sync failed: {exc}")


@router.message(Command("report"))
async def cmd_report(message: Message) -> None:
    if not _owner_only(message):
        return
    text, charts = await _ask_claude("Give me a monthly spending summary with a category breakdown chart.")
    await message.answer(text, parse_mode="Markdown")
    for path in charts:
        await message.answer_photo(FSInputFile(path))


@router.message()
async def handle_message(message: Message) -> None:
    if not _owner_only(message) or not message.text:
        return
    thinking = await message.answer("💭 Thinking...")
    text, chart_paths = await _ask_claude(message.text)
    await thinking.delete()
    await message.answer(text, parse_mode="Markdown")
    for path in chart_paths:
        await message.answer_photo(FSInputFile(path))
