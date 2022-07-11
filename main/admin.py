from django.contrib import admin

from .models import AccountTiers, Users, Images


@admin.action(description='Delete images with file')
def delete_images_with_file(modeladmin, request, images):
    for img in images:
        img.image.delete(save=True)
        img.delete()


class AccountTiersAdmin(admin.ModelAdmin):
    class UserAccountTiersAdmin(admin.TabularInline):
        model = Users
        fields = ['user_name']
        max_num = 0

    list_display = ['account_tiers',
                    'link_to_the_originally_uploaded_file',
                    'ability_to_generate_expiring_links']
    inlines = [UserAccountTiersAdmin]


class ImageAdmin(admin.ModelAdmin):
    @admin.display(ordering='user__user_name', description='User name')
    def get_user_name(self, obj):
        return obj.user.user_name

    list_display = ['image_name', 'width', 'height', 'get_user_name']
    actions = [delete_images_with_file]


class ImageLinksAdmin(admin.TabularInline):
    model = Images
    fields = ['link', 'image_name', 'height', 'width', 'original', 'expiring', 'expiring_time']
    max_num = 0


class UserAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'account_tier']
    inlines = [ImageLinksAdmin]


admin.site.register(AccountTiers, AccountTiersAdmin)
admin.site.register(Users, UserAdmin)
admin.site.register(Images, ImageAdmin)
