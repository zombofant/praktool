# encoding=utf-8
"""
Make use of the django template language. If you are going to use this
module, make sure you call :func:`django.conf.settings.configure` before
importing this module.
"""

from __future__ import division, unicode_literals, print_function
from our_future import *

from django.template import Template, Context
