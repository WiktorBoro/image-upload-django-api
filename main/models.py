from django.db import models
#from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator


def validate_image_height(value):
    for height in value.split(','):
        try:
            int(height)
        except ValueError:
            raise ValidationError("The heights must be numbers written after ,")
        return value


class AccountTiers(models.Model):
    account_tiers = models.CharField(max_length=50)
    arbitrary_thumbnail_sizes = models.BooleanField(default=False)
    link_to_the_originally_uploaded_file = models.BooleanField(default=False)
    ability_to_generate_expiring_links = models.BooleanField(default=False)
    image_height = models.CharField(max_length=100, validators=[validate_image_height])
    objects = models.Manager()

    def __str__(self):
        return self.account_tiers


class Users(models.Model):
    user_name = models.CharField(max_length=50)
    # password = models.CharField(max_length=128)
    # api_key = models.CharField(max_length=128)
    account_tiers = models.ForeignKey(AccountTiers, on_delete=models.CASCADE)

    objects = models.Manager()

    def __str__(self):
        return self.user_name


class Image(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    image_name = models.CharField(max_length=50)
    image = models.ImageField()

    objects = models.Manager()

    def __str__(self):
        return self.image_name


class ImageLinks(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    link = models.URLField()
    size = models.SmallIntegerField()
    link_name = models.CharField(default=image.name.__str__() + " - " + size.__str__(), max_length=100)
    expiring = models.SmallIntegerField(default=1,
                                        validators=[
                                            MaxValueValidator(100),
                                            MinValueValidator(1)
                                        ])
    objects = models.Manager()

    def __str__(self):
        return self.link_name
