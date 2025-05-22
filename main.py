import os
import json
import uuid
from urllib.parse import quote
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application
import re

# Environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')  # @channel_username or -1001234567890
WEBAPP_BASE_URL = os.environ.get('WEBAPP_BASE_URL', 'https://your-app.vercel.app')

# Simple in-memory storage (in production, use a proper database)
VIDEOS_STORE = {}

class VideoProcessor:
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Basic URL validation"""
        return url.startswith(('http://', 'https://')) and '.' in url
    
    @staticmethod
    def extract_video_title(video_url: str) -> str:
        """Extract video title from URL"""
        if 'youtube.com' in video_url or 'youtu.be' in video_url:
            return "YouTube Video"
        elif 'vimeo.com' in video_url:
            return "Vimeo Video"
        elif 'tiktok.com' in video_url:
            return "TikTok Video"
        elif 'instagram.com' in video_url:
            return "Instagram Video"
        else:
            return "Video Content"
    
    @staticmethod
    def save_video(video_id: str, video_url: str, username: str = "Unknown"):
        """Save video to storage"""
        VIDEOS_STORE[video_id] = {
            "id": video_id,
            "url": video_url,
            "added_by": username,
            "title": VideoProcessor.extract_video_title(video_url)
        }

async def process_video_url(update: Update, context):
    """Process video URL and create channel post"""
    try:
        video_url = update.message.text.strip()
        
        # Validate URL
        if not VideoProcessor.is_valid_url(video_url):
            await update.message.reply_text(
                "❌ Please send a valid video URL.\n"
                "Example: https://www.youtube.com/watch?v=VIDEO_ID"
            )
            return
        
        # Generate unique video ID
        video_id = str(uuid.uuid4())
        username = update.effective_user.username or update.effective_user.first_name or "Unknown"
        
        # Save video info
        VideoProcessor.save_video(video_id, video_url, username)
        
        # Create webapp URL
        webapp_url = f"{WEBAPP_BASE_URL}/watch/{video_id}"
        
        # Get video title
        video_title = VideoProcessor.extract_video_title(video_url)
        
        # Create channel post
        post_message = (
            f"🎬 New Video Available!\n\n"
            f"📺 {video_title}\n\n"
            f"Click the button below to watch:"
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎥 Watch Video", url=webapp_url)]
        ])
        
        # Send to channel
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=post_message,
            reply_markup=keyboard
        )
        
        # Confirm to user
        await update.message.reply_text(
            f"✅ Video added successfully!\n\n"
            f"🆔 Video ID: `{video_id}`\n"
            f"🔗 Original URL: {video_url}\n"
            f"🌐 Watch URL: {webapp_url}\n\n"
            f"The post has been created in the channel!",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        print(f"Error processing video: {e}")
        await update.message.reply_text(
            "❌ An error occurred while processing your video. Please try again."
        )

async def start_command(update: Update, context):
    """Handle /start command"""
    welcome_message = (
        "🎬 Welcome to Video Hosting Bot!\n\n"
        "Send me a video URL and I'll:\n"
        "• Create a post in the channel\n"
        "• Add the video to our webapp\n"
        "• Provide a watch button for users\n\n"
        "Just send me any video URL to get started!"
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context):
    """Handle /help command"""
    help_message = (
        "🔧 How to use this bot:\n\n"
        "1. Send me a video URL (YouTube, Vimeo, TikTok, etc.)\n"
        "2. I'll process it and create a channel post\n"
        "3. Users can click 'Watch Video' to view it\n\n"
        "Supported formats:\n"
        "• YouTube URLs\n"
        "• Vimeo URLs\n"
        "• TikTok URLs\n"
        "• Instagram URLs\n"
        "• Direct video file URLs"
    )
    await update.message.reply_text(help_message)

# Webhook handler for Vercel
async def webhook_handler(request_data):
    """Handle incoming webhook from Telegram"""
    try:
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        from telegram.ext import CommandHandler, MessageHandler, filters
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_video_url))
        
        # Process update
        update = Update.de_json(request_data, application.bot)
        await application.process_update(update)
        
        return {"statusCode": 200, "body": "OK"}
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"statusCode": 500, "body": f"Error: {str(e)}"}

# Export the video store for the web app
def get_video_info(video_id: str):
    """Get video information by ID"""
    return VIDEOS_STORE.get(video_id)

def get_all_videos():
    """Get all videos"""
    return VIDEOS_STORE