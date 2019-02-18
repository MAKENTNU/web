from django.http import HttpResponse
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


def index(request):
    queryset = ItemInSubContainer.objects.values()
    output = '<br/>'.join([q.__str__() for q in queryset])
    template = loader.get_template('inventory/index.html')
    context = {
        'output': output
    }
    return HttpResponse(template.render(context, request))


def items(request):
    items = Item.objects.values()
    print(request)
    context = {
        'items': items
    }
    template = loader.get_template('inventory/inventory.html')
    return HttpResponse(template.render(context, request))


def item(request):
    return HttpResponse("an item boys")
