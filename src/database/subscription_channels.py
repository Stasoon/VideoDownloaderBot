from typing import Generator

from .models import ChannelToSubscribe


# region SQL Create

def save_channel(channel_id: str, title: str, url: str) -> None:
    if not is_channel_already_exist(channel_id):
        ChannelToSubscribe.create(channel_id=channel_id, title=title, url=url)
    else:
        channel = ChannelToSubscribe.get(ChannelToSubscribe.channel_id == channel_id)
        channel.update(channel_id=channel_id, title=title, url=url)
        channel.save()

# endregion


# region SQL Read

def is_channel_already_exist(channel_id: str) -> bool:
    return bool(ChannelToSubscribe.get_or_none(ChannelToSubscribe.channel_id == channel_id))


def get_channels() -> Generator[ChannelToSubscribe, None, None]:
    yield from (channel for channel in ChannelToSubscribe.select())


def get_channel_ids() -> tuple:
    channel_ids = [channel.channel_id for channel in ChannelToSubscribe.select()]
    return tuple(channel_ids)


# endregion


# region SQL Delete

def delete_channel(channel_id: int) -> None:
    channel = ChannelToSubscribe.get(ChannelToSubscribe.channel_id == channel_id)
    channel.delete_instance()

# endregion
