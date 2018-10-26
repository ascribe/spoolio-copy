# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import sys

import sphinx_rtd_theme

sys.path.insert(0, os.path.abspath('../..'))


extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
]
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = u'ascribe'
copyright = u'2016, ascribe'
author = u'ascribe'
version = u'0.0.1'
release = u'0.0.1'
language = None
exclude_patterns = []
pygments_style = 'sphinx'
todo_include_todos = True
html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_static_path = ['_static']
htmlhelp_basename = 'ascribedoc'
latex_elements = {}
latex_documents = [
    (master_doc, 'ascribe.tex', u'ascribe Documentation',
     u'ascribe', 'manual'),
]
man_pages = [
    (master_doc, 'ascribe', u'ascribe Documentation',
     [author], 1)
]
texinfo_documents = [
    (master_doc, 'ascribe', u'ascribe Documentation',
     author, 'ascribe', 'One line description of project.',
     'Miscellaneous'),
]
intersphinx_mapping = {'https://docs.python.org/': None}
