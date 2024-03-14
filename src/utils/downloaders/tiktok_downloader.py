import aiohttp
from bs4 import BeautifulSoup

from .base_downloader import BaseDownloader


class TikTokDownloader(BaseDownloader):

    def __init__(self, video_url: str):
        super().__init__(video_url)

    async def get_video_file_url(self) -> tuple[str, str]:
        video_url = None
        retries_count = 8

        for i in range(retries_count):
            try:
                video_url = await self.__get_link(link=self.video_url)
            except Exception:
                pass
            else:
                break

        return '', video_url

    async def __get_link(self, link: str):
        tmate_url = "https://tmate.cc/"
        headers = {
            'User-Agent': 'ваш User-Agent',
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(tmate_url) as response:
                if response.status != 200:
                    return

                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                token = soup.find("input", {"name": "token"})["value"]

            data = {'url': link, 'token': token}

            async with session.post('https://tmate.cc/download', data=data) as response:
                if response.status != 200:
                    return

                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                download_link = soup.find(class_="downtmate-right is-desktop-only right").find_all("a")[0]["href"]

        return download_link


# async def save_video(video: Video, api: AsyncTikTokAPI):
#     async with aiohttp.ClientSession(cookies={cookie["name"]: cookie["value"] for cookie in await api.context.cookies() if cookie["name"] == "tt_chain_token"}) as session:
#         async with session.get(video.video.download_addr, headers={"referer": "https://www.tiktok.com/"}) as resp:
#             return io.BytesIO(await resp.read())
