.PHONY: env dev install test edit dev-icc.rdfservice \
    dev-icc.restfuldocs py pot init-ru update-ru comp-cat \
    upd-cat adjust-ini devel

LPYTHON=python3
V=$(PWD)/../$(LPYTHON)
VB=$(V)/bin
PYTHON=$(VB)/$(LPYTHON)
ROOT=$(PWD)
INI=icc.cellula
LCAT=src/icc/cellula/locales/

SERVER_PORT=8081

env:
	[ -d $(V) ] || virtualenv  $(V)
	$(VB)/easy_install --upgrade pip

pre-dev:env dev-icc.rdfservice dev-icc.restfuldocs
	$(VB)/easy_install rdflib pip setuptools
	$(PYTHON) setup.py develop

devel:
	python setup.py develop

dev:	pre-dev upd-cat

install: env comp-cat
	$(PYTHON) setup.py install

edit:
	cd src && emacs

test: adjust-ini
	@ip a | grep 2001 || true
	@ip a | grep 172. || true
	@echo "================================================================"
	@echo "Point Your browser to http://[::1]:$(SERVER_PORT) or http://127.0.0.1:$(SERVER_PORT)"
	@echo "================================================================"
	pserve $(INI).ini --reload
	#cd src && $(PYTHON) app.py

dev-icc.rdfservice:
	make -C ../icc.rdfservice dev

dev-icc.restfuldocs:
	make -C ../icc.restfuldocs dev

py:
	$(PYTHON)

pot:
	mkdir -p $(LCAT)
	$(VB)/pot-create src -o $(LCAT)/messages.pot || echo "Someting unusual with pot."

init-ru:
	$(PYTHON) setup.py init_catalog -l ru -i $(LCAT)/messages.pot \
                         -d $(LCAT)

update-ru:
	$(PYTHON) setup.py update_catalog -l ru -i $(LCAT)/messages.pot \
                            -d $(LCAT)

comp-cat:
	$(PYTHON) setup.py compile_catalog -d $(LCAT)

upd-cat: pot update-ru comp-cat

adjust-ini:
  #	sed 's/HOME/\/home\/$(USER)/' icc.cellula.ini.in > icc.cellula.ini
