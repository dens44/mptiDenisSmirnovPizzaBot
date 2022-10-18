from peewee import Model, SqliteDatabase

database = SqliteDatabase('sqlite.db')


class BaseModel(Model):
    class Meta:
        database = database


from database.Users import UsersTable
from database.Pizza import PizzaTable
from database.Orders import OrdersTable

UsersTable.create_table()
PizzaTable.create_table()
OrdersTable.create_table()


