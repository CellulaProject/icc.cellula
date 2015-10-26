.PHONY: env dev install test edit dev-icc.rdfservice dev-icc.restfuldocs py

LPYTHON=python3
V=$(PWD)/../$(LPYTHON)
VB=$(V)/bin
PYTHON=$(VB)/$(LPYTHON)
ROOT=$(PWD)
INI=icc.cellula

env:
	[ -d $(V) ] || virtualenv  $(V)
	$(VB)/easy_install --upgrade pip

dev:	env dev-icc.rdfservice dev-icc.restfuldocs
	$(V)/bin/pip install rdflib
	$(PYTHON) setup.py develop

install: env
	$(PYTHON) setup.py install

edit:
	cd src && emacs

test:
	ip a | grep 2001
	ip a | grep 172.
	#. $(V)/bin/activate
	$(VB)/pserve $(INI).ini --reload
	#cd src && $(PYTHON) app.py

dev-icc.rdfservice:
	make -C ../icc.rdfservice dev
	
dev-icc.restfuldocs:
	make -C ../icc.restfuldocs dev
	
py:	
	$(PYTHON)