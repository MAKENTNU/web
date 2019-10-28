from django.http import HttpResponse, JsonResponse
from django.template import loader
# Create your views here.
from django.views.generic import TemplateView
from django.db.models import Q

from inventory.models import ItemInSubContainer, Item


class InventoryView(TemplateView):
    template_name = 'inventory/inventory.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        itemset = Item.objects.all()
        context.update({
            'all_items': itemset,
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
    template_name = "inventory/inventory_search.html"

    MAX_RESULTS = 10

    def post(self, request):
        search_string = request.POST.get('search')

        search_string = search_string.lower().strip()

        item_filter = Q(name__contains=search_string) | Q(description__contains=search_string)
        matched_items = Item.objects.filter(item_filter).order_by('name')[:self.MAX_RESULTS]

        data = {
            "item_names": [item.name for item in matched_items],
        }

        return JsonResponse(data)
