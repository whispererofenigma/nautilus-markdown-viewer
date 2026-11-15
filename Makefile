.PHONY: all install uninstall deb clean test test-desktop

PYTHON ?= python3

all: deb

install:
	@./install.sh

uninstall:
	@./uninstall.sh

deb:
	@./packaging/build-deb.sh

test:
	@$(PYTHON) -m py_compile src/viewer/*.py src/extension/*.py
	@$(PYTHON) -m unittest discover -s tests -v

test-desktop:
	@RUN_DESKTOP_TESTS=1 $(PYTHON) -m unittest discover -s tests -v

clean:
	@rm -rf *.deb build_deb
