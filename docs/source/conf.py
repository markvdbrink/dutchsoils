# Configuration file for the Sphinx documentation builder.

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# -- Project information -----------------------------------------------------

project = "DutchSoils"
copyright = "2025, Mark van den Brink"
author = "Mark van den Brink"
release = "0.3.2"

# -- General configuration ---------------------------------------------------

templates_path = ["_templates"]

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "numpydoc",
    "myst_nb",
    # "sphinx.ext.viewcode",
]

# -- Options for HTML output -------------------------------------------------

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]
html_theme_options = {
    "icon_links": [
        {
            "name": "GitHub",  # Label for this link
            "url": "https://github.com/markvdbrink/dutchsoils",  # required
            "icon": "fab fa-github-square",
            "type": "fontawesome",  # Default is fontawesome
        }
    ],
}

# -- Autodoc and autosummary settings ------------------------------

autodoc_default_options = {
    "autosummary": True,
}
autodoc_typehints = "description"
autodoc_typehints_format = "short"

autosummary_generate = True
autosummary_generate_overwrite = True

# -- Napoleon settings ----------------------------------------------------------------

napoleon_google_docstring = False

# -- Numpydoc settings ----------------------------------------------------------------

numpydoc_class_members_toctree = True
numpydoc_show_class_members = False

# -- Set Intersphinx directories ------------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/devdocs", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable", None),
    "matplotlib": ("https://matplotlib.org/stable", None),
}
