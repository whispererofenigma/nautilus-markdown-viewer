.PHONY: all install uninstall deb clean test

all: deb

install:
	@./install.sh

uninstall:
	@./uninstall.sh

deb:
	@./packaging/build-deb.sh

test:
	@python3 -m py_compile src/viewer/*.py src/extension/*.py
	@echo "All Python syntax checks passed!"

clean:
	@rm -rf *.deb build_deb
