from django.http import HttpResponse
from .models import Users, AccountTiers, Images
from json import loads
import base64
from rest_framework import status
from secrets import token_urlsafe
from time import sleep
from PIL import Image
from io import BytesIO
from os import path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.conf import settings
from celery import shared_task

nbytes_url_code = 16
protocol_http_https = "http://"


def home(request):
    return HttpResponse('<center><h1>Hello World!</h1></center>')


@api_view(['GET'])
def get_image_list(request):
    request_json = loads(request.body)
    user_name = request_json['user_name']
    try:
        user = Users.objects.get(user_name=user_name)
    except ObjectDoesNotExist:
        return Response({'Upload': 'Failure! User does not exist!'})

    link_and_links_dict = dict()
    for original_image in Images.objects.filter(user=user, original=True).all():
        link_and_links_dict = {original_image.image_name: {}}

        if user.account_tier.link_to_the_originally_uploaded_file:
            link_and_links_dict[original_image.image_name].update({"original_image": original_image.link})

        for image in Images.objects.filter(original=False, original_id=original_image.original_id).all():
            link_and_links_dict[original_image.image_name].update({f"{image.width}x{image.height}": image.link})
    return Response(link_and_links_dict)


@api_view(['POST'])
def upload_image(request):
    domain = request.META['HTTP_HOST']
    request_json = loads(request.body)
    user_name = request_json['user_name']
    image_name = request_json['image_name']
    try:
        user = Users.objects.get(user_name=user_name)
    except ObjectDoesNotExist:
        return Response({'Upload': 'Failure! User does not exist!'})

    if not image_name:
        return Response({'Upload': 'Failure! Enter a name for the image!'})
    elif Images.objects.filter(user=user, image_name=image_name).exists():
        return Response({'Upload': 'Failure! You already have a graphic with that name!'})

    image = request_json['base64']
    if not image:
        return Response({'Upload': 'Failure! Graphics error, please try again!'})

    image_format, image_bs64 = image.split(';base64,')
    image_format = image_format.split('/')[-1]
    image = base64.b64decode(image_bs64)
    original_image_name = token_urlsafe(nbytes=nbytes_url_code)
    file_name = original_image_name + "." + image_format
    image = ContentFile(image, name=file_name)

    original_image = Images(image_name=image_name,
                            user=user,
                            image=image,
                            original=True,
                            original_id=file_name,
                            link=f'{protocol_http_https}{domain}/image/{file_name}')
    original_image.save()
    link_dict = create_other_image_sizes_and_links_(user=user,
                                                    domain=domain,
                                                    original_image=original_image,
                                                    image_format=image_format)
    return Response({'Upload': 'Succes', 'links': link_dict})


def create_other_image_sizes_and_links_(user,
                                        domain,
                                        original_image,
                                        image_format):
    link_dict = dict()
    size_to_generating_url = user.account_tier.image_height
    if user.account_tier.link_to_the_originally_uploaded_file:
        link_dict.update({'original': original_image.link})

    for size in size_to_generating_url.replace(' ', '').split(','):
        file_name = token_urlsafe(nbytes=nbytes_url_code) + "." + image_format
        link = f'{protocol_http_https}{domain}/image/{file_name}'
        print(path.join(settings.STATICFILES_DIRS[0], original_image.original_id))
        print(file_name)
        image = Image.open(path.join(settings.STATICFILES_DIRS[0], original_image.original_id))
        new_height = int(size)
        new_width = int(new_height / original_image.height * original_image.width)
        image = image.resize((new_width, new_height))
        img_to_save = BytesIO()
        print(image.format)
        image.save(fp=img_to_save, format=image_format, quality=100)
        img_to_save = ContentFile(img_to_save.getvalue(), name=file_name)
        Images(image=img_to_save,
               image_name=original_image.image_name + " - " + str(new_height),
               original_id=original_image.original_id,
               link=link,
               user=user).save()

        link_dict.update({size: link})
    return link_dict


@api_view(['POST'])
def generate_expiring_link(request):
    domain = request.META['HTTP_HOST']
    request_json = loads(request.body)
    user_name = request_json['user_name']
    image_name = request_json['image_name']
    expiring_time = request_json['expiring_time']
    try:
        user = Users.objects.get(user_name=user_name)
    except ObjectDoesNotExist:
        return Response({'Failure': 'User does not exist!'})

    if not 1 <= expiring_time <= 30000:
        return Response({'Failure': 'The expiry time must be between 1 adn 30000'})

    if not image_name:
        return Response({'Upload': 'Enter a name for the image!'})
    elif not Images.objects.filter(user=user, image_name=image_name).exists():
        return Response({'Failure': 'You already have a graphic with that name!'})

    original_image = Images.objects.get(user=user, image_name=image_name, original=True)
    image = Image.open(path.join(settings.STATICFILES_DIRS[0], original_image.original_id))

    image_format = original_image.original_id.split('.')[-1]
    file_name = token_urlsafe(nbytes=nbytes_url_code) + "." + image_format
    expiring_link = f'{protocol_http_https}{domain}/image/{file_name}'

    image = image.convert('1')  # convert image to black and white
    img_to_save = BytesIO()
    image.save(fp=img_to_save, format=image_format, quality=100)
    img_to_save = ContentFile(img_to_save.getvalue(), name=file_name)

    expiring_image = Images(image_name=image_name + " - expiring " + str(expiring_time),
                            user=user,
                            image=img_to_save,
                            expiring_time=expiring_time,
                            original_id=original_image.original_id,
                            link=expiring_link)
    expiring_image.save()
    image_link_expiration.delay(expiring_time=expiring_time, expiring_link=expiring_link)
    return Response({'Generating': 'Succes', 'expiring_link': expiring_link})


@shared_task(bind=True)
def image_link_expiration(self,
                          expiring_time,
                          expiring_link):
    sleep(expiring_time)
    expiring_image = Images.objects.get(expiring_time=expiring_time, link=expiring_link)
    expiring_image.image.delete(save=True)
    expiring_image.delete()
