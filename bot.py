import yt_dlp
import os
import re
import time
import requests
import random
from threading import Thread
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent
from youtube_search import YoutubeSearch
from pytube import YouTube
from keep_alive import keep_alive

# إعداد المتغيرات من البيئة
API_ID = int(os.environ.get("API_ID", "8934899"))
API_HASH = os.environ.get("API_HASH", "bf3e98d2c351e4ad06946b4897374a1e")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8521458447:AAF0n_1009F2JXecuA72TQ1Me9awg1m3Hec")
CHANNEL = os.environ.get("CHANNEL", "TokYo")

from database import ytdb, sounddb

app = Client("youtube_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))

def Find(text):
    m = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s!()\[\]{};:'\".,<>?«»""'']))"
    url = re.findall(m, text)
    return [x[0] for x in url]

@app.on_message(filters.command("start"))
def start_handler(c, m):
    m.reply_text(
        "بوت تحميل من يوتيوب وساوند كلاود وتيك توك وشازام\n\n"
        "الاوامر المتاحة:\n"
        "يوت [اسم] - البحث في يوتيوب\n"
        "بحث [اسم] - تحميل من يوتيوب\n"
        "ساوند [اسم] - البحث في ساوند كلاود\n"
        "تيك [رابط] - تحميل من تيك توك\n"
        "شازام - التعرف على الاغنية (بالرد)\n"
        "شازام [اسم] - البحث عن كلمات الاغنية\n\n"
        f"القناة @{CHANNEL}"
    )

@app.on_message(filters.regex("^يوت ") & filters.group)
def yout_search(c, m):
    Thread(target=yout_func, args=(c, m)).start()

def yout_func(c, m):
    try:
        query = m.text.split(None, 1)[1]
        keyboard = []
        results = YoutubeSearch(query, max_results=4).to_dict()
        for res in results:
            title = res['title']
            id = res['id']
            keyboard.append([InlineKeyboardButton(title, callback_data=f'{m.from_user.id}GET{id}')])
        m.reply(f'البحث ~ {query}', reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)
    except Exception as e:
        m.reply(f"حدث خطأ {str(e)}")

@app.on_message(filters.regex("^بحث ") & filters.group)
def yt_download(c, m):
    Thread(target=yt_func, args=(c, m)).start()

def yt_func(c, m):
    try:
        query = m.text.split(None, 1)[1]
        results = YoutubeSearch(query, max_results=1).to_dict()
        res = results[0]
        title = res['title']
        duration = int(time_to_seconds(res['duration']))
        duration_string = time.strftime('%M:%S', time.gmtime(duration))
        
        if ytdb.get(f'ytvideo{res["id"]}'):
            aud = ytdb.get(f'ytvideo{res["id"]}')
            duration_string = time.strftime('%M:%S', time.gmtime(aud["duration"]))
            return m.reply_audio(aud["audio"], caption=f'@{CHANNEL} ~ {duration_string}')
        
        url = f'https://youtu.be/{res["id"]}'
        yt = YouTube(url)
        
        if yt.length > 1500:
            return m.reply("صوت فوق 25 دقيقة ما اقدر انزله")
        
        duration_string = time.strftime('%M:%S', time.gmtime(yt.length))
        ydl_ops = {"format": "bestaudio[ext=m4a]", 'forceduration': True}
        
        with yt_dlp.YoutubeDL(ydl_ops) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_file = ydl.prepare_filename(info)
            ydl.process_info(info)
        
        os.rename(audio_file, audio_file.replace(".m4a", ".mp3"))
        audio_file = audio_file.replace(".m4a", ".mp3")
        
        a = m.reply_audio(
            audio_file,
            title=yt.title,
            duration=yt.length,
            caption=f'@{CHANNEL} ~ {duration_string}',
            performer=yt.author
        )
        
        ytdb.set(f'ytvideo{res["id"]}', {"type": "audio", "audio": a.audio.file_id, "duration": a.audio.duration})
        os.remove(audio_file)
        
    except Exception as e:
        m.reply(f"حدث خطأ {str(e)}")

@app.on_callback_query(filters.regex("GET"))
def get_info(c, query):
    Thread(target=getInfo, args=(c, query)).start()

def getInfo(c, query):
    try:
        user_id = query.data.split("GET")[0]
        vid_id = query.data.split("GET")[1]
        
        if not query.from_user.id == int(user_id):
            return
        
        query.message.delete()
        url = f'https://youtu.be/{vid_id}'
        yt = YouTube(url)
        photo = yt.thumbnail_url
        
        reply_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("ملف صوتي", callback_data=f'{user_id}AUDIO{vid_id}'),
                InlineKeyboardButton("فيديو", callback_data=f'{user_id}VIDEO{vid_id}'),
            ],
            [InlineKeyboardButton(f'@{CHANNEL}', url=f'https://t.me/{CHANNEL}')]
        ])
        
        query.message.reply_to_message.reply_photo(
            photo,
            caption=f'@{CHANNEL} ~ {url}',
            reply_markup=reply_markup
        )
    except Exception as e:
        query.message.reply_text(f"حدث خطأ {str(e)}")

@app.on_callback_query(filters.regex("AUDIO"))
def get_audio(c, query):
    Thread(target=audio_down, args=(c, query)).start()

def audio_down(c, query):
    try:
        user_id = query.data.split("AUDIO")[0]
        vid_id = query.data.split("AUDIO")[1]
        
        if not query.from_user.id == int(user_id):
            return False
        
        rep = InlineKeyboardMarkup([[InlineKeyboardButton(f'@{CHANNEL}', url=f'https://t.me/{CHANNEL}')]])
        
        if ytdb.get(f'ytvideo{vid_id}'):
            aud = ytdb.get(f'ytvideo{vid_id}')
            query.edit_message_caption(f"@{CHANNEL}", reply_markup=rep)
            duration = aud["duration"]
            sec = time.strftime('%M:%S', time.gmtime(duration))
            return query.message.reply_audio(aud["audio"], caption=f'@{CHANNEL} ~ {sec}')
        
        url = f'https://youtu.be/{vid_id}'
        query.edit_message_caption("جاري التحميل", reply_markup=rep)
        
        ydl_ops = {"format": "bestaudio[ext=m4a]", 'forceduration': True}
        
        with yt_dlp.YoutubeDL(ydl_ops) as ydl:
            info = ydl.extract_info(url, download=False)
            if int(info['duration']) > 1500:
                return query.edit_message_caption("صوت اكثر من 25 دقيقة مقدر انزله", reply_markup=rep)
            audio_file = ydl.prepare_filename(info)
            ydl.process_info(info)
        
        query.edit_message_caption("جاري الرفع", reply_markup=rep)
        duration = int(info['duration'])
        sec = time.strftime('%M:%S', time.gmtime(duration))
        
        os.rename(audio_file, audio_file.replace(".m4a", ".mp3"))
        audio_file = audio_file.replace(".m4a", ".mp3")
        
        a = query.message.reply_audio(
            audio_file,
            title=info['title'],
            duration=int(info['duration']),
            performer=info['channel'],
            caption=f'@{CHANNEL} ~ {sec}',
        )
        
        query.edit_message_caption(f"@{CHANNEL}", reply_markup=rep)
        ytdb.set(f'ytvideo{vid_id}', {"type": "audio", "audio": a.audio.file_id, "duration": a.audio.duration})
        os.remove(audio_file)
        
    except Exception as e:
        query.message.reply_text(f"حدث خطأ {str(e)}")

@app.on_callback_query(filters.regex("VIDEO"))
def get_video(c, query):
    Thread(target=video_down, args=(c, query)).start()

def video_down(c, query):
    try:
        user_id = query.data.split("VIDEO")[0]
        vid_id = query.data.split("VIDEO")[1]
        
        if not query.from_user.id == int(user_id):
            return False
        
        rep = InlineKeyboardMarkup([[InlineKeyboardButton(f'@{CHANNEL}', url=f'https://t.me/{CHANNEL}')]])
        
        if ytdb.get(f'ytvideoV{vid_id}'):
            vid = ytdb.get(f'ytvideoV{vid_id}')
            query.edit_message_caption(f"@{CHANNEL}", reply_markup=rep)
            duration = vid["duration"]
            sec = time.strftime('%M:%S', time.gmtime(duration))
            return query.message.reply_video(vid["video"], caption=f'@{CHANNEL} ~ {sec}')
        
        url = f'https://youtu.be/{vid_id}'
        query.edit_message_caption("جاري التحميل", reply_markup=rep)
        
        with yt_dlp.YoutubeDL({}) as ydl:
            info = ydl.extract_info(url, download=False)
            if int(info['duration']) > 1500:
                return query.edit_message_caption("فيديو اكثر من 25 دقيقة مقدر انزله", reply_markup=rep)
        
        ydl_opts = {
            "format": "best",
            "keepvideo": True,
            "prefer_ffmpeg": False,
            "geo_bypass": True,
            "outtmpl": "%(title)s.%(ext)s",
            "quite": True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ytdl:
            ytdl_data = ytdl.extract_info(url, download=True)
            file_name = ytdl.prepare_filename(ytdl_data)
        
        query.edit_message_caption("جاري الرفع", reply_markup=rep)
        duration = int(info['duration'])
        sec = time.strftime('%M:%S', time.gmtime(duration))
        
        a = query.message.reply_video(
            file_name,
            duration=int(info['duration']),
            caption=f'@{CHANNEL} ~ {sec}',
        )
        
        query.edit_message_caption(f"@{CHANNEL}", reply_markup=rep)
        ytdb.set(f'ytvideoV{vid_id}', {"type": "video", "video": a.video.file_id, "duration": a.video.duration})
        os.remove(file_name)
        
    except Exception as e:
        query.message.reply_text(f"حدث خطأ {str(e)}")

if __name__ == "__main__":
    print("البوت يعمل الان...")
    keep_alive()
    app.run()
