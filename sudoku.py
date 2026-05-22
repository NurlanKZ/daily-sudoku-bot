import os
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from telegram.ext import ApplicationBuilder

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )
}

async def get_puzzle_string(url):
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            html = await response.text()

    soup = BeautifulSoup(html, "html.parser")

    inputs = soup.select("#puzzle_grid input")

    # Ensure we always produce 81 characters
    values = []
    for inp in inputs:
        val = inp.get("value")
        values.append(val if val and val.isdigit() else "0")

    string81 = "".join(values)

    if len(string81) != 81:
        raise ValueError(f"Expected 81 cells, got {len(string81)}")

    return string81

async def format_sudoku_html(puzzle: str, level: str = "Unknown") -> str:
    lines = []

    for r in range(9):
        row = []
        for c in range(9):
            val = puzzle[r * 9 + c]
            row.append(val if val != "0" else " ")

            if c in (2, 5):
                row.append("|")

        lines.append(" ".join(row))

        if r in (2, 5):
            lines.append("-" * 21)

    board = "\n".join(lines)

    return (
        f"<b>🧩 Sudoku</b>\n"
        f"<b>Difficulty:</b> {level}\n\n"
        f"<pre>{board}</pre>"
    )

async def send_daily_message(app):
    string81 = await get_puzzle_string("https://west.websudoku.com/?level=4")

    url = f"https://www.thonky.com/sudoku/evaluate-sudoku?puzzlebox={string81}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            html = await resp.text()

    soup = BeautifulSoup(html, "html.parser")

    # Find the target div
    card = soup.find("div", class_="card text-bg-success p-3")
    if not card:
        raise ValueError("Sudoku evaluation card not found")

    big_texts = card.find_all("big")

    if len(big_texts) < 2:
        raise ValueError("Unexpected HTML structure: missing difficulty info")

    difficulty_info = big_texts[1].get_text(strip=True)

    message_content = await format_sudoku_html(
        string81,
        level=difficulty_info[-11:-10]
    )

    await app.bot.send_message(
        chat_id=CHANNEL_ID,
        text=message_content,
        parse_mode="Markdown"
    )

async def run_app():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Start the application (polling won't be strictly necessary if only scheduling)
    await app.initialize()

    # Send the message WITHOUT starting the polling
    await send_daily_message(app)
    
    # Shutdown
    await app.shutdown()

if __name__ == '__main__':
    asyncio.run(run_app())  # Use asyncio.run() to run the async function