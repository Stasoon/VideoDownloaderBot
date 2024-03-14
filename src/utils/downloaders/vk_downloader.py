from playwright.async_api import async_playwright

from src.utils.downloaders import BaseDownloader


class VkDownloader(BaseDownloader):

    def __init__(self, video_url: str):
        super().__init__(video_url)

    async def get_video_file_url(self) -> tuple[str, str]:
        loader_url = 'https://savefrom.ws/vk-video-downloader/'

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            await page.goto(loader_url)

            url_input = await page.wait_for_selector('input#url')
            await url_input.type(text=self.video_url)

            next_button = await page.query_selector('button#downloadBtn')
            await next_button.click()

            download_button_selector = 'a.btn.btn-sm.btn-secondary'
            await page.wait_for_selector(download_button_selector)
            download_button = (await page.query_selector_all(download_button_selector))[-1]
            download_link = str(await download_button.get_property('href'))

            await browser.close()

        return '', download_link
