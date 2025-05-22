from http.server import BaseHTTPRequestHandler
import json
import os
import uuid
import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
import re

# Environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
WEBAPP_BASE_URL = os.environ.get('WEBAPP_BASE_URL', 'https://your-app.vercel.app')

# Global video storage
VIDEOS_STORE = {}

class VideoProcessor:
    @staticmethod
    def is_valid_url(url: str) -> bool:
        return url.startswith(('http://', 'https://')) and '.' in url
    
    @staticmethod
    def extract_video_title(video_url: str) -> str:
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
        VIDEOS_STORE[video_id] = {
            "id": video_id,
            "url": video_url,
            "added_by": username,
            "title": VideoProcessor.extract_video_title(video_url)
        }

async def process_message(bot, message):
    """Process incoming message"""
    try:
        text = message.get('text', '').strip()
        user = message.get('from', {})
        username = user.get('username') or user.get('first_name', 'Unknown')
        chat_id = message.get('chat', {}).get('id')
        
        # Handle commands
        if text == '/start':
            welcome_message = (
                "🎬 Welcome to Video Hosting Bot!\n\n"
                "Send me a video URL and I'll:\n"
                "• Create a post in the channel\n"
                "• Add the video to our webapp\n"
                "• Provide a watch button for users\n\n"
                "Just send me any video URL to get started!"
            )
            await bot.send_message(chat_id=chat_id, text=welcome_message)
            return
        
        elif text == '/help':
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
            await bot.send_message(chat_id=chat_id, text=help_message)
            return
        
        # Process video URL
        if not VideoProcessor.is_valid_url(text):
            await bot.send_message(
                chat_id=chat_id, 
                text="❌ Please send a valid video URL.\nExample: https://www.youtube.com/watch?v=VIDEO_ID"
            )
            return
        
        # Generate video ID and save
        video_id = str(uuid.uuid4())
        VideoProcessor.save_video(video_id, text, username)
        
        # Create webapp URL
        webapp_url = f"{WEBAPP_BASE_URL}/watch/{video_id}"
        video_title = VideoProcessor.extract_video_title(text)
        
        # Create channel post
        post_message = f"🎬 New Video Available!\n\n📺 {video_title}\n\nClick the button below to watch:"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🎥 Watch Video", url=webapp_url)
        ]])
        
        # Send to channel
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=post_message,
            reply_markup=keyboard
        )
        
        # Confirm to user
        await bot.send_message(
            chat_id=chat_id,
            text=f"✅ Video added successfully!\n\n🆔 Video ID: `{video_id}`\n🔗 Original URL: {text}\n🌐 Watch URL: {webapp_url}\n\nThe post has been created in the channel!",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        print(f"Error processing message: {e}")
        try:
            await bot.send_message(
                chat_id=chat_id,
                text="❌ An error occurred while processing your message. Please try again."
            )
        except:
            pass

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        try:
            if self.path == '/api/webhook':
                # Health check
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {"status": "Bot webhook is running", "path": self.path}
                self.wfile.write(json.dumps(response).encode())
                
            elif self.path.startswith('/api/video/'):
                # Get specific video
                video_id = self.path.split('/')[-1]
                video_info = VIDEOS_STORE.get(video_id)
                
                if video_info:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(video_info).encode())
                else:
                    self.send_response(404)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Video not found"}).encode())
                    
            elif self.path == '/api/videos':
                # Get all videos
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(VIDEOS_STORE).encode())
                
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Not found"}).encode())
                
        except Exception as e:
            print(f"GET error: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def do_POST(self):
        """Handle POST requests (webhooks)"""
        try:
            if self.path != '/api/webhook':
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Not found"}).encode())
                return
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "No data received"}).encode())
                return
                
            post_data = self.rfile.read(content_length)
            update_data = json.loads(post_data.decode('utf-8'))
            
            # Check if it's a message
            if 'message' not in update_data:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok - no message"}).encode())
                return
            
            message = update_data['message']
            
            # Create bot instance and process message
            bot = Bot(token=BOT_TOKEN)
            
            # Process message asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(process_message(bot, message))
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode())
                
            except Exception as e:
                print(f"Message processing error: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Processing error: {str(e)}"}).encode())
                
            finally:
                loop.close()
                
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
            
        except Exception as e:
            print(f"POST error: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

# Export video functions for the web app
def get_video_info(video_id: str):
    """Get video information by ID"""
    return VIDEOS_STORE.get(video_id)

def get_all_videos():
    """Get all videos"""
    return VIDEOS_STORE
