from database import BaseModel
from peewee import *


class PizzaTable(BaseModel):
    pizza_id = PrimaryKeyField(null=False)
    name = TextField()
    desc = TextField()
    price = IntegerField()

    @staticmethod
    def get_menu():
        return PizzaTable.select().execute()
