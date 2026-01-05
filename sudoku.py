import os
import asyncio
from telegram.ext import ApplicationBuilder
from PIL import Image
from playwright.sync_api import sync_playwright

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

def take_screenshot(url, output_file="input.png"):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage"]
        )
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")

        page.screenshot(path=output_file, full_page=True)
        
        browser.close()

def prep_sudoku_image():
    take_screenshot("https://www.websudoku.com/?level=4")

    img = Image.open("input.png")
    cropped_img = img.crop((578, 152, 578+432, 152+470))  # Define the crop box (left, upper, right, lower)
    
    # Save the cropped image
    cropped_img.save("output.png")

async def send_daily_message(app):
    prep_sudoku_image()

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