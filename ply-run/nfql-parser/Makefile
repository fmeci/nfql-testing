.PHONY: test clean bootstrap 

clean:
	rm parser.out
	rm parsetab.py
	rm output/*
	
bootstrap: _virtualenv setup
	_virtualenv/bin/pip3-2 install -e .
ifneq ($(wildcard requirements.txt),)
	_virtualenv/bin/pip3-2 install -r test-requirements.txt
endif
	make clean

_virtualenv:
	virtualenv _virtualenv

test:
	python3.2 src/main.py $(wildcard tests/*.flw)
	mv tests/*.json output

