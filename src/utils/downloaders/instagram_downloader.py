from playwright.async_api import async_playwright

from .base_downloader import BaseDownloader


class InstagramDownloader(BaseDownloader):

    def __init__(self, video_url: str):
        super().__init__(video_url)

    async def get_video_file_url(self) -> tuple[str, str]:
        loader_url = 'https://igsaved.com/ru/'

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(loader_url)

            url_input = await page.wait_for_selector('input.search__input.js__search-input')
            await url_input.type(text=self.video_url)

            next_button = await page.query_selector('button.search__button.search__button_download')
            await next_button.click()

            download_button = await page.wait_for_selector('a.button.button__blue')
            download_link = str(await download_button.get_property('href'))

            await browser.close()

        return '', download_link
