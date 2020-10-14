VERSION=$(shell ddit ditversion)
DIT_NAME=$(shell ddit targetname)

TAG_NAME=v${VERSION}

.PHONY: clean install

all: ${DIT_NAME}

publish: ${DIT_NAME}
	git tag -f "${TAG_NAME}"
	ghr -replace "${TAG_NAME}" "${DIT_NAME}"

${DIT_NAME}: dabl-meta.yaml Makefile
	ddit build --force

clean:
	rm -fr ${DIT_NAME} .daml dist *~ pkg/*~
