from django.db import models


class Category(models.Model):
    class Meta:
        verbose_name_plural = "categories"

    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class Item(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['name', ]),
            models.Index(fields=['description', ]),
        ]

    name = models.CharField(max_length=128)
    unit = models.CharField(max_length=16, null=True, blank=True)
    description = models.TextField(max_length=256, blank=True)
    comment = models.TextField(max_length=256, null=True, blank=True)
    # searchable = models.BooleanField(default=True)
    consumable = models.BooleanField(default=False)
    image = models.ImageField(upload_to="inventory", blank=True)

    categories = models.ManyToManyField(
        Category,
        related_name="items",
    )

    @property
    def total_amount(self):  # returns total amount of this item
        amount = 0
        for obj in self.items_in_subcontainer.all():
            amount += obj.amount
        return amount

    def __str__(self):
        return self.name


class Container(models.Model):
    class Meta:
        ordering = ["name"]

    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class SubContainer(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name", "container"], name="unique_name_per_container"),
        ]

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
        return f"{self.name} in {self.container}"


class ItemInSubContainer(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["item", "subcontainer"], name="unique_item_and_subcontainer"),
        ]
        verbose_name_plural = "items in subcontainer"

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="items_in_subcontainer",
    )
    subcontainer = models.ForeignKey(
        SubContainer,
        on_delete=models.CASCADE,
        related_name="items_in_subcontainer",
    )
    amount = models.DecimalField(decimal_places=2, max_digits=6)

    def __str__(self):
        return f"{self.subcontainer.name} contains {str(self.amount)} of item {self.item.name}"
