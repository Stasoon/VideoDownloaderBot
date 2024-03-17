from dataclasses import dataclass


@dataclass
class VideoData:
    id: str = None
    title: str = None

    duration: int = None
    resolution: tuple[int, int] = (None, None)

    file_path: str = None
    file_url: str = None

    thumbnail_url: str = None

