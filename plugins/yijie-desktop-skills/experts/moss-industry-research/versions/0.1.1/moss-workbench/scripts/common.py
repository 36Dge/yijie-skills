"""Reviewed YiJie standard-library input and output helpers; no network."""
import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


def number(value, label, minimum=None, maximum=None, optional=False):
    if value is None and optional:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError(label + ': explicit finite number required')
    try:
        result = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError(label + ': invalid number') from error
    if not result.is_finite() or abs(result) > Decimal('1e20'):
        raise ValueError(label + ': unsupported number')
    if minimum is not None and result < minimum or maximum is not None and result > maximum:
        raise ValueError(label + ': outside supported range')
    return result


def text(value, label):
    if not isinstance(value, str) or not value.strip() or len(value) > 4000:
        raise ValueError(label + ': non-empty text required (max 4000)')
    if any(ord(c) < 32 and c not in '\t\n\r' for c in value):
        raise ValueError(label + ': unsupported control character')
    return value


def day(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('Date must be YYYY-MM-DD')
    return date.fromisoformat(value)


def read_json(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 2_000_000:
        raise ValueError('Input must be an ordinary JSON file, at most 2 MB')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(path.read_text(), parse_float=Decimal, object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def dumps(value):
    return json.dumps(value, ensure_ascii=False, indent=2,
                      default=lambda v: str(v) if isinstance(v, Decimal) else (_ for _ in ()).throw(TypeError(type(v).__name__))) + '\n'


def output_folder(path):
    path = Path(path).absolute()
    here = Path(__file__).resolve().parent
    package = here.parent if here.name == 'scripts' else here
    if path.is_symlink() or package == path.resolve() or package in path.resolve().parents:
        raise ValueError('Outputs must be outside managed expert resources')
    path.mkdir(parents=False, exist_ok=False)
    return path


def save_json(path, value):
    with Path(path).open('x') as stream:
        stream.write(dumps(value))


def fields(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= value.keys() or value.keys() - set(required) - set(optional):
        raise ValueError('Input fields differ from the supported schema: ' + ', '.join(required))

