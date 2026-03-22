STAMPED_MD := stamped-examples.md
STAMPED_PDF := stamped-examples.pdf

all: pdf

serve-devel:
	hugo server --enableGitInfo --bind 0.0.0.0

pdf: $(STAMPED_PDF)

$(STAMPED_MD): content/examples/*.md scripts/build-pdf.py
	python3 scripts/build-pdf.py -o $@

$(STAMPED_PDF): $(STAMPED_MD)
	pandoc $< -o $@ \
		--pdf-engine=xelatex \
		--toc \
		-V geometry:margin=1in \
		-V 'mainfont=DejaVu Serif' \
		--highlight-style=tango

test: test-snippets test-hugo

test-snippets:
	pytest content/ -v

test-hugo:
	hugo --gc --minify

materialize:
	tox -e materialize

rematerialize:
	tox -e rematerialize

clean:
	rm -f $(STAMPED_MD) $(STAMPED_PDF)
	rm -rf public/

.PHONY: all serve-devel pdf clean test test-snippets test-hugo materialize rematerialize
