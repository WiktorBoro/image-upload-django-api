from rest_framework.test import APITestCase
from PIL import Image
from ..models import Users, AccountTiers, Images
from django.core.files.base import ContentFile
import pathlib
from io import BytesIO


class TestSetUp(APITestCase):
    def setUp(self):
        self.account_tiers_basic = AccountTiers.objects.create(account_tiers="Basic",
                                                               image_height="200")
        self.account_tiers_enterprise = AccountTiers.objects.create(account_tiers="Enterprise",
                                                                    image_height="200, 400",
                                                                    link_to_the_originally_uploaded_file=True,
                                                                    ability_to_generate_expiring_links=True)

        self.mike_user = Users.objects.create(user_name="Mike", account_tier=self.account_tiers_basic)
        self.janna_user = Users.objects.create(user_name="Janna", account_tier=self.account_tiers_enterprise)
        self.john_user = Users.objects.create(user_name="John", account_tier=self.account_tiers_basic)

        img_bs64 = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAZCAIAAACpVwlNAAAB6UlEQVRIiWPU1tZmoA1gopG5o0bT1WgWOOv/fxGPsmpPaUYGBoY/Pz+/vnNy48rNNz4xUsFoCLizpWPFhT/M3FLm/pGJEW+bZh77ykim6ehG//ry5s2bPwxv3mw8YGAbJi/DcOwmA8N/bhW38AAbNTGO3x8enN28cuOld/8ZIb5UuLrmh66nluDfV1e2LV524tU/hDuwhzUjm6iFkRLTq5evGBj+/2fSDUqw57i6bvakyYsOfteLCbXkg6uU1ZS+u27mlCUnf2sHByOJY3G1Rmh7dzADIzPznzeX1s8//J6RkZHh39Wl9bX///z/z8jA8OTINbdEeVmGY9cg6t9e3HPk9jsGhsf7rthEyEozMNzAafS9HZPXXJf3zfH4vmnJked/IIK8Gl7RfibyQlzMjAyMTCx/LyJ0ff3yCcL49uMXKzcb3rD+/Oz54yfHr7jHWhpzXD7xg5HxP7OWX7Q185HF0y68/fWfQc4lM5i4FItFFSPjv6snL/5QNzfnZ2BgYGAQkJLgenL+wJVHz188f/7y639WogzGFY3/bp08/0HR3FqSgYGB4cPL1z9lTV315CRlNKzCHFT/U2Q0I+OjE2dfSJpaKzL+Z/x7efOyU38NInMK0gO0Xl+8/I1IoxlHy+tRo0eNJgUAAD6FwH3gPHbtAAAAAElFTkSuQmCC'

        # For TestUploadImage
        self.body_upload_image = {
            'image_name': 'image_upload',
            'base64': img_bs64,
        }

        # For TestGenerateExpiringLink
        self.body_expiring_link = {
            'image_name': 'image',
            'expiring_time': 300
        }

        # create image
        image = Image.open(f'{pathlib.Path(__file__).parent.resolve()}\\tests_img1.jpg')
        iamge_to_save = BytesIO()
        image.save(fp=iamge_to_save, format=image.format, quality=100)
        image = ContentFile(iamge_to_save.getvalue(), name='image')

        # For TestGetImageList
        Images.objects.create(user=self.mike_user,
                              image=image,
                              image_name='image',
                              link='test.pl/link1',
                              original=True,
                              original_id='1.png')

        Images.objects.create(user=self.mike_user,
                              image=image,
                              image_name='image',
                              link='test.pl/link2',
                              original_id='1.png')

        # For TestGenerateExpiringLink
        Images.objects.create(user=self.janna_user,
                              image=image,
                              link='test.pl/link1',
                              original=True,
                              original_id='1.png',
                              image_name='image')
        # END create image
