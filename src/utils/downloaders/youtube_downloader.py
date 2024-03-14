from playwright.async_api import async_playwright

from .base_downloader import BaseDownloader


class YoutubeDownloader(BaseDownloader):

    def __init__(self, video_url: str):
        super().__init__(video_url)

    async def get_video_file_url(self) -> tuple[str, str]:
        loader_url = 'https://savefrom.kim/ru/'

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(loader_url)

            url_input = await page.wait_for_selector('input#id_url')
            await url_input.type(text=self.video_url)

            next_button = await page.query_selector('button#search')
            await next_button.click()

            download_button = await page.wait_for_selector('a.results__btn-download')

            async with page.expect_download() as download_info:
                await download_button.click()
            download = await download_info.value

            await browser.close()

        return download.suggested_filename, download.url
