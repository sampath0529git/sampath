import os
import time
import asyncio
from pyrogram import Client, filters

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

app = Client("fast_async_subtitle_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_videos = {}

async def progress(current, total, msg, text, start_time):
    if total == 0:
        return
    percent = current * 100 / total
    current_time = time.time()
    
    if current_time - start_time[0] > 3:
        try:
            await msg.edit_text(f"{text}\n⏳ Progress: {percent:.1f}%")
            start_time[0] = current_time
        except:
            pass

@app.on_message(filters.command("restart"))
async def restart_bot(client, message):
    msg = await message.reply_text("🔄 Bot Restart වෙමින් පවතී...")
    user_videos.clear()
    deleted_count = 0
    for file in os.listdir():
        if file.endswith(('.mp4', '.mkv', '.avi', '.srt')):
            try:
                os.remove(file)
                deleted_count += 1
            except:
                pass
    await msg.edit_text(f"✅ Bot සාර්ථකව Restart කළා!\n🗑️ පරණ ෆයිල් {deleted_count} ක් අයින් කළා.")

@app.on_message(filters.video | filters.document)
async def handle_files(client, message):
    if message.text and message.text.startswith('/'):
        return

    chat_id = message.chat.id
    msg = await message.reply_text("🔍 ෆයිල් එක චෙක් කරමින් පවතී...")

    file_name = ""
    if message.document and message.document.file_name:
        file_name = message.document.file_name.lower()

    # Video එකක් ආවොත්
    if message.video or file_name.endswith(('.mp4', '.mkv', '.avi')):
        try:
            await msg.edit_text("📥 වීඩියෝ එක ඩවුන්ලෝඩ් වෙමින් පවතී...")
            start_time = [time.time()] 
            file_path = await message.download(
                progress=progress, 
                progress_args=(msg, "📥 වීඩියෝ එක ඩවුන්ලෝඩ් වෙමින් පවතී...", start_time)
            )
            user_videos[chat_id] = file_path
            await msg.edit_text("✅ වීඩියෝ එක හරි! දැන් ඒකට අදාල .srt (Subtitle) ෆයිල් එක එවන්න.")
        except Exception as e:
            await msg.edit_text(f"❌ වීඩියෝ එක ඩවුන්ලෝඩ් කරද්දී අවුලක් ගියා: {str(e)}")

    # Subtitle එකක් ආවොත්
    elif file_name.endswith('.srt'):
        if chat_id not in user_videos:
            await msg.edit_text("⚠️ මුලින්ම වීඩියෝ එකක් එවලා ඉන්න මචං.")
            return

        try:
            await msg.edit_text("📥 Subtitle ෆයිල් එක සර්වර් එකට ගනිමින් පවතී...")
            srt_path = await message.download()
            
            video_path = user_videos[chat_id]
            out_path = f"CineVibe_LK_{message_id}.mp4"

            await msg.edit_text("⚙️ වීඩියෝ එකට Subtitles එකතු කරමින් පවතී... මේකට තත්පර කිහිපයක් යයි.")
            
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
            await msg.edit_text(f"❌ අවුලක් ගියා මචං: {str(e)}")
            
        finally:
            for f in [user_videos.get(chat_id), srt_path, out_path]:
                if f and os.path.exists(f):
                    try:
                        os.remove(f)
                    except:
                        pass
            if chat_id in user_videos:
                del user_videos[chat_id]
            
    else:
        await msg.edit_text("⚠️ කරුණාකරලා වීඩියෝ එකක් හෝ .srt ෆයිල් එකක් පමණක් එවන්න.")

print("🚀 Bot started successfully!")
app.run()
