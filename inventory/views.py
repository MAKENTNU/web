from django.db.models import Q
from django.http import JsonResponse
from django.views.generic import TemplateView

from inventory.models import Item, Category


class InventoryView(TemplateView):
    template_name = 'inventory/inventory.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'all_items': Item.objects.prefetch_related('categories',
                                                       'subcontainers__container',
                                                       'items_in_subcontainer'),
            'all_categories': Category.objects.all(),
        })
        return context


class ItemView(TemplateView):
    template_name = "inventory/item.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        item = Item.objects.first()
        context.update({
            'item': item,
        })
        return context


class SearchItemsView(TemplateView):
    template_name = "inventory/inventory.html"

    def post(self, request):
        search_string = request.POST.get('search')

        search_string = search_string.lower().strip()

        item_filter = Q(name__contains=search_string) | Q(description__contains=search_string)
        matched_items = Item.objects.filter(item_filter).order_by('name').prefetch_related('categories',
                                                                                           'subcontainers__container',
                                                                                           'items_in_subcontainer')

        # Maybe this can be optimized by serializing the QuerySet matched_items?
        result = []
        for item in matched_items:
            item_dict = {}
            item_dict['pk'] = item.pk
            item_dict['name'] = item.name
            item_dict['categories'] = item.category_html_list
            item_dict['amount'] = item.total_amount
            if item.unit:
                item_dict['unit'] = item.unit
            else:
                item_dict['unit'] = ''
            item_dict['container'] = item.container_html_list
            item_dict['comment'] = item.comment
            result.append(item_dict)

        data = {
            "matched_items": result,
        }

        return JsonResponse(data)
