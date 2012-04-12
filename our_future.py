# File name: our_future.py
# This file is part of: pyuni
#
# LICENSE
#
# The contents of this file are subject to the Mozilla Public License
# Version 1.1 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See
# the License for the specific language governing rights and limitations
# under the License.
#
# Alternatively, the contents of this file may be used under the terms
# of the GNU General Public license (the  "GPL License"), in which case
# the provisions of GPL License are applicable instead of those above.
#
# FEEDBACK & QUESTIONS
#
# For feedback and questions about pyuni please e-mail one of the
# authors named in the AUTHORS file.
########################################################################
"""
Importing all symbols from this file will include some of the python3
changes in our code. Currently, this only affects the builtins range,
zip, map and filter, which will behave mostly like their py3 versions.
"""

from __future__ import unicode_literals, print_function, division
__all__ = ["range", "zip", "map", "filter"]

from itertools import izip, imap, ifilter

range = xrange
"""Alias of :func:`xrange`"""

zip = izip
"""Alias of :func:`itertools.izip`"""

map = imap
"""Alias of :func:`itertools.imap`"""

filter = ifilter
"""Alias of :func:`itertools.ifilter`"""
