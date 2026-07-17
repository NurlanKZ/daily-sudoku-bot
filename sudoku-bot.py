import os
import random
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

async def fetch_puzzle(set_id):
    """Fetch a WebSudoku puzzle by set_id."""

    url = "https://west.websudoku.com/"

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.5",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://west.websudoku.com",
        "Pragma": "no-cache",
        "Referer": "https://west.websudoku.com/?select=1&level=4",
        "Sec-Fetch-Dest": "frame",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Sec-GPC": "1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/136.0.0.0 Mobile Safari/537.36"
        ),
        "sec-ch-ua": '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
    }

    cookies = {
        "options": "4",
        "seed": "CO1KA7YT1008O0GK4WOKGCCK0",
        "overlay": "6",
    }

    data = {
        "level": "4",
        "set_id": str(set_id),
        "goto": " Go to this puzzle ",
    }

    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with session.post(url, headers=headers, data=data) as response:
            response.raise_for_status()
            return await response.text()

async def get_puzzle_string(url):
    data = []
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()

    return data

def extract_sudoku(html: str) -> str:
    """
    Extract an 81-character Sudoku string from a WebSudoku HTML snippet.

    Filled cells are their digit ('1'-'9').
    Empty cells are represented as '0'.

    Returns:
        str: 81-character puzzle string.
    """
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", id="puzzle_grid")
    if table is None:
        raise ValueError("Could not find puzzle_grid table.")

    puzzle = []

    for row in table.find_all("tr"):
        cells = row.find_all("input")
        if len(cells) != 9:
            continue

        for cell in cells:
            puzzle.append(cell.get("value", "0"))

    if len(puzzle) != 81:
        raise ValueError(f"Expected 81 cells, found {len(puzzle)}")

    return "".join(puzzle)

async def send_daily_message(app):
    set_id = random.randint(4_025_000_000, 4_051_000_000)
    string81 = extract_sudoku(fetch_puzzle(set_id))

    link = f"https://sudoku.coach/en/solver/{string81}"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🧩 Open puzzle", url=link)]
    ])

    await app.bot.send_message(
        chat_id=CHANNEL_ID,
        text="Solve this puzzle:",
        reply_markup=keyboard,
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