from django.http import HttpResponse
from .models import Users, AccountTiers, Images
from json import loads
import base64
from rest_framework import status
from secrets import token_urlsafe
from django.shortcuts import render
from PIL import Image
from io import BytesIO
from random import randrange
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.templatetags.static import static


nbytes_url_code = 32
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

        for image in Images.objects.get(original=False, original_id=original_image.original_id):
            link_and_links_dict[original_image.image_name].update({f"{image.width}x{image.height}": image.link})
    return Response(link_and_links_dict)


@api_view(['POST'])
def upload_image(request):
    domain = request.META['HTTP_HOST']
    request_json = loads(request.body)
    user_name = request_json['user_name']
    image_name = request_json['image_name']
    if not image_name:
        return Response({'Upload': 'Failure! Enter a name for the image!'})
    try:
        user = Users.objects.get(user_name=user_name)
    except ObjectDoesNotExist:
        return Response({'Upload': 'Failure! User does not exist!'})

    image = request_json['base64']
    if not image:
        return Response({'Upload': 'Failure! Graphics error, please try again!'})

    image_format, image_bs64 = image.split(';base64,')
    image = base64.b64decode(image_bs64)
    original_image_name = token_urlsafe(nbytes=nbytes_url_code)
    file_name = original_image_name + "." + image_format.split('/')[-1]
    image = ContentFile(image, name=file_name)

    original_image = Images(image_name=image_name,
                            user=user,
                            image=image,
                            original=True,
                            original_id=file_name,
                            link=f'{protocol_http_https}{domain}/image/{file_name}')
    original_image.save()
    link_dict = create_other_image_sizes_and_links_(user=user, domain=domain, original_image=original_image)
    return Response({'Upload': 'Succes', 'links': link_dict})


def create_other_image_sizes_and_links_(user, domain, original_image):
    link_dict = dict()

    size_to_generating_url = user.account_tier.image_height
    if user.account_tier.link_to_the_originally_uploaded_file:
        link_dict.update({'original': original_image.link})

    for size in size_to_generating_url.replace(' ', '').split(','):
        link = f'{protocol_http_https}{domain}/image/{token_urlsafe(nbytes=nbytes_url_code)}'

        im = Image.open('E:\\PyCharm 2020.2.4\\image_upload\image_upload\\main\\templates\\image\\6NdnRT77exeffhVoto0efZsKcVpCREwJzFbRNprbpd0.png')
        new_height = int(size)
        new_width = int(new_height / original_image.height * original_image.width)
        im = im.resize((new_width, new_height))
        im.save(original_image.original_id)
        Images(image=im,
               image_name=original_image.image_name,
               original_id=original_image.original_id,
               link=link,
               user=user)

        link_dict.update({size: link})
    return link_dict


@api_view(['POST'])
def generate_expiring_link(request):
    if request.method == "POST":
        pass
