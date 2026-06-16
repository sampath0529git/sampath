import os
import time
import asyncio
from pyrogram import Client, filters

# Heroku වලින් Variables ගන්නවා
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

app = Client("fast_async_subtitle_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_videos = {}

# Progress පෙන්නන ෆන්ක්ෂන් එක
async def progress(current, total, msg, text, start_time):
    if total == 0:
        return
    percent = current * 100 / total
    current_time = time.time()
    
    # මැසේජ් එක Edit කරන්නේ තත්පර 3කට සැරයක් විතරයි
    if current_time - start_time[0] > 3:
        try:
            await msg.edit_text(f"{text}\n⏳ Progress: {percent:.1f}%")
            start_time[0] = current_time
        except:
            pass

# Bot ව Restart කරලා පරණ ෆයිල් මකන Command එක
@app.on_message(filters.command("restart"))
async def restart_bot(client, message):
    msg = await message.reply_text("🔄 Bot Restart වෙමින් පවතී... පරණ ෆයිල් හොයනවා...")
    
    # පරණ වීඩියෝ මතකය අයින් කිරීම
    user_videos.clear()
    
    # සර්වර් එකේ තියෙන පරණ වීඩියෝ සහ සබ්ටයිටල් ෆයිල් මකා දැමීම
    deleted_count = 0
    for file in os.listdir():
        if file.endswith(('.mp4', '.mkv', '.avi', '.srt')):
            try:
                os.remove(file)
                deleted_count += 1
            except:
                pass
                
    await msg.edit_text(f"✅ Bot සාර්ථකව Restart කළා මචං!\n🗑️ සර්වර් එකේ හිරවෙලා තිබ්බ පරණ ෆයිල් {deleted_count} ක් අයින් කළා. දැන් අලුතෙන් වීඩියෝ එවන්න පුළුවන්.")

@app.on_message(filters.video | filters.document)
async def handle_files(client, message):
    # Command එකක් නම් මේකෙන් අයින් වෙනවා
    if message.text and message.text.startswith('/'):
        return

    chat_id = message.chat.id
    msg = await message.reply_text("🔍 ෆයිල් එක චෙක් කරමින් පවතී...")

    # ෆයිල් එකේ නම ගන්නවා
    file_name = ""
    if message.document and message.document.file_name:
        file_name = message.document.file_name.lower()

    # වීඩියෝ එකක් ආවොත්
    if message.video or file_name.endswith(('.mp4', '.mkv', '.avi')):
        await msg.edit_text("📥 වීඩියෝ එක ඩවුන්ලෝඩ් වෙමින් පවතී...")
        start_time = [time.time()] 
        
        file_path = await message.download(
            progress=progress, 
            progress_args=(msg, "📥 වීඩියෝ එක ඩවුන්ලෝඩ් වෙමින් පවතී...", start_time)
        )
        user_videos[chat_id] = file_path
        await msg.edit_text("✅ වීඩියෝ එක හරි! දැන් ඒකට අදාල .srt (Subtitle) ෆයිල් එක එවන්න.")
        
    # Subtitle ෆයිල් එකක් ආවොත්
    elif file_name.endswith('.srt'):
        if chat_id not in user_videos:
            await msg.edit_text("⚠️ මුලින්ම වීඩියෝ එකක් එවලා ඉන්න මචං. නැත්නම් /restart දීලා මුල ඉඳන් පටන් ගන්න.")
            return

        await msg.edit_text("📥 Subtitle ෆයිල් එක සර්වර් එකට ගනිමින් පවතී...")
        
        srt_path = await message.download()
        
        video_path = user_videos[chat_id]
        out_path = f"CineVibe_LK_{message.message_id}.mp4"

        await msg.edit_text("⚙️ වීඩියෝ එකට Subtitles එකතු කරමින් පවතී... මේකට තත්පර කිහිපයක් යයි.")
        
        try:
            # Async FFmpeg Command
            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-y", "-i", video_path, "-i", srt_path,
                "-c", "copy", "-c:s", "mov_text", out_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            await msg.edit_text("📤 Subtitle දාපු වීඩියෝ එක අප්ලෝඩ් කරමින් පවතී...")
            
            caption_text = "🎬 **CineVibe LK** | Action • Comedy • Drama\n\nමෙන්න Subtitles එක්ක වීඩියෝ එක! 🍿"
            
            start_time_up = [time.time()]
            await message.reply_video(
                video=out_path, 
                caption=caption_text,
                progress=progress, 
                progress_args=(msg, "📤 Subtitle දාපු වීඩියෝ එක අප්ලෝඩ් කරමින් පවතී...", start_time_up)
            )
            await msg.delete()
            
        except Exception as e:
            await msg.edit_text(f"❌ පොඩි අවුලක් ගියා මචං: {str(e)}")
            
        finally:
            # වැඩේ ඉවර වුණාම ෆයිල් මකනවා
            for f in [video_path, srt_path, out_path]:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except:
                        pass
            if chat_id in user_videos:
                del user_videos[chat_id]
            
    else:
        await msg.edit_text("⚠️ කරුණාකරලා වීඩියෝ එකක් (MP4/MKV) හෝ .srt ෆයිල් එකක් පමණක් එවන්න.")

print("🚀 Bot started with Restart Command!")
app.run()
