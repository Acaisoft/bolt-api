create_package:
	python3 setup.py sdist bdist_wheel

run_tests:
	py.test bolt_api/upstream/tests
