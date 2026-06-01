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
    data = []
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()

    return data

async def get_sudoku_level(string81):
    url = f"https://www.thonky.com/sudoku/evaluate-sudoku?puzzlebox={string81}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            html = await resp.text()

    soup = BeautifulSoup(html, "html.parser")

    card = soup.find("div", class_="card text-bg-success p-3")
    if not card:
        return None

    big_texts = card.find_all("big")
    if len(big_texts) < 2:
        return None

    difficulty_info = big_texts[1].get_text(strip=True)

    return int(difficulty_info[-11:-10])

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
        f"Difficulty: {level}\n\n"
        f"<pre>{board}</pre>"
    )

async def send_daily_message(app):
    saved_message = None
    puzzles = await get_puzzle_string("https://sudoku.coach/beapi/get-puzzles/quick_puzzle_sudoku/5/36")

    for string81 in puzzles:
        level = await get_sudoku_level(string81['puzzle'])
        if level is None:
            continue

        saved_message = await format_sudoku_html(string81['puzzle'], level)

        if level > 3: # found a puzzle with difficulty greater than 3, use it and stop looking
            break

    await app.bot.send_message(
        chat_id=CHANNEL_ID,
        text=saved_message,
        parse_mode="HTML"
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