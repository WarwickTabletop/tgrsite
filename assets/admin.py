from django.contrib import admin

from .models import Asset, VisualAsset


class AssetAdmin(admin.ModelAdmin):
    fields = ('name', 'assetFile')
    search_fields = ('name',)


class VisualAssetAdmin(admin.ModelAdmin):
    fields = ('name', 'lightAssetFile', 'darkAssetFile')
    search_fields = ('name',)


# Register your models here.
admin.site.register(Asset, AssetAdmin)
admin.site.register(VisualAsset, VisualAssetAdmin)
