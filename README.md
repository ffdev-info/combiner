# combiner

Combiner is a small utility to combine [ffdev.info][ffdev-1] signature files
into one signature file for bulk testing.

The application makes sure that identifiers are unique and align for all
input xml. It also makes sure that PUIDs are unique. You can use an optional
prefix using `--prefix` so that PUIDs are recognizable in your workflow.

[ffdev-1]: https://ffdev.info

## CLI options

For more information run `python combiner.py --help`.

<!--markdownlint-disable-->

```text
usage: combiner [-h] [--debug] [--path PATH] [--prefix PREFIX] [--start-index START_INDEX] [--version]

combine development signature files into one

options:
  -h, --help            show this help message and exit
  --debug               use debug loggng
  --path PATH           directory where the signature files are
  --prefix PREFIX       prefix for custom puids
  --start-index START_INDEX
                        integer from which to start the signature index (for DROID copy-paste)
  --version             print version information

for more information visit https://github.com/ffdev-info/combiner
```

<!--markdownlint-enable-->

## Developer install

### pip

Setup a virtual environment `venv` and install the local development
requirements as follows:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements/local.txt
```

### tox

#### Run tests (all)

```bash
python -m tox
```

#### Run tests-only

```bash
python -m tox -e py3
```

#### Run linting-only

```bash
python -m tox -e linting
```

### pre-commit

Pre-commit can be used to provide more feedback before committing code. This
reduces reduces the number of commits you might want to make when working on
code, it's also an alternative to running tox manually.

To set up pre-commit, providing `pip install` has been run above:

* `pre-commit install`

This repository contains a default number of pre-commit hooks, but there may
be others suited to different projects. A list of other pre-commit hooks can be
found [here][pre-commit-1].

[pre-commit-1]: https://pre-commit.com/hooks.html

## Packaging

The [`justfile`][just-1] contains helper functions for packaging and release.
Run `just help` for more information.

[just-1]: https://github.com/casey/just

### pyproject.toml

Packaging consumes the metadata in `pyproject.toml` which helps to describe
the project on the official [pypi.org][pypi-2] repository. Have a look at the
documentation and comments there to help you create a suitably descriptive
metadata file.

### Versioning

Versioning in Python can be hit and miss. You can label versions for
yourself, but to make it reliaable, as well as meaningful is should be
controlled by your source control system. We assume git, and versions can
be created by tagging your work and pushing the tag to your git repository,
e.g. to create a release candidate for version 1.0.0:

```sh
git tag -a 1.0.0-rc.1 -m "release candidate for 1.0.0"
git push origin 1.0.0-rc.1
```

When you build, a package will be created with the correct version:

```sh
make package-source
### build process here ###
Successfully built python_repo-1.0.0rc1.tar.gz and python_repo-1.0.0rc1-py3-none-any.whl
```

### Local packaging

To create a python wheel for testing locally, or distributing to colleagues
run:

* `make package-source`

A `tar` and `whl` file will be stored in a `dist/` directory. The `whl` file
can be installed as follows:

* `pip install <your-package>.whl`

### Publishing

Publishing for public use can be achieved with:

* `make package-upload-test` or `make package-upload`

`make-package-upload-test` will upload the package to [test.pypi.org][pypi-1]
which provides a way to look at package metadata and documentation and ensure
that it is correct before uploading to the official [pypi.org][pypi-2]
repository using `make package-upload`.

[pypi-1]: https://test.pypi.org
[pypi-2]: https://pypi.org
