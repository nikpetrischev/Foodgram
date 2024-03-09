# Standard Library
import io
from typing import Any

# DRF Library
from rest_framework.renderers import BaseRenderer

# Reportlab
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics, ttfonts
from reportlab.pdfgen import canvas
from reportlab.platypus.tables import Table, TableStyle

# Offsets for landscape A4 page format, cm
TITLE_OFFSETS = {
    'vertical': 19.5,
    'horizontal': 2,
}
TABLE_OFFSETS = {
    'vertical': 16,
    'horizontal': 2,
}


class ShoppingCartRenderer(BaseRenderer):
    """
    Custom renderer for generating a PDF report of a user's shopping cart.

    This renderer extends the BaseRenderer class from Django Rest Framework
    to create a PDF document that lists the items in a user's shopping cart.
    It uses the ReportLab library to generate the PDF and customizes the
    appearance of the document, including the font and layout.

    Attributes
    ----------
    media_type : str
        The media type of the rendered content. Default is 'application/pdf'.
    format : str
        The format of the rendered content. Default is 'pdf'.
    """
    media_type: str = 'application/pdf'
    format: str = 'pdf'

    def render(
            self,
            data: Any,
            accepted_media_type: Any = None,
            renderer_context: Any = None,
    ) -> bytes:
        """
        Renders the shopping cart data into a PDF document.

        This method processes the shopping cart data, creates a PDF document
        with a table listing the items, and returns the PDF content as bytes.

        Parameters
        ----------
        data : Any
            The shopping cart data to be rendered.
        accepted_media_type : Any, optional
            The media type that is acceptable for the response.
            Default is None.
        renderer_context : Any, optional
            The context for the renderer. Default is None.

        Returns
        -------
        bytes
            The rendered PDF content as bytes.
        """
        buffer: io.BytesIO = io.BytesIO()

        # Adding font supporting cyrillic letters.
        pdfmetrics.registerFont(
            ttfonts.TTFont(
                'DejaVuSerif',
                './static/font/DejaVuSerif.ttf',
            ),
        )

        # Generate list for visualising table to be.
        cart_list: list[tuple] = [('Продукт', 'Ед.изм.', 'Кол-во')]
        for item in data:
            cart_list.append(
                (
                    item['ingredient__name'],
                    item['ingredient__measurement_unit'],
                    item['total'],
                ),
            )

        # Table 3 column wide. Title background is black,
        # rows' background changes between white and light grey.
        # Columns 2 and 3 are center-aligned.
        table: Table = Table(cart_list, colWidths=(15 * cm, 3 * cm, 5 * cm))
        table.setStyle(
            TableStyle(
                (
                    ('GRID', (0, 0), (-1, -1), 1, (0, 0, 0)),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSerif', 18),
                    ('BACKGROUND', (0, 0), (-1, 0), (0, 0, 0)),
                    ('TEXTCOLOR', (0, 0), (-1, 0), (1, 1, 1)),
                    ('LINEBEFORE', (1, 0), (1, 0), 2, (1, 1, 1)),
                    ('LINEBEFORE', (2, 0), (2, 0), 2, (1, 1, 1)),
                    ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSerif', 14),
                    (
                        'ROWBACKGROUNDS',
                        (0, 1),
                        (-1, -1),
                        ((1, 1, 1), (210 / 255, 210 / 255, 210 / 255)),
                    ),
                ),
            ),
        )

        # Creating canvas and applying Title on them.
        page: canvas.Canvas = canvas.Canvas(buffer, pagesize=landscape(A4))
        page.setFont('DejaVuSerif', 24)
        page.drawString(
            x=TITLE_OFFSETS'horizontal'] * cm,
            y=TITLE_OFFSETS['vertical'] * cm,
            text='Список покупок',
        )
        # Adding table to canvas.
        table.wrapOn(
            canv=page,
            aW=A4[1],
            aH=A4[0],
        )
        table.drawOn(
            canvas=page,
            x=TABLE_OFFSETS['horizontal'] * cm,
            y=TABLE_OFFSETS['vertical'] * cm,
        )

        # Finishing document
        page.showPage()
        page.save()

        return buffer.getvalue()
