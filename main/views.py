from .models import Users
from django.http import HttpResponse


def home(request):
    Users(user_name="test").save()
    return HttpResponse('xd')


def get_image_list(request):
    if request.method == "GET":
        pass


def upload_image(request):
    if request.method == "POST":
        pass


def generate_image_links(request):
    if request.method == "POST":
        pass


def generate_expiring_link(request):
    if request.method == "POST":
        pass