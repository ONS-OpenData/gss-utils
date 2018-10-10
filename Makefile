test: virtualenv
	.env/bin/pip install behave nose vcrpy
	.env/bin/behave

virtualenv: .env/bin/activate
.env/bin/activate: setup.py
	test -d .env || virtualenv .env
	.env/bin/pip install .
	touch .env/bin/activate
