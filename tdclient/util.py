from datetime import datetime
import io
import logging
from urllib.parse import quote as urlquote

import msgpack


log = logging.getLogger(__name__)


def create_url(tmpl, **values):
    """Create url with values

    Args:
        tmpl (str): url template
        values (dict): values for url
    """
    quoted_values = {k: urlquote(str(v)) for k, v in values.items()}
    return tmpl.format(**quoted_values)


def parse_csv_value(s):
    """Parse and convert value to suitable types

    Args:
        s (str): value on csv
    Returns:
        Suitable value (int, float, str, bool or None)
    """
    try:
        return int(s)
    except (OverflowError, ValueError):
        try:
            return float(s)
        except (OverflowError, ValueError):
            pass
    lower = s.lower()
    if lower in ("false", "true"):
        return "true" == lower
    elif lower in ("", "none", "null"):
        return None
    else:
        return s


def create_msgpack(items):
    """Create msgpack streaming bytes from list

    Args:
        items (list of dict): target list

    Returns:
        Converted msgpack streaming (bytes)

    Examples:

        >>> t1 = int(time.time())
        >>> l1 = [{"a": 1, "b": 2, "time": t1}, {"a":3, "b": 6, "time": t1}]
        >>> create_msgpack(l1)
        ``b'\x83\xa1a\x01\xa1b\x02\xa4time\xce]\xa5X\xa1\x83\xa1a\x03\xa1b\x06\xa4time\xce]\xa5X\xa1'``
    """
    stream = io.BytesIO()
    packer = msgpack.Packer()
    for item in items:
        try:
            mp = packer.pack(item)
        except (OverflowError, ValueError):
            packer.reset()
            mp = packer.pack(normalized_msgpack(item))
        stream.write(mp)

    return stream.getvalue()


def normalized_msgpack(value):
    """Convert int to str if overflow

    Args:
        value (int, float, str, bool or None): value to be normalized

    Returns:
        Normalized value
    """
    if isinstance(value, (list, tuple)):
        return [normalized_msgpack(v) for v in value]
    elif isinstance(value, dict):
        return dict(
            [(normalized_msgpack(k), normalized_msgpack(v)) for (k, v) in value.items()]
        )

    if isinstance(value, int):
        if -(1 << 63) < value < (1 << 64):
            return value
        else:
            return str(value)
    else:
        return value


def get_or_else(hashmap, key, default_value=None):
    """ Get value or default value
    Args:
        hashmap (dict): target
        key (Any): key
        default_value (Any): default value
    Returns:
        value of key or default_value
    """
    value = hashmap.get(key)
    if value is None:
        return default_value
    else:
        if 0 < len(value.strip()):
            return value
        else:
            return default_value


def parse_date(s, fmt):
    """Parse date from str to datetime using fmt

    TODO: parse datetime with using format string
    for now, this ignores given format string since API may return date in ambiguous format :(

    Args:
       s (str): target str
       fmt (str): format for datetime
    Returns:
       datetime
    """
    try:
        return datetime.strptime(s, fmt)
    except ValueError:
        log.warning("Failed to parse date string: %s as %s" % (s, fmt))
        return None
