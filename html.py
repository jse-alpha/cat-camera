"""
HTML code for cat camera
"""

import shutil
import json
from datetime import datetime, timedelta
from pathlib import Path
from string import Template


_TO_HTML_KWARGS = {
    # Represent NaN (Not a Number) and other null values as empty strings
    'na_rep': '',

    # Format floating point numbers to 2 decimal places
    'float_format': '{:,.2f}'.format,
    'justify': 'center',
    'show_dimensions': False,
}

def _html_str_replace(
    html: str,
    mapped: dict = {
        r'\r': '.',
        r'\n': ' ',
        '>NaT<': '><'
    }
) -> str:

    ''' Replace characters in html based on mapped dict. '''

    for chars in mapped:
        html = html.replace(chars, mapped[chars])

    return html


def load_html_template(
    html_template_path: Path = Path("template/camera_page_template.html")
) -> str:

    ''' Load HTML template string. '''

    with open(
        html_template_path
    ) as template_file:

        template = Template(template_file.read())

    params = {
        'cam_version': __version__
    }

    html = template.substitute(params)

    # Remove NaT (not a time)
    return _html_str_replace(html)
