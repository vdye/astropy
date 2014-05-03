# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Temporary solution until `astropy.vo.validator.conf.conesearch_master_list`
includes ``<testQuery>`` fields.

In case USVO service is unstable, it does the following:

    #. Try USVO production server.
    #. If fails, try USVO test server (has latest bug fix, but does not
       contain all registered services).
    #. If fails, use RA=0 DEC=0 SR=0.1.

"""
from __future__ import absolute_import, division, print_function, unicode_literals

# STDLIB
import warnings
from xml.dom import minidom

# LOCAL
from ...utils import OrderedDict  # For 2.6 compatibility
from ...utils.data import get_readable_fileobj
from ...utils.exceptions import AstropyUserWarning


def parse_cs(id):
    """Return ``<testQuery>`` pars as dict for given Resource ID."""
    if isinstance(id, bytes):  # pragma: py3
        id = id.decode('ascii')

    # Production server.
    url = 'http://vao.stsci.edu/directory/getRecord.aspx?' \
        'id={0}&format=xml'.format(id)

    # Test server (in case production server fails).
    backup_url = 'http://vaotest.stsci.edu/directory/getRecord.aspx?' \
        'id={0}&format=xml'.format(id)

    tqp = ['ra', 'dec', 'sr']
    d = OrderedDict()
    urls_failed = False
    urls_errmsg = ''

    try:
        with get_readable_fileobj(url, encoding='binary',
                                  show_progress=False) as fd:
            dom = minidom.parse(fd)
    except Exception as e: # pragma: no cover
        try:
            warnings.warn('{0} raised {1}, trying {2}'.format(
                url, str(e), backup_url), AstropyUserWarning)
            with get_readable_fileobj(backup_url, encoding='binary',
                                      show_progress=False) as fd:
                dom = minidom.parse(fd)
        except Exception as e:
            urls_failed = True
            urls_errmsg = '{0} raised {1}, using default'.format(
                    backup_url, str(e))

    if not urls_failed:
        tq = dom.getElementsByTagName('testQuery')
        if tq:
            for key in tqp:
                d[key.upper()] = tq[0].getElementsByTagName(
                    key)[0].firstChild.nodeValue.strip()
        else: # pragma: no cover
            urls_failed = True
            urls_errmsg = 'No testQuery found for {0}, using default'.format(id)

    # If no testQuery found, use RA=0 DEC=0 SR=1
    if urls_failed:  # pragma: no cover
        d = OrderedDict({'RA': '0', 'DEC': '0', 'SR': '0.1'})
        warnings.warn(urls_errmsg, AstropyUserWarning)

    return d
