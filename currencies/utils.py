import pycountry


def get_currency_alpha(iso_numeric_code: int) -> str | None:
    # 840 -> USD (якщо pycountry знає)
    s = str(iso_numeric_code).zfill(3)
    try:
        c = pycountry.currencies.get(numeric=s)
    except KeyError:
        return None
    return getattr(c, "alpha_3", None)
