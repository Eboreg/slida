from PySide6.QtCore import QSize, QSizeF


def get_subsquare_count(bounds: QSize | QSizeF, min_width: int):
    columns = int(bounds.width() / min_width)
    sub_width = bounds.width() / columns
    rows = round(bounds.height() / sub_width)

    return rows, columns
