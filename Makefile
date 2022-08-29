VENV=.venv

LICENSE_CONFIG?="license-config.json"

LICENSE:
	@echo "you must have a LICENSE file" 1>&2
	exit 1

LICENSE_HEADER:
	@echo "you must have a LICENSE_HEADER file" 1>&2
	exit 1

node_modules/license-check-and-add:
	npm ci

.PHONY: license
license: LICENSE_HEADER
	npm run license:fix

.PHONY: license-deploy
license-deploy: node_modules/license-check-and-add LICENSE LICENSE_HEADER
	LICENSE_CONFIG=${LICENSE_CONFIG} npm run license:deploy

PHONY: test
test: $(VENV)
	rm -rf tests/fixtures/data_out/*/*
	# requires a valid http url:
	GRAPHQL_ENDPOINT=http://graphql poetry run coverage run \
		--omit="$(PWD)/tests $(VENV)" \
		-m py.test -vv $(args)
