from django.db import models


# Create your models here.


class Item(models.Model):
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=256)

class Room(models.Model):
    name = models.CharField(max_length=128)


class Container(models.Model):
    name = models.CharField(max_length=128)
    room = models.ForeignKey(Room,on_delete=models.CASCADE)


class SubContainer(models.Model):
    name = models.CharField(max_length=128)
    items = models.ManyToManyField(Item, through='ItemInSubContainer')
    container = models.ForeignKey(Container, on_delete=models.CASCADE)

class ItemInSubContainer(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    subcontainer = models.ForeignKey(SubContainer, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()

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