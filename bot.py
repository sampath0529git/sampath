import os
import time
import subprocess
from pyrogram import Client, filters

# Heroku වලින් Variables ගන්නවා
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

app = Client("fast_subtitle_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_videos = {}

# Progress එක වෙලාවත් එක්ක පාලනය කිරීම (වේගය වැඩි කිරීමට)
def progress(current, total, msg, text, start_time):
    percent = current * 100 / total
    current_time = time.time()
    
    # මැසේජ් එක Edit කරන්නේ තත්පර 3කට සැරයක් විතරයි
    if current_time - start_time[0] > 3:
        try:
            msg.edit_text(f"{text}\n⏳ Progress: {percent:.1f}%")
            start_time[0] = current_time  # අලුත් වෙලාව සේව් කරනවා
        except:
            pass

@app.on_message(filters.video | filters.document)
def handle_files(client, message):
    chat_id = message.chat.id
    msg = message.reply_text("🔍 ෆයිල් එක චෙක් කරමින් පවතී...")

    # වීඩියෝ එකක් ආවොත්
    if message.video or (message.document and message.document.file_name.endswith(('.mp4', '.mkv', '.avi'))):
        msg.edit_text("📥 වීඩියෝ එක ඩවුන්ලෝඩ් වෙමින් පවතී...")
        
        # ඩවුන්ලෝඩ් පටන් ගන්න වෙලාව සටහන් කරගන්නවා
        start_time = [time.time()] 
        
        file_path = message.download(
            progress=progress, 
            progress_args=(msg, "📥 වීඩියෝ එක ඩවුන්ලෝඩ් වෙමින් පවතී...", start_time)
        )
        user_videos[chat_id] = file_path
        msg.edit_text("✅ වීඩියෝ එක හරි! දැන් ඒකට අදාල .srt (Subtitle) ෆයිල් එක එවන්න.")
        
    # Subtitle ෆයිල් එකක් ආවොත්
    elif message.document and message.document.file_name.endswith('.srt'):
        if chat_id not in user_videos:
            msg.edit_text("⚠️ මුලින්ම වීඩියෝ එකක් එවලා ඉන්න මචං.")
            return

        start_time = [time.time()]
        srt_path = message.download(
            progress=progress, 
            progress_args=(msg, "📥 Subtitle ෆයිල් එක ඩවුන්ලෝඩ් වෙමින් පවතී...", start_time)
        )
        video_path = user_videos[chat_id]
        out_path = f"CineVibe_LK_{message.message_id}.mp4"

        msg.edit_text("⚙️ වීඩියෝ එකට Subtitles එකතු කරමින් පවතී... මේකට පොඩි වෙලාවක් යයි.")
        
        try:
            # FFmpeg Command එක
            command = [
                "ffmpeg", "-y", "-i", video_path, "-i", srt_path,
                "-c", "copy", "-c:s", "mov_text", out_path
            ]
            subprocess.run(command, check=True)
            
            msg.edit_text("📤 Subtitle දාපු වීඩියෝ එක අප්ලෝඩ් කරමින් පවතී...")
            
            caption_text = "🎬 **CineVibe LK** | Action • Comedy • Drama\n\nමෙන්න Subtitles එක්ක වීඩියෝ එක! 🍿"
            
            start_time_up = [time.time()]
            message.reply_video(
                video=out_path, 
                caption=caption_text,
                progress=progress, 
                progress_args=(msg, "📤 Subtitle දාපු වීඩියෝ එක අප්ලෝඩ් කරමින් පවතී...", start_time_up)
            )
            msg.delete()
            
        except Exception as e:
            msg.edit_text(f"❌ පොඩි අවුලක් ගියා මචං: {str(e)}")
            
        finally:
            # සර්වර් එකේ ඉඩ ඉතුරු කරන්න
            for f in [video_path, srt_path, out_path]:
                if os.path.exists(f):
                    os.remove(f)
            del user_videos[chat_id]
            
    else:
        msg.edit_text("⚠️ කරුණාකරලා වීඩියෝ එකක් (MP4/MKV) හෝ .srt ෆයිල් එකක් පමණක් එවන්න.")

print("🚀 Fast Subtitle Bot සාර්ථකව පටන් ගත්තා!")
app.run()
