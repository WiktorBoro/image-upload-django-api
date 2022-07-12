from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.conf import settings


def validate_image_height(value):
    for height in value.split(','):
        try:
            int(height)
        except ValueError:
            raise ValidationError("The heights must be numbers written after ,")
        return value


class AccountTiers(models.Model):
    account_tiers = models.CharField(max_length=50)
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
    account_tier = models.ForeignKey(AccountTiers, on_delete=models.CASCADE)

    objects = models.Manager()

    def __str__(self):
        return self.user_name


class Images(models.Model):

    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    image_name = models.CharField(max_length=50)

    width = models.SmallIntegerField(null=True)
    height = models.SmallIntegerField(null=True)
    image = models.ImageField(upload_to=settings.STATICFILES_DIRS[0], height_field='height', width_field='width')
    original = models.BooleanField(default=False)
    original_id = models.CharField(max_length=100, null=True)

    link = models.URLField(null=True)
    expiring_time = models.SmallIntegerField(default=1,
                                             validators=[
                                                 MaxValueValidator(100),
                                                 MinValueValidator(1)
                                             ])
    objects = models.Manager()

    def __str__(self):
        return self.image_name
