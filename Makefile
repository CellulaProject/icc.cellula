.PHONY: env dev install test edit dev-icc.rdfservice dev-icc.restfuldocs

LPYTHON=python3
V=$(PWD)/../$(LPYTHON)
PYTHON=$(V)/bin/$(LPYTHON)
ROOT=$(PWD)
INI=icc.cellula

env:
	[ -d $(V) ] || virtualenv  $(V)

dev:	env dev-icc.rdfservice dev-icc.restfuldocs
	$(PYTHON) setup.py develop

install: env
	$(PYTHON) setup.py install

edit:
	cd src && emacs

test:
	ip a | grep 2001
	ip a | grep 172.
	. $(V)/bin/activate
	pserve $(INI).ini --reload
	#cd src && $(PYTHON) app.py

dev-icc.rdfservice:
	make -C ../icc.rdfservice
	
dev-icc.restfuldocs:
	make -C ../icc.restfuldocs