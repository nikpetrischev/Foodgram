# Django Library
from django.db import models


class NameAndStrAbstract(models.Model):
    """
    An abstract base model for models with a name field and a string representation.

    This model includes a 'name' field, which is a CharField with a maximum length of 200 characters.
    It also defines a custom string representation for the model instances,
    which returns the value of the 'name' field.
    This abstract model can be used as a base class for other models
    that require a name field and a custom string representation.
    """
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
        """
        Return a string representation of the model instance.

        This method returns the value of the 'name' field,
        providing a human-readable representation of the model instance.

        Returns
        -------
        str
            The value of the 'name' field.
        """
        return self.name
