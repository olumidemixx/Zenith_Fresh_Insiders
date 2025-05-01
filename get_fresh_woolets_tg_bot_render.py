from single_traders import single_topTraders

from wallet_stats_prev import fresh_wallet_stats
from get_all_tokens_2  import getBondedTokens, getCompletingTokens
import os

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import asyncio
from typing import List, Set, Dict
import time
from concurrent.futures import ThreadPoolExecutor
from toptradersbysellsAndUnrealizedPSKipFirst100000Orso import topTraders,earlyBuyers,topHolders


from aiohttp import web
from pyngrok import ngrok
import logging
import re
import sys

from dotenv import load_dotenv

load_dotenv()  # Loads variables from .env

BOT_TOKEN = os.getenv('BOT_TOKEN')


# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("analyzing...")   
    all_tokens = getBondedTokens() + getCompletingTokens()
    

    all_wallets = single_topTraders(all_tokens[:20])
    

    fresh_insiders = fresh_wallet_stats(all_wallets)
    # Save fresh_insiders to a text file
    with open('fresh_insiders.txt', 'w') as f:
        f.write("if empty, it means there are no wallets is in the document before sending\n"+str(fresh_insiders))

    # Send the text file as a document
    with open('fresh_insiders.txt', 'rb') as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f)

    await update.message.reply_text("Analysis complete. Check the file below for details.")
    


from aiohttp import web
from pyngrok import ngrok
import logging
import sys
import asyncio

async def setup_webhook(application: Application, webhook_url: str):
    """Setup webhook for the bot"""
    webhook_path = f"/{BOT_TOKEN}"
    await application.bot.set_webhook(url=webhook_url + webhook_path)
    return webhook_path

async def handle_webhook(request):
    """Handle incoming webhook requests"""
    try:
        update = Update.de_json(await request.json(), application.bot)
        await application.process_update(update)
        return web.Response(status=200)
    except Exception as e:
        logging.error(f"Error processing update: {e}")
        return web.Response(status=500)

async def on_startup(web_app):
    """Setup webhook on startup"""
    global application
    
    try:
        # Initialize the application
        await application.initialize()
        await application.start()
        
        # Use Render URL from environment variable
        webhook_url = "https://zenithfinderbot.onrender.com"
        if not webhook_url:
            logging.error("RENDER_EXTERNAL_URL environment variable not found")
            await application.shutdown()
            sys.exit(1)
            
        logging.info(f"Using Render URL: {webhook_url}")
        
        # Setup webhook
        webhook_path = await setup_webhook(application, webhook_url)
        
        # Add webhook handler
        web_app.router.add_post(webhook_path, handle_webhook)
        
    except Exception as e:
        logging.error(f"Startup failed: {e}")
        await application.shutdown()
        sys.exit(1)

async def on_shutdown(web_app):
    logging.info("yeahhhhh")
    """Cleanup on shutdown"""
    #global application
    #await application.bot.delete_webhook()
    #await application.stop()
    #await application.shutdown()

    
    
def main():
    global application
    
    # Initialize the bot application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("analyze", analyze))
    web_app = web.Application()
    web_app.on_startup.append(on_startup)
    web_app.on_shutdown.append(on_shutdown)
    
    # Add home page route
    #web_app.router.add_get('/', home_page)

    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8443))
    
    # Start the web server
    # When running on Render, we need to bind to 0.0.0.0 instead of localhost
    host = '0.0.0.0' if os.environ.get("RENDER_EXTERNAL_URL") else 'localhost'
    web.run_app(web_app, host=host, port=port)

if __name__ == '__main__':
    main()

