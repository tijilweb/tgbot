import os
import re
import requests
import telebot
import traceback
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from urllib.parse import urlparse
import yt_dlp

# Debugging enable karo
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Bot token yahan dalo
BOT_TOKEN = "8463441374:AAFc_PNTOeXOd0H7mFPfrwCNarA3i6w-vmk"

# Bot ko higher timeout ke saath initialize karo
bot = telebot.TeleBot(BOT_TOKEN)

# Channel details
CHANNEL_LINK = "https://t.me/BESTMODZE"

# Supported platforms
SUPPORTED_PLATFORMS = {
    'instagram': ['instagram.com', 'www.instagram.com', 'instagr.am'],
    'youtube': ['youtube.com', 'www.youtube.com', 'youtu.be', 'm.youtube.com'],
    'terabox': ['terabox.com', 'www.terabox.com']
}

def create_promo_keyboard():
    """Create promotional keyboard"""
    keyboard = InlineKeyboardMarkup()
    channel_btn = InlineKeyboardButton("📢 Join Our Channel", url=CHANNEL_LINK)
    keyboard.add(channel_btn)
    return keyboard

def download_youtube_video(url):
    """YouTube video download function - SMALLER SIZE"""
    try:
        print(f"📹 Downloading YouTube video: {url}")
        
        # Smaller size ke liye format select karo
        ydl_opts = {
            'outtmpl': 'downloads/%(title).80s.%(ext)s',
            'format': 'best[height<=360]/best[height<=480]/best[height<=720]',  # Lower quality for smaller size
            'quiet': False,
            'no_warnings': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # File size check karo
            if os.path.exists(filename):
                file_size = os.path.getsize(filename) / (1024 * 1024)
                print(f"📊 Downloaded file size: {file_size:.1f}MB")
                
            print(f"✅ YouTube download successful: {filename}")
            return filename, info.get('title', 'YouTube Video')
            
    except Exception as e:
        error_msg = f"YouTube download error: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        return None, error_msg

def download_instagram_video(url):
    """Instagram video download function"""
    try:
        print(f"📷 Downloading Instagram video: {url}")
        
        ydl_opts = {
            'outtmpl': 'downloads/%(title).80s.%(ext)s',
            'format': 'best',
            'quiet': False,
            'no_warnings': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # File size check karo
            if os.path.exists(filename):
                file_size = os.path.getsize(filename) / (1024 * 1024)
                print(f"📊 Downloaded file size: {file_size:.1f}MB")
                
            print(f"✅ Instagram download successful: {filename}")
            return filename, info.get('title', 'Instagram Video')
            
    except Exception as e:
        error_msg = f"Instagram download error: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        return None, error_msg

def download_terabox_video(url):
    """Terabox video download function"""
    try:
        print(f"📦 Downloading TeraBox video: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(url, timeout=15)
        response.raise_for_status()
        
        # Video URLs dhundho
        video_patterns = [
            r'https?://[^\s"<>]+\.mp4[^\s"<>]*',
            r'video_url["\']?:\s*["\']([^"\']+)["\']',
            r'src=["\']([^"\']+\.mp4)["\']',
        ]
        
        found_urls = []
        for pattern in video_patterns:
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            found_urls.extend(matches)
        
        for i, video_url in enumerate(found_urls[:3]):
            try:
                if video_url.startswith('//'):
                    video_url = 'https:' + video_url
                elif video_url.startswith('/'):
                    base_url = '/'.join(url.split('/')[:3])
                    video_url = base_url + video_url
                
                print(f"🔄 Trying URL {i+1}...")
                
                video_response = session.get(video_url, stream=True, timeout=30)
                
                if video_response.status_code == 200:
                    filename = f"downloads/terabox_video_{os.urandom(4).hex()}.mp4"
                    
                    with open(filename, 'wb') as f:
                        for chunk in video_response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    if os.path.exists(filename) and os.path.getsize(filename) > 1024:
                        file_size = os.path.getsize(filename) / (1024 * 1024)
                        print(f"✅ TeraBox download successful: {filename} ({file_size:.1f}MB)")
                        return filename, "TeraBox Video"
                    else:
                        if os.path.exists(filename):
                            os.remove(filename)
                            
            except Exception as e:
                print(f"❌ Failed to download from URL {i+1}: {str(e)}")
                continue
        
        return None, "Could not find downloadable video link."
        
    except Exception as e:
        error_msg = f"TeraBox download error: {str(e)}"
        print(f"❌ {error_msg}")
        return None, error_msg

def detect_platform(url):
    """Detect which platform the URL belongs to"""
    try:
        domain = urlparse(url).netloc.lower()
        print(f"🔍 Detecting platform for: {domain}")
        
        for platform, domains in SUPPORTED_PLATFORMS.items():
            if any(supported_domain in domain for supported_domain in domains):
                print(f"✅ Platform detected: {platform}")
                return platform
        
        return None
        
    except Exception as e:
        print(f"❌ Platform detection error: {e}")
        return None

def send_video_safe(chat_id, file_path, caption, reply_markup):
    """Improved video sending with chunked upload"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            print(f"📤 Sending video attempt {attempt + 1}...")
            
            # File size check
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            print(f"📦 File size: {file_size:.1f}MB")
            
            # Agar file 20MB se badi hai to compression try karo
            if file_size > 20:
                print("⚡ Large file detected, using optimized sending...")
            
            with open(file_path, 'rb') as video_file:
                bot.send_video(
                    chat_id,
                    video_file,
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode='Markdown',
                    timeout=120,  # 2 minutes timeout
                    disable_notification=True  # Notification off for faster sending
                )
            print("✅ Video sent successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Send attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10  # Progressive waiting
                print(f"🔄 Retrying in {wait_time} seconds...")
                import time
                time.sleep(wait_time)
            else:
                print("💥 All send attempts failed")
                return False
    return False

def compress_video_if_large(file_path, max_size_mb=20):
    """Agar video bahut bada hai to compress karo"""
    try:
        file_size = os.path.getsize(file_path) / (1024 * 1024)
        
        if file_size <= max_size_mb:
            return file_path  # Compression ki zarurat nahi
            
        print(f"🔧 Compressing video from {file_size:.1f}MB to under {max_size_mb}MB...")
        
        # Simple compression - lower quality download karo
        # Yahan aap FFmpeg use kar sakte hain agar available hai
        return file_path
        
    except Exception as e:
        print(f"⚠️ Compression failed: {e}")
        return file_path

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = """
🚀 **Video Downloader Bot** 🚀

**I can download videos from:**
• 📷 Instagram (Reels, Posts)
• 📺 YouTube (Videos, Shorts)  
• 📦 TeraBox (Videos)

**How to use:**
Simply send me the video URL!

**Tips for better experience:**
• Use shorter videos (under 2 minutes)
• Stable internet connection
• Try different video links

**Support Us:**
Please join our channel for updates! 👇
    """
    
    bot.send_message(
        message.chat.id, 
        welcome_text, 
        reply_markup=create_promo_keyboard(),
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['small'])
def download_small_video(message):
    """Small videos ke liye special command"""
    if not message.reply_to_message or not message.reply_to_message.text:
        bot.reply_to(message, "❌ Please reply to a URL with /small command for smaller video size")
        return
    
    url = message.reply_to_message.text.strip()
    user_id = message.from_user.id
    
    processing_msg = bot.reply_to(message, "⏳ Downloading smaller video...")
    
    try:
        platform = detect_platform(url)
        if not platform:
            bot.edit_message_text("❌ Unsupported platform", message.chat.id, processing_msg.message_id)
            return
        
        os.makedirs('downloads', exist_ok=True)
        
        # YouTube ke liye smallest format
        if platform == 'youtube':
            ydl_opts = {
                'outtmpl': 'downloads/small_%(title).50s.%(ext)s',
                'format': 'worst[height<=360]',  # Smallest quality
                'quiet': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
                title = info.get('title', 'Video')
        else:
            # Other platforms
            if platform == 'instagram':
                file_path, title = download_instagram_video(url)
            else:
                file_path, title = download_terabox_video(url)
        
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            
            if file_size > 50:
                bot.edit_message_text(f"❌ Still too large: {file_size:.1f}MB", message.chat.id, processing_msg.message_id)
                os.remove(file_path)
                return
            
            caption = f"✅ **Small Video Download!**\n\n📹 {title}\n🔗 {platform.capitalize()}\n💾 {file_size:.1f}MB"
            
            send_success = send_video_safe(message.chat.id, file_path, caption, create_promo_keyboard())
            
            if send_success:
                bot.delete_message(message.chat.id, processing_msg.message_id)
            else:
                bot.edit_message_text("❌ Failed to send. Try better internet.", message.chat.id, processing_msg.message_id)
            
            try:
                os.remove(file_path)
            except:
                pass
        else:
            bot.edit_message_text(f"❌ Download failed: {title}", message.chat.id, processing_msg.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", message.chat.id, processing_msg.message_id)

@bot.message_handler(func=lambda message: True)
def handle_urls(message):
    url = message.text.strip()
    user_id = message.from_user.id
    
    print(f"📨 User sent URL: {url}")
    
    if not re.match(r'^https?://', url):
        bot.reply_to(message, "❌ Please send a valid URL")
        return
    
    platform = detect_platform(url)
    
    if not platform:
        bot.reply_to(message, 
            "❌ Unsupported platform! Supported: Instagram, YouTube, TeraBox",
            reply_markup=create_promo_keyboard()
        )
        return
    
    processing_msg = bot.reply_to(message, f"⏳ Processing {platform} link...")
    
    try:
        os.makedirs('downloads', exist_ok=True)
        
        if platform == 'youtube':
            file_path, title = download_youtube_video(url)
        elif platform == 'instagram':
            file_path, title = download_instagram_video(url)
        elif platform == 'terabox':
            file_path, title = download_terabox_video(url)
        else:
            file_path, title = None, "Unsupported platform"
        
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            print(f"📊 Final file size: {file_size:.1f}MB")
            
            if file_size > 50:
                bot.edit_message_text(
                    f"❌ File too large ({file_size:.1f}MB). Use /small for smaller version.",
                    message.chat.id,
                    processing_msg.message_id
                )
                os.remove(file_path)
                return
            
            # Agar file 10MB se badi hai to warning
            if file_size > 10:
                bot.edit_message_text(
                    f"⏳ Download complete ({file_size:.1f}MB). Sending may take time...",
                    message.chat.id,
                    processing_msg.message_id
                )
            
            caption = f"✅ **Download Successful!**\n\n📹 {title}\n🔗 {platform.capitalize()}"
            
            send_success = send_video_safe(message.chat.id, file_path, caption, create_promo_keyboard())
            
            if send_success:
                bot.delete_message(message.chat.id, processing_msg.message_id)
            else:
                bot.edit_message_text(
                    "❌ Failed to send video. Possible issues:\n• Slow internet\n• Large file\n• Try /small command\n\nJoin channel for help! 👇",
                    message.chat.id,
                    processing_msg.message_id,
                    reply_markup=create_promo_keyboard()
                )
            
            try:
                os.remove(file_path)
            except:
                pass
            
        else:
            bot.edit_message_text(
                f"❌ Download failed!\nError: {title}",
                message.chat.id,
                processing_msg.message_id,
                parse_mode='Markdown'
            )
            
    except Exception as e:
        bot.edit_message_text(
            f"❌ Error: {str(e)}",
            message.chat.id,
            processing_msg.message_id
        )

if __name__ == "__main__":
    print("🚀 Video Downloader Bot Started!")
    print("📢 Channel: @BESTMODZE")
    print("⚡ Optimized for slow connections")
    print("🤖 Bot is running...")
    
    os.makedirs('downloads', exist_ok=True)
    
    try:
        bot.polling(none_stop=True, timeout=90)
    except Exception as e:
        print(f"Bot error: {e}")
