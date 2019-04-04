from django.http import HttpResponse, JsonResponse
from django.template import loader
# Create your views here.
from django.views.generic import TemplateView

from inventory.models import ItemInSubContainer, Room, Item


class InventoryView(TemplateView):
    template_name = 'inventory/inventory.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_word = kwargs['search_word']
        itemset = Item.objects.filter(name__contains=search_word)
        context.update({
            'items': itemset,
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

        # TODO: Do some sanity checks on search_string...

        result_name = Item.objects.filter(name__contains=search_string)
        result_description = Item.objects.filter(description__contains=search_string)
        data = {
        }

        return JsonResponse(data)
