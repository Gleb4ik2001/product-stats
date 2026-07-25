from django.db import models


class Product(models.Model):
    external_id = models.CharField(
        max_length=128, unique=True, db_index=True, verbose_name="Внешний id"
    )
    name = models.CharField(max_length=255, verbose_name="Название")
    category = models.CharField(max_length=128, db_index=True, verbose_name="Категория")
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Цена")
    updated_at = models.DateTimeField(verbose_name="Дата обновления")

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return f"[{self.external_id}] {self.name} ({self.category}) - {self.price}"
