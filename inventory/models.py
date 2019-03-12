from django.db import models


class Item(models.Model):
    name = models.CharField(max_length=128)
    unit = models.CharField(max_length=16, null=True)
    category = models.CharField(max_length=128, null=True)
    description = models.CharField(max_length=256)
    comment = models.CharField(max_length=256, null=True)
    searchable = models.BooleanField(default=True)

    @property
    def total_amount(self):  # returns total amount of this item
        amount = 0
        for obj in self.iteminsubcontainer_set.all():
            amount += obj.amount
        return amount

    # Skal amount og subcontainer inn her kanskje?

    def __str__(self):
        return "Item: "+self.name

    class Meta:
        indexes = [
            models.Index(fields=['name', ]),
            models.Index(fields=['description', ]),
        ]


class Room(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return "Room: "+self.name


class Container(models.Model):
    name = models.CharField(max_length=128)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    def __str__(self):
        return "Container: "+self.name+" in "+self.room.name


class SubContainer(models.Model):
    name = models.CharField(max_length=128)
    items = models.ManyToManyField(Item, through='ItemInSubContainer')
    container = models.ForeignKey(Container, on_delete=models.CASCADE)

    def __str__(self):
        return "Subcontainer "+self.name + " in container "+self.container.name


class ItemInSubContainer(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    subcontainer = models.ForeignKey(SubContainer, on_delete=models.CASCADE)
    amount = models.DecimalField(decimal_places=2, max_digits=6)

    def __str__(self):
        return self.subcontainer.name + " contains "+str(self.amount)+" of item "+self.item.name

# TODO: Orders are  currently WIP
"""
class Order(models.Model):
    date = models.DateField()
    seller = models.CharField(max_length=128)
    items = models.ManyToManyField(Item, through='ItemInOrder')


class ItemInOrder(models.Model):
    amount = models.PositiveIntegerField()
"""