from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
import asyncio


class Downloader:

    def __init__(self, video_url: str, height: int = 480):
        self.video_url = video_url
        self.height = height

    def __get_video_info(self):
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(self.video_url, download=False)
            return info.get('id'), f"{info.get('title')}.mp4"

    async def get_video_info(self) -> tuple[str, str]:
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor()

        try:
            data = await loop.run_in_executor(executor, self.__get_video_info)
        except Exception:
            data = None, None

        return data

    def __save_video(self):
        ydl_opts = {
            'noplaylist': True,
            'quiet': True,
            'outtmpl': f'videos/%(title)s_{str(uuid4())[:15]}.%(ext)s',
            'max-filesize': '150M',
            'format': f'18/bv*[height<=720][ext=mp4]',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.video_url, download=True)
            print(ydl.list_formats(info))
            return info.get('id'), f"{info.get('title')}.mp4", ydl.prepare_filename(info)

    async def get_video_file_url(self) -> str:
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor()

        data = await loop.run_in_executor(executor, self.__save_video)
        return data
