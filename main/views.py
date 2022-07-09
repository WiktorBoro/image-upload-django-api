from .models import UserModel
from django.http import HttpResponse


def home(requests):
    UserModel(user_name="test").save()
    return HttpResponse('xd')