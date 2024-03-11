# DRF Library
import base64

from django.core.files.base import ContentFile
from rest_framework import serializers

import webcolors


class Hex2NameColorField(serializers.Field):
    """
    A custom serializer field to convert hex color codes to their names.

    This field is used to validate and convert hex color codes
    to their corresponding color names using the `webcolors` library.
    """

    def to_representation(self, value: str) -> str:
        """
        Convert the internal hex color code to its corresponding color name.

        Parameters
        ----------
        value : str
            The internal hex color code.

        Returns
        -------
        str
            The color name corresponding to the hex color code.

        Raises
        ------
        serializers.ValidationError
            If the hex color code cannot be converted to a color name.
        """
        try:
            return webcolors.hex_to_name(value)
        except ValueError:
            return value

    def to_internal_value(self, data: str) -> str:
        """
        Validate the input data as a hex color code.

        Parameters
        ----------
        data : str
            The input data to validate.

        Returns
        -------
        str
            The validated hex color code.

        Raises
        ------
        serializers.ValidationError
            If the input data is not a valid hex color code.
        """
        try:
            webcolors.name_to_hex(data)
        except ValueError:
            raise serializers.ValidationError('Неверный формат цвета')
        return data


class Base64ImageField(serializers.ImageField):
    """
    A custom serializer field for handling base64 encoded images.

    This field is used to validate and convert base64 encoded image strings to
    Django ContentFile objects.
    """

    def to_internal_value(self, data: str) -> ContentFile:
        """
        Validate and convert the input data to the internal value.

        Parameters
        ----------
        data : str
            The input data to validate and convert.

        Returns
        -------
        ContentFile
            The converted internal value.

        Raises
        ------
        serializers.ValidationError
            If the input data is not a valid base64 encoded image.
        """
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)
