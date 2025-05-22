import requests
import os

# Configuration - Replace with your actual values
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
WEBHOOK_URL = "https://your-app-name.vercel.app/api/webhook"

def set_webhook():
    """Set webhook for the Telegram bot"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    data = {
        "url": WEBHOOK_URL,
        "allowed_updates": ["message"]
    }
    
    response = requests.post(url, data=data)
    result = response.json()
    
    if result.get("ok"):
        print("✅ Webhook set successfully!")
        print(f"Webhook URL: {WEBHOOK_URL}")
    else:
        print("❌ Failed to set webhook")
        print(f"Error: {result.get('description', 'Unknown error')}")

def get_webhook_info():
    """Get current webhook information"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    response = requests.get(url)
    result = response.json()
    
    if result.get("ok"):
        webhook_info = result.get("result", {})
        print("📋 Current webhook info:")
        print(f"URL: {webhook_info.get('url', 'Not set')}")
        print(f"Has custom certificate: {webhook_info.get('has_custom_certificate', False)}")
        print(f"Pending update count: {webhook_info.get('pending_update_count', 0)}")
        print(f"Last error date: {webhook_info.get('last_error_date', 'None')}")
        print(f"Last error message: {webhook_info.get('last_error_message', 'None')}")
    else:
        print("❌ Failed to get webhook info")

def delete_webhook():
    """Delete the current webhook"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
    response = requests.post(url)
    result = response.json()
    
    if result.get("ok"):
        print("✅ Webhook deleted successfully!")
    else:
        print("❌ Failed to delete webhook")

if __name__ == "__main__":
    print("🤖 Telegram Bot Webhook Setup")
    print("=" * 40)
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Please set your BOT_TOKEN in this script first!")
        exit(1)
    
    if "your-app-name" in WEBHOOK_URL:
        print("❌ Please update WEBHOOK_URL with your actual Vercel app URL!")
        exit(1)
    
    print("Choose an option:")
    print("1. Set webhook")
    print("2. Get webhook info")
    print("3. Delete webhook")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        set_webhook()
    elif choice == "2":
        get_webhook_info()
    elif choice == "3":
        delete_webhook()
    else:
        print("Invalid choice!")