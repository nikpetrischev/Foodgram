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
            return webcolors.hex_to_name(value) + f' ({value})'
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
