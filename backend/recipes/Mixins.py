# Django Library
from django.db import models


class NameAndStrAbstract(models.Model):
    name = models.CharField(
        max_length=200,
        null=False,
        blank=False,
        verbose_name='Наименование',
    )
    objects = models.Manager()

    class Meta:
        abstract = True

    def __str__(self):
        return self.name
