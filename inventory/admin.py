from django.contrib import admin

# Register your models here.
from inventory.models import Item, ItemInSubContainer, SubContainer, Category, Container


class ItemAdmin(admin.ModelAdmin):
	list_display = ["name", "description"]


class ContainerAdmin(admin.ModelAdmin):
	list_display = ["name"]


class CategoryAdmin(admin.ModelAdmin):
	list_display = ["name"]


class SubContainerAdmin(admin.ModelAdmin):
	list_display = ["name", "container"]


class ItemInSubContainerAdmin(admin.ModelAdmin):
	list_display = ["item", "subcontainer", "amount"]


admin.site.register(Item, ItemAdmin)
admin.site.register(Container, ContainerAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(SubContainer, SubContainerAdmin)
admin.site.register(ItemInSubContainer, ItemInSubContainerAdmin)


# TODO: create inline forms for containers
