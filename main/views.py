from django.http import HttpResponse
from .models import Users, Images
from json import loads
from json.decoder import JSONDecodeError
import base64
from secrets import token_urlsafe
from time import sleep
from PIL import Image
from io import BytesIO
from os import path
from rest_framework.views import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.conf import settings
from celery import shared_task

# Indicate the number of nbytes that will be used to encode the addresses of the graphics
nbytes_url_code = 16


def home(request):
    return HttpResponse('<center><h1>Hello World!</h1></center>')


# here you can add more user authorization password / login / api key
def check_user_and_image_name(func):
    def wrapper(request):
        try:
            request_json = loads(request.body)
        except JSONDecodeError:
            return Response({'Failure': 'Could not load JSON with request, check it is correct and try again!'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            user_name = request_json['user_name']
            user = Users.objects.get(user_name=user_name)
        except ObjectDoesNotExist:
            return Response({'Failure': 'User does not exist! Please try to enter the user again!'},
                            status=status.HTTP_400_BAD_REQUEST)

        # if we don't need check image_name
        if func.__name__ == "get_image_list":
            return func(request, user)

        # if we need check image_name
        try:
            image_name = request_json['image_name']
            if not image_name:
                raise KeyError
        except KeyError:
            return Response({'Failure': 'Enter a name for the image!'}, status=status.HTTP_400_BAD_REQUEST)
        return func(request, user, image_name)
        # END checking image_name

    return wrapper


def generate_link(domain: str,
                  file_name: str) -> str:
    protocol_http_https = "http://"
    return f'{protocol_http_https}{domain}/{settings.STATIC_URL}{file_name}'


@api_view(['GET'])
@check_user_and_image_name
def get_image_list(request, user):
    """
    param1 - test - A first parameter
    param2 - test2 - A second parameter
    """
    link_and_links_dict = dict()
    for original_image in Images.objects.filter(user=user, original=True).all():
        link_and_links_dict = {original_image.image_name: {}}

        if user.account_tier.link_to_the_originally_uploaded_file:
            link_and_links_dict[original_image.image_name].update({"original_image": original_image.link})

        for image in Images.objects.filter(original=False, original_id=original_image.original_id).all():
            link_and_links_dict[original_image.image_name].update({f"{image.width}x{image.height}": image.link})

    if link_and_links_dict:
        return Response(link_and_links_dict)
    return Response({'Failure': 'User has no graphics!'})


@api_view(['POST'])
@check_user_and_image_name
def upload_image(request,
                 user,
                 image_name):
    domain = request.META['HTTP_HOST']
    request_json = loads(request.body)

    if Images.objects.filter(user=user, image_name=image_name).exists():
        return Response({'Failure': 'You already have a graphic with that name!'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        image = request_json['base64']
        if not image:
            raise KeyError
    except KeyError:
        return Response({'Failure': 'Graphics error, please try again!'}, status=status.HTTP_400_BAD_REQUEST)

    # Working with base64 code and convert it to image
    image_format, image_bs64 = image.split(';base64,')
    image_format = image_format.split('/')[-1]

    image = base64.b64decode(image_bs64)
    original_image_id = token_urlsafe(nbytes=nbytes_url_code)
    file_name = original_image_id + "." + image_format
    # END base64 operation

    # Prepared the original image to be saved in db and saved
    image = ContentFile(image, name=file_name)
    original_image = Images(image=image,
                            image_name=image_name,
                            user=user,
                            original=True,
                            original_id=file_name,
                            link=generate_link(domain=domain, file_name=file_name))
    original_image.save()
    link_dict = create_other_image_sizes_and_links_(user=user,
                                                    domain=domain,
                                                    original_image=original_image,
                                                    image_format=image_format)
    return Response({'Upload': 'Success', 'links': link_dict}, status=status.HTTP_200_OK)


# Function it's responsible for create other image size and links for it dependent on user account tier
def create_other_image_sizes_and_links_(user,
                                        domain,
                                        original_image,
                                        image_format) -> dict:
    link_dict = dict()
    size_to_generating_url = user.account_tier.image_height

    # If user have required account tier we add original size to generate link
    if user.account_tier.link_to_the_originally_uploaded_file:
        link_dict.update({'original': original_image.link})

    # We iterate over all the sizes to be generated
    for size in size_to_generating_url.replace(' ', '').split(','):
        file_name = token_urlsafe(nbytes=nbytes_url_code) + "." + image_format
        link = generate_link(domain=domain, file_name=file_name)

        # Opened the image through pillow, resize and save to BytesIO()
        image = Image.open(path.join(settings.STATICFILES_DIRS[0], original_image.original_id))

        new_height = int(size)
        new_width = int(new_height / original_image.height * original_image.width)

        image = image.resize((new_width, new_height))
        img_to_save = BytesIO()
        image.save(fp=img_to_save, format=image_format, quality=100)
        # END pillow operation

        # Prepared the image to be saved in db and saved
        img_to_save = ContentFile(img_to_save.getvalue(), name=file_name)
        Images(image=img_to_save,
               image_name=original_image.image_name + " - " + str(new_height),
               original_id=original_image.original_id,
               link=link,
               user=user).save()

        link_dict.update({size: link})
    return link_dict


@api_view(['POST'])
@check_user_and_image_name
def generate_expiring_link(request,
                           user,
                           image_name):
    domain = request.META['HTTP_HOST']
    request_json = loads(request.body)
    expiring_time = request_json['expiring_time']

    if not 300 <= expiring_time <= 30000:
        return Response({'Failure': 'The expiry time must be between 1 adn 30000'}, status=status.HTTP_400_BAD_REQUEST)

    if not Images.objects.filter(user=user, image_name=image_name).exists():
        return Response({'Failure': 'You already have a graphic with that name!'}, status=status.HTTP_400_BAD_REQUEST)

    original_image = Images.objects.get(user=user, image_name=image_name, original=True)
    image_format = original_image.original_id.split('.')[-1]
    file_name = token_urlsafe(nbytes=nbytes_url_code) + "." + image_format

    # Opened the image through pillow, convert to binary and save to BytesIO()
    image = Image.open(path.join(settings.STATICFILES_DIRS[0], original_image.original_id))
    image = image.convert('1')
    img_to_save = BytesIO()
    image.save(fp=img_to_save, format=image_format, quality=100)
    # END pillow operation

    # Prepared the image to be saved in db and saved
    img_to_save = ContentFile(img_to_save.getvalue(), name=file_name)
    expiring_link = generate_link(domain=domain, file_name=file_name)
    expiring_image = Images(image_name=image_name + " - expiring " + str(expiring_time),
                            user=user,
                            image=img_to_save,
                            expiring_time=expiring_time,
                            original_id=original_image.original_id,
                            link=expiring_link)
    expiring_image.save()

    # We start a separate countdown until the link expires and the graphics disappear
    image_link_expiration.delay(expiring_time=expiring_time, expiring_link=expiring_link)
    return Response({'Generating': 'Succes', 'expiring_link': expiring_link}, status=status.HTTP_200_OK)


# Function responsible for countdown and deleting image
@shared_task(bind=True)
def image_link_expiration(self,
                          expiring_time: int,
                          expiring_link: str):
    sleep(expiring_time)
    expiring_image = Images.objects.get(expiring_time=expiring_time, link=expiring_link)
    expiring_image.image.delete(save=True)
    expiring_image.delete()
