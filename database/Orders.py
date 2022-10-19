from database import BaseModel, UsersTable, PizzaTable
from peewee import *


class OrdersTable(BaseModel):
    order_id = PrimaryKeyField(null=False)
    created = DateTimeField(
        constraints=[SQL("DEFAULT (datetime('now'))")])
    user_id = ForeignKeyField(UsersTable)
    pizza_id = ForeignKeyField(PizzaTable)
    pizza_count = IntegerField()
    address = TextField()
    price = IntegerField()
    status = TextField()

    @staticmethod
    def set_order_done(order_id):
        OrdersTable.update(status="done").where(OrdersTable.order_id == order_id).execute()
