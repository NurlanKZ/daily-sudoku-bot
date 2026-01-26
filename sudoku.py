import os
import asyncio
from telegram.ext import ApplicationBuilder
from PIL import Image
from playwright.async_api import async_playwright

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

async def take_screenshot(url, output_file="input.png"):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage"]
        )
        page = await browser.new_page()

        # Use 'domcontentloaded' instead of 'networkidle' - faster and more reliable
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        
        # Wait a bit for dynamic content
        await asyncio.sleep(2)

        await page.screenshot(path=output_file, full_page=True)
        await browser.close()

async def prep_sudoku_image():
    await take_screenshot("https://www.websudoku.com/?level=4")
    
    img = Image.open("input.png")
    cropped_img = img.crop((578, 152, 578+432, 152+470))
    cropped_img.save("output.png")

async def send_daily_message(app):
    await prep_sudoku_image()

    # Use context manager to properly close the file
    with open('output.png', 'rb') as photo:
        await app.bot.send_photo(chat_id=CHANNEL_ID, photo=photo)

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