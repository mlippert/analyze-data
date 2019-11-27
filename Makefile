#
# Makefile to build and test the next-analytics
#

# force the shell used to be bash in case for some commands we want to use
# set -o pipefail ex:
#    set -o pipefail ; SOMECOMMAND 2>&1 | tee $(LOG_FILE)
SHELL := /bin/bash

# Test if a variable has a value, callable from a recipe
# like $(call ndef,ENV)
ndef = $(if $(value $(1)),,$(error $(1) not set))

GIT_TAG_VERSION = $(shell git describe)

PYLINT := pylint
PYSTYLE := pycodestyle
BABEL = ./node_modules/.bin/babel
ESLINT = ./node_modules/.bin/eslint

LINT_LOG := logs/lint.log
TEST_LOG := logs/test.log

# Add --quiet to only report on errors, not warnings
ESLINT_OPTIONS = --ext .js --ext .jsx
ESLINT_FORMAT = stylish

PYSOURCES = \
	pysrc/main.py

# Pattern rules
# lint a python source
# a lint error shouldn't stop the build
%.lint : %.py
	$(call ndef,VIRTUAL_ENV)
	-$(PYLINT) $< | tee $@
	-$(PYSTYLE) $< | tee --append $@
	-@cat $@ >> $(LINT_LOG)


.DEFAULT_GOAL := help
.DELETE_ON_ERROR :
.PHONY : all init install build lint-log vim-lint lint test clean clean-build help

init : install build ## run install, build; intended for initializing a fresh repo clone

install : VER ?= 3
install : ## create python3 virtual env, install requirements (define VER for other than python3)
	@python$(VER) -m venv venv
	@ln -s venv/bin/activate activate
	@source activate                        ; \
	pip install --upgrade pip setuptools    ; \
	pip install -r requirements.txt

build : lint ## build the analyze-data
	@echo "No building is currently needed to run analyze-data"

lint : clean-lintlog $(patsubst %.py,%.lint,$(PYSOURCES)) ## run lint over all python source updating the .lint files

lint-log : ESLINT_OPTIONS += --output-file $(LINT_LOG) ## run eslint concise diffable output to $(LINT_LOG)
lint-log : ESLINT_FORMAT = unix
vim-lint : ESLINT_FORMAT = unix ## run eslint in format consumable by vim quickfix
eslint : ## run lint over the sources & tests; display results to stdout
eslint vim-lint lint-log :
	$(ESLINT) $(ESLINT_OPTIONS) --format $(ESLINT_FORMAT) src

test : ## (Not implemented) run the unit tests
	@echo test would run "$(MOCHA) --reporter spec test | tee $(TEST_LOG)"

clean : clean-build ## remove ALL created artifacts

clean-build : ## remove all artifacts created by the build target
	find . -name \*.lint -type f -print -delete

clean-lintlog :
	@rm $(LINT_LOG) 2> /dev/null || true

outdated : ## check for newer versions of required python packages
	$(call ndef,VIRTUAL_ENV)
	pip list --outdated

upgrade-deps : ## upgrade to the latest versions of required python packages
	$(call ndef,VIRTUAL_ENV)
	pip install --upgrade -r requirements.txt

upgrade-pip : ## upgrade pip and setuptools
	$(call ndef,VIRTUAL_ENV)
	pip install --upgrade pip setuptools

## Help documentation à la https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
## if you want the help sorted rather than in the order of occurrence, pipe the grep to sort and pipe that to awk
help :
	@echo ""                                                                   ; \
	echo "Useful targets in this next-analytics Makefile:"                     ; \
	(grep -E '^[a-zA-Z_-]+ ?:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = " ?:.*?## "}; {printf "\033[36m%-20s\033[0m : %s\n", $$1, $$2}') ; \
	echo ""                                                                    ; \
	echo "If VIRTUAL_ENV needs to be set for a target, run '. activate' first" ; \
	echo ""
