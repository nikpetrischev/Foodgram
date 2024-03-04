# Standart Library
import io

# DRF Library
from rest_framework import renderers

from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics, ttfonts
from reportlab.pdfgen import canvas
from reportlab.platypus.tables import Table, TableStyle


class ShoppingCartRenderer(renderers.BaseRenderer):
    media_type = 'application/pdf'
    format = 'pdf'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        buffer = io.BytesIO()

        pdfmetrics.registerFont(
            ttfonts.TTFont(
                'DejaVuSerif',
                './static/font/DejaVuSerif.ttf',
            ),
        )

        cart_list = [('Продукт', 'Ед.изм.', 'Кол-во')]
        for item in data:
            cart_list.append(
                (
                    item['ingredient__name'],
                    item['ingredient__measurement_unit'],
                    item['total'],
                ),
            )
        table = Table(cart_list, colWidths=(20 * cm, 3 * cm, 5 * cm))

        table.setStyle(
            TableStyle(
                [
                    ('GRID', (0, 0), (-1, -1), 1, (0, 0, 0)),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSerif', 18),
                    ('BACKGROUND', (0, 0), (-1, 0), (0, 0, 0)),
                    ('TEXTCOLOR', (0, 0), (-1, 0), (1, 1, 1)),
                    ('LINEBEFORE', (1, 0), (1, 0), 2, (1, 1, 1)),
                    ('LINEBEFORE', (2, 0), (2, 0), 2, (1, 1, 1)),
                    ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSerif'),
                    (
                        'ROWBACKGROUNDS',
                        (0, 1),
                        (-1, -1),
                        [(1, 1, 1), (210 / 255, 210 / 255, 210 / 255)],
                    ),
                ],
            ),
        )

        page = canvas.Canvas(buffer)
        page.drawString(0, 0, 'Список покупок')
        # table.wrapOn(page, 2.5 * cm, 2.5 * cm)
        table.drawOn(page, 2.5 * cm, 2.5 * cm)
        page.showPage()
        page.save()

        return buffer.getvalue()
