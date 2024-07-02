# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import energy_forecast
project = 'Energetic Stress Production'
copyright = '2024, Antoine Tavant, Matthieu Colin'
author = 'Antoine Tavant, Matthieu Colin'
version = energy_forecast.version

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.napoleon',
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
    'sphinx.ext.autodoc',
    'sphinx.ext.mathjax',
    'sphinx_design',
    'nbsphinx',
]


templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# define code executed for each file as if included in it
rst_prolog="""
"""

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output


html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "github_url": "https://github.com/GreenForecast-Squad/energetic-stress-production",
    "announcement": f"<p>Last version is v{version}</p>",
}
html_static_path = ['_static']
html_sidebars = {
    "**": ["search-field.html", "sidebar-nav-bs.html", 'globaltoc.html',]
    # "**": ["search-field.html", "sidebar-nav-bs.html"]
}
# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = False

html_title = f"{project} v{version}"


# -- nbsphinx extension configuration ------------------------------------------
nbsphinx_execute = 'never'  # never, always, or auto (only run if no output available)

# -- Extension configuration -------------------------------------------------
napoleon_use_rtype = False  # move return type inline
