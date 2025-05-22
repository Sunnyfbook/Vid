from flask import Flask, render_template_string, jsonify, request
import re
import os
from main import get_video_info, get_all_videos

app = Flask(__name__)

class VideoEmbedder:
    @staticmethod
    def get_embed_code(video_url: str, video_title: str = "Video") -> str:
        """Generate embed code based on video URL"""
        
        # YouTube
        youtube_patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]+)',
            r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in youtube_patterns:
            match = re.search(pattern, video_url)
            if match:
                video_id = match.group(1)
                return f'''
                <div class="video-container">
                    <iframe width="100%" height="500" 
                            src="https://www.youtube.com/embed/{video_id}?autoplay=1" 
                            frameborder="0" 
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                            allowfullscreen>
                    </iframe>
                </div>'''
        
        # Vimeo
        vimeo_match = re.search(r'vimeo\.com/(\d+)', video_url)
        if vimeo_match:
            video_id = vimeo_match.group(1)
            return f'''
            <div class="video-container">
                <iframe width="100%" height="500" 
                        src="https://player.vimeo.com/video/{video_id}?autoplay=1" 
                        frameborder="0" 
                        allow="autoplay; fullscreen; picture-in-picture" 
                        allowfullscreen>
                </iframe>
            </div>'''
        
        # TikTok
        tiktok_match = re.search(r'tiktok\.com/.*/video/(\d+)', video_url)
        if tiktok_match:
            return f'''
            <div class="video-container">
                <iframe width="100%" height="500" 
                        src="https://www.tiktok.com/embed/v2/{tiktok_match.group(1)}" 
                        frameborder="0" 
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                        allowfullscreen>
                </iframe>
            </div>'''
        
        # Instagram
        if 'instagram.com' in video_url:
            return f'''
            <div class="video-container">
                <div class="fallback-message">
                    <h3>{video_title}</h3>
                    <p>Click the link below to watch on Instagram:</p>
                    <a href="{video_url}" target="_blank" class="video-link">Watch on Instagram</a>
                </div>
            </div>'''
        
        # Direct video files
        video_extensions = ['.mp4', '.webm', '.ogg', '.mov', '.avi']
        if any(ext in video_url.lower() for ext in video_extensions):
            return f'''
            <div class="video-container">
                <video width="100%" height="500" controls autoplay>
                    <source src="{video_url}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            </div>'''
        
        # Fallback for other URLs
        return f'''
        <div class="video-container">
            <div class="fallback-message">
                <h3>{video_title}</h3>
                <p>Click the link below to watch the video:</p>
                <a href="{video_url}" target="_blank" class="video-link">Open Video</a>
            </div>
        </div>'''

# HTML Templates as strings
BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }

        .header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 1rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }

        .header h1 {
            color: white;
            text-align: center;
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }

        .header p {
            color: rgba(255, 255, 255, 0.8);
            text-align: center;
        }

        .main-content {
            padding: 2rem 0;
        }

        .video-container {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            margin: 2rem auto;
            max-width: 800px;
        }

        .video-container iframe,
        .video-container video {
            width: 100%;
            height: 450px;
            border: none;
        }

        .video-info {
            padding: 1.5rem;
            background: white;
            border-radius: 15px;
            margin: 1rem auto;
            max-width: 800px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }

        .video-info h2 {
            color: #333;
            margin-bottom: 1rem;
            font-size: 1.5rem;
        }

        .video-meta {
            display: flex;
            gap: 2rem;
            margin-top: 1rem;
            font-size: 0.9rem;
            color: #666;
        }

        .fallback-message {
            padding: 3rem;
            text-align: center;
            background: #f8f9fa;
        }

        .video-link {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 25px;
            margin-top: 1rem;
            transition: background 0.3s ease;
        }

        .video-link:hover {
            background: #5a67d8;
        }

        .error-container, .home-content {
            background: white;
            border-radius: 15px;
            padding: 3rem;
            text-align: center;
            margin: 2rem auto;
            max-width: 600px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }

        .error-container h2 {
            color: #e53e3e;
            margin-bottom: 1rem;
        }

        .home-content h2 {
            color: #333;
            margin-bottom: 1rem;
        }

        .home-content p {
            color: #666;
            line-height: 1.6;
            margin-bottom: 1rem;
        }

        @media (max-width: 768px) {
            .container {
                padding: 0 15px;
            }
            
            .header h1 {
                font-size: 1.5rem;
            }
            
            .video-container iframe,
            .video-container video {
                height: 250px;
            }
            
            .video-meta {
                flex-direction: column;
                gap: 0.5rem;
            }
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="container">
            <h1>🎬 Video Hosting Platform</h1>
            <p>Your personal video streaming service</p>
        </div>
    </header>

    <main class="main-content">
        <div class="container">
            {{ content }}
        </div>
    </main>
</body>
</html>
'''

@app.route('/')
def index():
    """Homepage"""
    content = '''
    <div class="home-content">
        <h2>Welcome to Our Video Platform</h2>
        <p>This platform hosts videos shared through our Telegram bot. Each video gets its own unique viewing page with embedded player support for various video platforms.</p>
        <p>To add videos, use our Telegram bot by sending video URLs directly to the bot.</p>
        <p><strong>Supported platforms:</strong> YouTube, Vimeo, TikTok, Instagram, Direct video files, and more!</p>
    </div>
    '''
    return render_template_string(BASE_TEMPLATE, title="Home - Video Hosting Platform", content=content)

@app.route('/watch/<video_id>')
def watch_video(video_id):
    """Video watch page"""
    video_info = get_video_info(video_id)
    
    if not video_info:
        content = '''
        <div class="error-container">
            <h2>❌ Video Not Found</h2>
            <p>The video you're looking for doesn't exist or may have been removed.</p>
            <a href="/" class="video-link">← Back to Home</a>
        </div>
        '''
        return render_template_string(BASE_TEMPLATE, title="Video Not Found", content=content), 404
    
    # Generate embed code
    embed_code = VideoEmbedder.get_embed_code(video_info['url'], video_info.get('title', 'Video'))
    
    content = f'''
    {embed_code}
    <div class="video-info">
        <h2>{video_info.get('title', 'Video Information')}</h2>
        <div class="video-meta">
            <div><strong>Added by:</strong> {video_info['added_by']}</div>
            <div><strong>Video ID:</strong> {video_info['id']}</div>
            <div><strong>Original URL:</strong> <a href="{video_info['url']}" target="_blank">{video_info['url'][:50]}{'...' if len(video_info['url']) > 50 else ''}</a></div>
        </div>
    </div>
    '''
    
    return render_template_string(BASE_TEMPLATE, title=f"{video_info.get('title', 'Video')} - Video Platform", content=content)

@app.route('/api/video/<video_id>')
def api_get_video(video_id):
    """API endpoint to get video information"""
    video_info = get_video_info(video_id)
    
    if not video_info:
        return jsonify({'error': 'Video not found'}), 404
    
    return jsonify(video_info)

@app.route('/api/videos')
def api_list_videos():
    """API endpoint to list all videos"""
    videos = get_all_videos()
    return jsonify(videos)

# For Vercel
app.debug = False

if __name__ == '__main__':
    app.run(debug=True)