from enum import Enum

from .models import CachedVideo


class VideoSource(Enum):
    TIKTOK = 'tiktok'
    YOUTUBE = 'youtube'
    INSTAGRAM = 'insta'
    PINTEREST = 'pinterest'
    VK = 'vk'


def save_video_to_cache(file_id: str, key: str, source: VideoSource) -> CachedVideo:
    return CachedVideo.get_or_create(telegram_file_id=file_id, path=key, source=source.value)


def get_cached_video(key: str, source: VideoSource) -> CachedVideo:
    return CachedVideo.get_or_none(path=key, source=source.value)

