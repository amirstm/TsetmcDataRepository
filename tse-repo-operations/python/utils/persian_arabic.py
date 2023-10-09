"""
Methods used for converting characters of Persian and Arabic
"""


def persian_to_arabic(inp: str) -> str:
    """Converting Persian characters to Arabic"""
    return inp.replace("ک", "ك").replace("ی", "ي")


def arabic_to_persian(inp: str) -> str:
    """Converting Arabic characters to Persian"""
    return inp.replace("ك", "ک").replace("ي", "ی")
