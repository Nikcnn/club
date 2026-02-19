from fastapi import FastAPI
from sqladmin import Admin, ModelView
from apps.users.models import User
from apps.db.session import engine

app = FastAPI()
admin = Admin(app, engine)


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.name]


admin.add_view(UserAdmin)