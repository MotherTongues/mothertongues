# Contributing to MotherTongues

Feel free to dive in! [Open an issue](https://github.com/MotherTongues/mothertongues/issues/new) or submit PRs.

This repo follows the [Contributor Covenant](http://contributor-covenant.org/version/1/3/0/) Code of Conduct.

This repo uses automated tools to standardize the formatting of code, text files and
commits.
 - [Pre-commit hooks](#pre-commit-hooks) validate and automatically apply code
   formatting rules.
 - [commitlint](#commitlint) is used as a commit message hook to validate that
   commit messages follow the convention.

## Cloning
To clone and install from source you will have to have Git, Python 3.8+, [poetry](https://python-poetry.org/docs/) and Node 16+ on your machine. You can then follow these steps:

### Clone repo and UI submodule
`git clone https://github.com/MotherTongues/mothertongues.git --recursive`
### Build the UI:
`cd mothertongues/mothertongues-UI && npm install`
### Build the Python Development version of the UI:
`npx nx build mtd-mobile-ui --configuration=pydev`
### Install the Python package:
`cd .. && poetry install`

## Pre-commit Hooks

Run these commands in each of your sandboxes to enable our pre-commit hooks and commitlint:

```sh
pre-commit install
gitlint install-hook
git submodule foreach 'pre-commit install'
git submodule foreach 'gitlint install-hook'
```

## Pre-commit hooks

We systematically use a number of pre-commit hooks to
normalize formatting of code. You need to install and enable pre-commit to have these used automatically when you do your own commits.

Pre-commit hooks enabled:
- check-yaml validates YAML files
- end-of-file-fixer makes sure each text file ends with exactly one newline character
- trailing-whitespace removes superfluous whitespace at the end of lines in text files
- [Flake8](https://flake8.pycqa.org/) enforces good Python style rules; more info about
  using Flake8 in pre-commit hooks at:
  [Lj Miranda flake8 blog post](https://ljvmiranda921.github.io/notebook/2018/06/21/precommits-using-black-and-flake8/)
- [isort](https://pycqa.github.io/isort/) orders python imports in a standard way
- [Black](https://github.com/psf/black), the Uncompromising Code Formatter, refortmats all
  Python code according to very strict rules we've agreed to follow; more info about Black
  formatting rules in
  [The Black code style](https://black.readthedocs.io/en/stable/the_black_code_style.html)
- [mypy](http://mypy-lang.org/) runs type checking for any statically-typed Python code in
  the repo

### Enabling pre-commit hooks

All the pre-commit hooks are executed using a tool called
[pre-commit](https://pre-commit.com/). Once you enable pre-commit, it will run all the
hooks each time you try to commit anything in this repo.

Note that you have to run the second command in every sandbox you create, so please
don't forget to do so when you clone a new sandbox!

## commitlint

We use [Conventional Commits](https://www.conventionalcommits.org/).
Install and enable [gitlint](https://jorisroovers.com/gitlint/) to have your
commit messages scanned automatically.

Convential commits look like this:

    type(optional-scope): subject (i.e., short description)

    optional body, which is free form

    optional footer

Valid types: (these are the default, which we're using as is for now)
 - build: commits for the build system
 - chore: maintain the repo, not the code itself
 - ci: commits for the continuous integration system
 - docs: adding and changing documentation
 - feat: adding a new feature
 - fix: fixing something
 - perf: improving performance
 - refactor: refactor code
 - revert: undo a previous change
 - style: working only on code or documentation style
 - test: commits for testing code

Valid scopes: the scope is optional and usually refers to which module is being changed.
 - TBD - for now not validated, should be just one word ideally

Valid subject: short, free form, what the commit is about in less than 50 or 60 characters
(not strictly enforced, but it's best to keep it short)

Optional body: this is where you put all the verbose details you want about the commit, or
nothing at all if the subject already says it all. Must be separated by a blank line from
the subject. Explain what the changes are, why you're doing them, etc, as necessary.

Optional footer: separated from the body (or subject if body is empty) by a blank line,
lists reference (e.g.: "Closes #12" "Ref #24") or warns of breaking changes (e.g.,
"BREAKING CHANGE: explanation").

These rules are inspired by these commit formatting guides:
 - [Conventional Commits](https://www.conventionalcommits.org/)
 - [Bluejava commit guide](https://github.com/bluejava/git-commit-guide)
 - [develar's commit message format](https://gist.github.com/develar/273e2eb938792cf5f86451fbac2bcd51)
 - [AngularJS Git Commit Message Conventions](https://docs.google.com/document/d/1QrDFcIiPjSLDn3EL15IJygNPiHORgU1_OOAqWjiDU5Y).
