# Contributing guidelines

Thank you for considering contributing to DutchSoils! DutchSoils is an open source software project and any contribution is welcome.

You can contribute by:
- Asking questions on the Q&A page.
- Submitting bugs and feature requests.
- Improving documentation.
- Improving/extending the code for everyone to use.

The goal is to maintain a diverse community that is pleasant for everyone. **Please be considerate and respectful of others**. Everyone must abide by our [Code of Conduct](https://github.com/markvdbrink/dutchsoils/blob/main/CODE_OF_CONDUCT.md) and we encourage all to read it carefully.

## For users
Any questions regarding the use of DutchSoils can be posted in the [Q&A discussion section](https://github.com/markvdbrink/dutchsoils/discussions/categories/q-a).
You can also [showcase](https://github.com/markvdbrink/dutchsoils/discussions/categories/show-and-tell) examples where DutchSoils was used.

## For contributers
Please report any bugs or feature suggestions in the [issue section](https://github.com/markvdbrink/dutchsoils/issues).

## For maintainers

### Contributing documentation

There are two ways in which you can improve the documentation: online on GitHub or locally.

To edit documentation online on GitHub, use the following steps:
1. Log in using your GitHub account.
2. Browse to the file with the documentation you want to change. This can either be a `.rst` in the `doc/source` folder or the docstring in the source code located at `src/dutchsoils`.
3. Click "Edit this file" and make your desired changes.
4. Click on the "Commit changes" button. Write in the title a short description of what you did. In the "Extended description", explain why you propose the changes with as much detail as possible.
5. Click on "Create a new branch for this commit and start a pull request" and give your branch a descriptive name, such as `docs/improvement`.
6. Target the pull request on **on the development (`dev`) branch**.
7. We will review your changes and merge them if everything is okay. Your changes will be made public with the next release!

Alternatively, if you want to edit the documentation locally, please refer to [Contributing code](https://dutchsoils.readthedocs.io/en/latest/contribute.html#contributing-code) for instructions.

### Contributing code

#### Set up local environment
To set up a local environment for development of DutchSoils, we recommend using a package manager. Good examples are [poetry](https://python-poetry.org/docs/) (which we use ourselves) or [uv](https://docs.astral.sh/uv/). Install the enviroment using the `pyproject.toml` file. The development packages are listed under `project.optional-dependencies`. With `poetry`, these can be installed using the `--all-extras` flag. Once you have set up the enviroment (only necessary for the first time), activate it by running `.\Scripts\Activate`.

#### Documentation
When defining new functions, please provide it with a docstring. [numpy style guide](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard). All functions/classes/methods should have docstrings with a full description of all arguments and return values.

The documentation files can be found in `docs/source` and use the `.rst` format for which this [cheat sheet](https://docs.generic-mapping-tools.org/6.5/devdocs/rst-cheatsheet.html) might be useful.

To build the documentation locally navigate to `docs` folder. If you have `make` [installed](https://gnuwin32.sourceforge.net/packages/make.htm), you can run `make html`. If not, [run](https://devguide.python.org/documentation/start-documenting/index.html#without-make) `python -m sphinx -b html . build/html`.

#### Testing and linting your code
After writing your code, please run the tests by executing `pytest` in the command line. If your code requires testing as well, please write (unit) tests in the `tests` folder. Each file in this directory should end with `_test.py`. You can use existing tests as a reference. If you are not sure how to make tests, please do not hesitate to reach out or submit you pull request anyway, we can help you with creating the required tests for your code.

Execute `pre-commit run` after staging your changed files for a Git commit. This package uses [Ruff](https://docs.astral.sh/ruff/) as linter to format code consistently.

### Submitting a pull request

When preparing a pull request, please follow these steps:
1. [Submit an issue](https://github.com/markvdbrink/dutchsoils/issues) describing the feature or bug which you want to address.
2. Branch the `main` branch using a descriptive name, such as `feat/xxx`, `docs/xxx` or `issue/xxx`.
3. Commit your changes using [conventional commit messages](https://www.conventionalcommits.org/en/v1.0.0/) starting with indicators such as `feat: `, `fix: `, `docs: ` or `chore: `. Use the body of the commit to explain **why** the changes were made.
4. Submit a pull request on the `dev` branch of the `markvdbrink/dutchsoils` repo.
