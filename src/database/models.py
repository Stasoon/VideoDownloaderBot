from peewee import (
    Model, PostgresqlDatabase, SqliteDatabase, AutoField,
    SmallIntegerField, BigIntegerField, IntegerField,
    DateTimeField, CharField, DecimalField, BooleanField,
    ForeignKeyField
)


db = SqliteDatabase(
    database='data.db'
    # DatabaseConfig.NAME,
    # user=DatabaseConfig.USER, password=DatabaseConfig.PASSWORD,
    # host=DatabaseConfig.HOST, port=DatabaseConfig.PORT
)


class _BaseModel(Model):
    class Meta:
        database = db


class User(_BaseModel):
    """ Пользователь бота """
    class Meta:
        db_table = 'users'

    telegram_id = BigIntegerField(primary_key=True, unique=True, null=False)
    name = CharField(default='Пользователь')
    username = CharField(null=True, default='Пользователь')
    last_activity = DateTimeField(null=True)
    bot_blocked = BooleanField(default=False)
    registration_timestamp = DateTimeField()

    def __str__(self):
        return f"@{self.username}" if self.username else f"tg://user?id={self.telegram_id}"


class CachedVideo(_BaseModel):
    telegram_file_id = CharField(max_length=350, primary_key=True)
    path = CharField()
    source = CharField()

    class Meta:
        db_table = 'cached_videos'


class Admin(_BaseModel):
    """ Администратор бота """
    class Meta:
        db_table = 'admins'

    telegram_id = BigIntegerField(unique=True, null=False)
    name = CharField()


def register_models() -> None:
    for model in _BaseModel.__subclasses__():
        model.create_table()
