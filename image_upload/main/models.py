from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class AccountTiers(models.Model):
    def validate_image_height(self, image_height):
        for height in image_height.split(','):
            try:
                int(height)
            except ValueError:
                raise ValidationError("The heights must be numbers written after ,")
            return image_height

    account_tiers = models.CharField(max_length=50)
    arbitrary_thumbnail_sizes = models.BooleanField(default=False)
    link_to_the_originally_uploaded_file = models.BooleanField(default=False)
    ability_to_generate_expiring_links = models.BooleanField(default=False)
    image_height = models.CharField(max_length=100, validators=[validate_image_height])

    def __str__(self):
        return self.account_tiers


class UserModel(User, models.Model):
    user_name = User.username()

    password = None
    account_tiers = None
    objects = models.Manager()


class Image(models):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image_name = models.CharField(max_length=50)
    image = models.ImageField()
    objects = models.Manager()


    class ImageLinks(models):
        image = models.ForeignKey('self', on_delete=models.CASCADE)
        link = None
        size = None

