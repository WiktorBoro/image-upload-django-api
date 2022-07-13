from django.http import HttpResponse
from .models import Users, Images
from json.decoder import JSONDecodeError
import base64
from secrets import token_urlsafe
from time import sleep
from PIL import Image
from io import BytesIO
from os import path
from rest_framework.views import status
from rest_framework.decorators import APIView
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.conf import settings
from celery import shared_task
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Indicate the number of nbytes that will be used to encode the addresses of the graphics
nbytes_url_code = 16


def home(request):
    return HttpResponse('<center><h1>Hello World!</h1></center>')


# here you can add more user authorization password / login / api key
def check_user_and_image_name(func):
    def wrapper(*args):
        self, request = args
        try:
            user_name = request.GET['user_name']
            user = Users.objects.get(user_name=user_name)
        except ObjectDoesNotExist:
            return Response({'Failure': 'User does not exist! Please try to enter the user again!'},
                            status=status.HTTP_400_BAD_REQUEST)

        # if we don't need check image_name
        if request.method == "GET":
            return func(self, request, user)

        # if we need check image_name
        try:
            request_json = request.data
        except JSONDecodeError:
            return Response({'Failure': 'Could not load JSON with request, check it is correct and try again!'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            image_name = request_json['image_name']
            if not image_name:
                raise KeyError
        except KeyError:
            return Response({'Failure': 'Enter a name for the image!'}, status=status.HTTP_400_BAD_REQUEST)
        return func(self, request=request, user=user, image_name=image_name, request_json=request_json)
        # END checking image_name

    return wrapper


def generate_link(domain: str,
                  file_name: str) -> str:
    protocol_http_https = "http://"
    return f'{protocol_http_https}{domain}{settings.STATIC_URL}{file_name}'


class GetImageList(APIView):

    @swagger_auto_schema(manual_parameters=[
                        openapi.Parameter(name='user_name', in_=openapi.IN_QUERY,
                                          required=True, type=openapi.TYPE_STRING)
                                            ],
                         responses={400: 'Dict with error message',
                                    200: 'Dict with links'},
                         operation_description="Returns a list of all images in all possible sizes"
                                               " for the given user and their account level")
    @check_user_and_image_name
    def get(self, request, user):
        """

        :param request:
        :param user:
        :return:
        """
        link_and_links_dict = dict()
        for original_image in Images.objects.filter(user=user, original=True).all():
            link_and_links_dict = {original_image.image_name: {}}

            if user.account_tier.link_to_the_originally_uploaded_file:
                link_and_links_dict[original_image.image_name].update({"original_image": original_image.link})

            for image in Images.objects.filter(original=False, original_id=original_image.original_id).all():
                link_and_links_dict[original_image.image_name].update({f"{image.width}x{image.height}": image.link})

        if link_and_links_dict:
            return Response(link_and_links_dict, status.HTTP_200_OK)
        return Response({'Failure': 'User has no graphics!'}, status.HTTP_400_BAD_REQUEST)


class UploadImage(APIView):

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(name='user_name', in_=openapi.IN_QUERY,
                              required=True, type=openapi.TYPE_STRING)
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'image_name': openapi.Schema(type=openapi.TYPE_STRING),
                'base64': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={400: 'Dict with error message',
                   201: 'Dict with link'},
        operation_description="Upload an image and get backlinks with sizes available for your account tier"
    )
    @check_user_and_image_name
    def post(self,
             request,
             user,
             image_name,
             request_json):
        """

        POST:
        Upload an image and get backlinks with sizes available for your account tier.

        :param request: POST
        :param str user: required
        :param str image_name:  required
        :param request_json:

        :return:
        """
        domain = request.META['HTTP_HOST']

        if Images.objects.filter(user=user, image_name=image_name).exists():
            return Response({'Failure': 'You already have a graphic with that name!'},
                            status=status.HTTP_400_BAD_REQUEST)

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
        link_dict = self.create_other_image_sizes_and_links_(user=user,
                                                             domain=domain,
                                                             original_image=original_image,
                                                             image_format=image_format)
        return Response({'Upload': 'Success', 'links': link_dict}, status=status.HTTP_201_CREATED)

    # Function it's responsible for create other image size and links for it dependent on user account tier
    def create_other_image_sizes_and_links_(self,
                                            user,
                                            domain,
                                            original_image,
                                            image_format) -> dict:
        link_dict = dict()
        sizes_to_generating_url = user.account_tier.image_height

        # If user have required account tier we add original size to generate link
        if user.account_tier.link_to_the_originally_uploaded_file:
            link_dict.update({'original': original_image.link})

        # We iterate over all the sizes to be generated
        for size in sizes_to_generating_url.replace(' ', '').split(','):
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


class GenerateExpiringLink(APIView):

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(name='user_name', in_=openapi.IN_QUERY,
                              required=True, type=openapi.TYPE_STRING)
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'image_name': openapi.Schema(type=openapi.TYPE_STRING),
                'expiring_time': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
        ),
        responses={400: 'Dict with error message',
                   201: 'Dict with expiring link'},
        operation_description="If you have the appropriate permissions, generate an expiring link to the binary graphic"
    )
    @check_user_and_image_name
    def post(self,
             request,
             user,
             image_name,
             request_json):
        """
        POST:
        If you have the appropriate permissions, generate an expiring link to the binary graphic

        :param request:
        :param user:
        :param image_name:
        :param request_json:

        :return:
        """
        domain = request.META['HTTP_HOST']

        if not user.account_tier.ability_to_generate_expiring_links:
            return Response({'Failure': 'You do not have the correct account tier, buy an upgrade!'},
                            status=status.HTTP_400_BAD_REQUEST)

        expiring_time = request_json['expiring_time']
        if not 300 <= expiring_time <= 30000:
            return Response({'Failure': 'The expiry time must be between 300 and 30000'},
                            status=status.HTTP_400_BAD_REQUEST)

        if not Images.objects.filter(user=user, image_name=image_name).exists():
            return Response({'Failure': 'You already have a graphic with that name!'},
                            status=status.HTTP_400_BAD_REQUEST)

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
        self.image_link_expiration.delay(expiring_time=expiring_time, expiring_link=expiring_link)
        return Response({'Generating': 'Succes', 'expiring_link': expiring_link}, status=status.HTTP_201_CREATED)

    # Function responsible for countdown and deleting image
    @shared_task(bind=True)
    def image_link_expiration(self,
                              expiring_time: int,
                              expiring_link: str):
        sleep(expiring_time)
        expiring_image = Images.objects.get(expiring_time=expiring_time, link=expiring_link)
        expiring_image.image.delete(save=True)
        expiring_image.delete()
