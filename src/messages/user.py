import html


class UserMessages:

    @staticmethod
    def get_welcome(user_name: str) -> str:
        return (
            f'👋 Привет, {html.escape(user_name)} \n\n'
            f'<b>• С помощью этого бота вы можете скачивать видео из TikTok, YouTube, VK или Pinterest</b> \n\n'
            '<i>Отправьте ссылку на видео, которое хотите скачать:</i>'
        )

    @staticmethod
    def get_download_error() -> str:
        return '<i>⚠ Не удалось скачать видео</i>'

    @staticmethod
    def get_url_invalid() -> str:
        return '<i>⚠ Видео не найдено! \n\nПроверьте корректность ссылки.</i>'

    @staticmethod
    def get_user_must_subscribe() -> str:
        return '❗Подпишитесь на каналы, чтобы пользоваться ботом:'

    @staticmethod
    def get_user_subscribed():
        return '✅ Спасибо! \nМожете пользоваться ботом.'

    @staticmethod
    def get_not_all_channels_subscribed() -> str:
        return 'Вы подписались не на все каналы 😔'
