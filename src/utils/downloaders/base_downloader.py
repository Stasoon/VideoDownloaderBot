from abc import ABC, abstractmethod


class BaseDownloader(ABC):

    @abstractmethod
    def __init__(self, video_url: str):
        self.video_url = video_url

    @abstractmethod
    async def get_video_file_url(self) -> tuple[str, str]:
        ...
