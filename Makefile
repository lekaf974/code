test:
	pytest --tb=short -v

watch-tests:
	ls *.py | entr pytest --tb=short
