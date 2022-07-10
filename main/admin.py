from django.contrib import admin

from .models import AccountTiers, Users, Image, ImageLinks


class AccountTiersAdmin(admin.ModelAdmin):
    class UserAccountTiersAdmin(admin.TabularInline):
        model = Users
        fields = ['user_name']
        max_num = 0

    list_display = ['account_tiers',
                    'arbitrary_thumbnail_sizes',
                    'link_to_the_originally_uploaded_file',
                    'ability_to_generate_expiring_links']
    inlines = [UserAccountTiersAdmin]


class ImageLinksAdmin(admin.TabularInline):
    model = ImageLinks
    fields = ['link', 'link_name', 'size', 'expiring']
    max_num = 0


class ImageAdmin(admin.ModelAdmin):
    @admin.display(ordering='user__user_name', description='User name')
    def get_user_name(self, obj):
        return obj.user.user_name
    list_display = ['image_name', 'get_user_name']
    inlines = [ImageLinksAdmin]


class UserAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'account_tiers']
    inlines = [ImageLinksAdmin]


admin.site.register(AccountTiers, AccountTiersAdmin)
admin.site.register(Users, UserAdmin)
admin.site.register(Image, ImageAdmin)
