from django.contrib import admin
from django.db import models
from django.contrib.admin import TabularInline
from django.utils.safestring import mark_safe

from inventory.models import Item, ItemInSubContainer, SubContainer, Category, Container


class ContainerAdmin(admin.ModelAdmin):
    class SubContainerInline(TabularInline):
        model = SubContainer
        extra = 2

    list_display = ["name", "get_subcontainers"]
    inlines = [SubContainerInline]

    def get_subcontainers(self, item):
        return mark_safe("<br>".join(str(sc) for sc in item.subcontainers.all()))

    get_subcontainers.short_description = "Subcontainers"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("subcontainers")


class ItemAdmin(admin.ModelAdmin):
    class ItemInSubcontainerInline(TabularInline):
        model = ItemInSubContainer
        raw_id_fields = ("subcontainer",)

        extra = 2

    list_display = ["name", "get_categories", "get_total_amount", "description"]
    ordering = ["name"]
    search_fields = ["name", "categories"]

    filter_horizontal = ["categories"]

    inlines = [ItemInSubcontainerInline]

    def get_categories(self, item):
        return ", ".join(str(i) for i in item.categories.all()) or None

    get_categories.short_description = "Categories"

    def get_total_amount(self, item):
        return item.amount_sum

    get_total_amount.short_description = "Total amount"
    get_total_amount.admin_order_field = "amount_sum"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(amount_sum=models.Sum("items_in_subcontainer__amount"))  # Facilitates querying `amount_sum`
        return qs.prefetch_related("categories")


class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]
    ordering = ["name"]


class SubContainerAdmin(admin.ModelAdmin):
    list_display = ["name", "container"]
    search_fields = ["name", "container__name"]
    ordering = ["container", "name"]

    raw_id_fields = ("container",)

    def get_model_perms(self, request):
        # Hide model admin from admin list
        return {}


# class ItemInSubContainerAdmin(admin.ModelAdmin):
#     list_display = ["item", "subcontainer", "amount"]


admin.site.register(Item, ItemAdmin)
admin.site.register(Container, ContainerAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(SubContainer, SubContainerAdmin)
# admin.site.register(ItemInSubContainer, ItemInSubContainerAdmin)

# TODO: create inline forms for containers
