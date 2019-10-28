from django.db import models


class Item(models.Model):
    name = models.CharField(max_length=128)
    unit = models.CharField(max_length=16, null=True)
    description = models.TextField(max_length=256)
    comment = models.TextField(max_length=256, null=True)
    searchable = models.BooleanField(default=True)
    consumable = models.BooleanField(default=False)
    image = models.ImageField(upload_to="inventory", blank=True)

    @property
    def total_amount(self):  # returns total amount of this item
        amount = 0
        for obj in self.iteminsubcontainers.all():
            amount += obj.amount
        return amount

    def __str__(self):
        return f"Item: {self.name}"

    class Meta:
        indexes = [
            models.Index(fields=['name', ]),
            models.Index(fields=['description', ]),
        ]


class Category(models.Model):
    name = models.CharField(max_length=128)
    items = models.ManyToManyField(
        Item,
        related_name="items",
    )

    def __str__(self):
        return f"Category: {self.name}"


class Container(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return f"Container: {self.name}"


class SubContainer(models.Model):
    name = models.CharField(max_length=128)
    items = models.ManyToManyField(
        Item,
        through='ItemInSubContainer',
        related_name="subcontainers",
    )
    container = models.ForeignKey(
        Container,
        on_delete=models.CASCADE,
        related_name="subcontainers",
    )

    def __str__(self):
        return f"Subcontainer {self.name} in container {self.container.name}"


class ItemInSubContainer(models.Model):
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="iteminsubcontainers",
    )
    subcontainer = models.ForeignKey(
        SubContainer,
        on_delete=models.CASCADE,
        related_name="iteminsubcontainers",
    )
    amount = models.DecimalField(decimal_places=2, max_digits=6)

    def __str__(self):
        return f"{self.subcontainer.name} contains {str(self.amount)} of item {self.item.name}"

# TODO: Orders are  currently WIP
"""
class Order(models.Model):
    date = models.DateField()
    seller = models.CharField(max_length=128)
    items = models.ManyToManyField(Item, through='ItemInOrder')


class ItemInOrder(models.Model):
    amount = models.PositiveIntegerField()
"""
