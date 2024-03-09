black .
isort .
pylint $(git ls-files '*.py')
mypy .