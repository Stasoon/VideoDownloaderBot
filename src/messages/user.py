import html

from src.database.models import User


class UserMessages:

    @staticmethod
    def get_welcome(user_name: str) -> str:
        return (
            f'👋 Привет, {html.escape(user_name)} \n\n'
            f'<b>• С помощью этого бота вы можете скачивать видео из TikTok, YouTube, VK или Pinterest</b> \n\n'
            '<i>Отправьте ссылку на видео, которое хотите скачать:</i>'
        )

