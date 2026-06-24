import os
import asyncio
import aiohttp
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

async def get_puzzle_string(url):
    data = []
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()

    return data

def string_to_grid(s: str):
    """
    Convert an 81-character string into a 9x9 grid (list of lists).
    Assumes row-major order.
    """
    if len(s) != 81:
        raise ValueError("Input string must be exactly 81 characters long.")

    # Optional: validate characters
    if not all(c.isdigit() for c in s):
        raise ValueError("Input must contain only digits 0-9.")

    grid = []
    for i in range(0, 81, 9):
        row = [int(ch) for ch in s[i:i+9]]
        grid.append(row)

    return grid

async def get_sudoku_level(puzzle_string):
    url = "https://ozerlyn.com/api/backend-proxy"
    params = {
        "endpoint": "/api/sudoku/calculate-se-rating"
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    payload = {
        "grid": string_to_grid(puzzle_string)
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=params, json=payload, headers=headers) as r:
            data = await r.json()

            # Debug output (IMPORTANT)
            print("API response:", data)

            if "se_rating" not in data:
                return None  # or handle differently

            return str(data["se_rating"])[0]


async def send_daily_message(app):
    puzzles = await get_puzzle_string("https://sudoku.coach/beapi/get-puzzles/quick_puzzle_sudoku/5/1")

    for item in puzzles:
        level = await get_sudoku_level(item['puzzle'])

        if level == "3":
            link = f"https://sudoku.coach/en/solver/{item['puzzle']}"
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