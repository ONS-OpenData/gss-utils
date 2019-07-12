PYTHONUSERBASE=.pip

.EXPORT_ALL_VARIABLES:

behave: .pip/bin/behave setup.py
	python setup.py behave_test --tags=-skip

.pip/bin/behave:
	pip install --cache-dir=.pipcache --user behave nose vcrpy docker
