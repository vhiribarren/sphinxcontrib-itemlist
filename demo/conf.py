import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'demo'
copyright = '2022, Vincent Hiribarren'
author = 'Vincent Hiribarren'

extensions = [ "sphinx_reqlist" ]

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'alabaster'
html_static_path = ['_static']
html_theme_options = {
    'nosidebar': True,
}