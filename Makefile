create_package:
	python3 setup.py sdist bdist_wheel

run_tests:
	python -m unittest app.validators.tests.test_test_creator app.models.tests.test_test_creator
