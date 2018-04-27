from django.db import models


# Create your models here.


class Order(models.Model):
    date = models.DateField()
    seller = models.CharField(max_length=128)
    items = models.ManyToManyField(Item, through='ItemInOrder')


class ItemInOrder(models.Model):
    amount = models.PositiveIntegerField()

class Item(models.Model):
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=256)


class ItemInSubContainer(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    subcontainer = models.ForeignKey(Item, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()


class SubContainer(models.Model):
    name = models.CharField(max_length=128)
    items = models.ManyToManyField(Item, through='ItemInSubContainer')
    container = models.ForeignKey(Container, on_delete=models.CASCADE)


class Container(models.Model):
    name = models.CharField(max_length=128)
    room = models.ForeignKey(Room)


class Room(models.Model):
    name = models.CharField(max_length=128)
