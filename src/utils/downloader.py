import os.path
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
import asyncio

from yt_dlp import DownloadError

from src.utils import logger
from src.utils.video_data import VideoData


class Downloader:

    def __init__(self, video_url: str, max_height: int = 720):
        self.video_url = video_url

        path = os.path.join('videos', f'{str(uuid4())[:15]}_%(title)s.%(ext)s')
        ydl_opts = {
            'noplaylist': True,
            'quiet': True,
            'outtmpl': path,
            'format': f'18/bv[height<={max_height}][ext=mp4]+ba/best',
        }
        self.ydl = yt_dlp.YoutubeDL(ydl_opts)

    @staticmethod
    def __get_resolution_and_thumb(info_dict: dict) -> tuple:
        """ Получает разрешение и ссылку на обложку """
        resolution, thumbnail_url = [None] * 2

        if 'formats' in info_dict:
            format_info = info_dict['formats'][-1]
            resolution = (format_info.get('width'), format_info.get('height'))

        if 'thumbnails' in info_dict and resolution:
            def is_best_resolution(thumbnail):
                return thumbnail.get('width') is not None and thumbnail.get('height') is not None

            try:
                best_thumbnail = max(
                    filter(is_best_resolution, info_dict['thumbnails']),
                    key=lambda t: t['width'] * t['height'] and t['url'].endswith('.jpg')
                )
                thumbnail_url = best_thumbnail['url'] if best_thumbnail else None
            except ValueError:
                thumbnail_url = info_dict['thumbnails'][-1].get('url')

        return resolution, thumbnail_url

    def __get_video_info(self, ydl) -> VideoData:
        info = ydl.extract_info(self.video_url, download=False)
        resolution, thumbnail_url = self.__get_resolution_and_thumb(info)

        return VideoData(
            id=info.get('id'), title=f"{info.get('title')}.mp4",
            duration=int(info.get('duration')),
            resolution=resolution, thumbnail_url=thumbnail_url
        )

    async def get_video_info(self) -> VideoData | None:
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor()

        try:
            data = await loop.run_in_executor(executor, self.__get_video_info, self.ydl)
        except Exception as e:
            logger.error(e)
            data = None

        return data

    def __save_video(self) -> VideoData:
        with self.ydl:
            info = self.ydl.extract_info(self.video_url, download=True)
            resolution, thumbnail_url = self.__get_resolution_and_thumb(info)

            return VideoData(
                id=info.get('id'), title=f"{info.get('title')}.mp4", duration=info.get('duration'),
                file_path=self.ydl.prepare_filename(info), resolution=resolution, thumbnail_url=thumbnail_url
            )

    async def save_video(self) -> VideoData:
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor()

        try:
            data = await loop.run_in_executor(executor, self.__save_video)
        except DownloadError as e:
            logger.error(e)
            data = None
        return data
