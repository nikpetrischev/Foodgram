# DRF Library
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
        Display color's hex value.

        Parameters
        ----------
        value : str
            The internal color's value.

        Returns
        -------
        str
            The represented value.
        """
        return value

    def to_internal_value(self, data: str) -> str:
        """
        Convert the input data to the internal value.

        Parameters
        ----------
        data : str
            The input data to convert.

        Returns
        -------
        str
            The converted internal value.

        Raises
        ------
        serializers.ValidationError
            If the input data cannot be converted to a color name.
        """
        try:
            data: str = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Не найдено имя для цвета')
        return data
