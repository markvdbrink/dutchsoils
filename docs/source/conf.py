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
release = "0.2.1"

# -- General configuration ---------------------------------------------------

templates_path = ["_templates"]

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    # 'sphinx.ext.doctest',
    "numpydoc",
]

# -- Options for HTML output -------------------------------------------------

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]

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
