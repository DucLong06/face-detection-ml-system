.PHONY: diagrams clean check

D2_FILES := $(wildcard *.d2)
SVG_FILES := $(D2_FILES:%.d2=out/%.svg)
D2_BIN ?= $(HOME)/.local/bin/d2

diagrams: $(SVG_FILES)

out/%.svg: %.d2 style/tokens.d2
	@mkdir -p out
	$(D2_BIN) --layout=elk $< $@

check:
	@for f in $(D2_FILES); do \
		echo "Validating $$f..."; \
		$(D2_BIN) fmt $$f > /dev/null || exit 1; \
	done
	@echo "All diagrams valid"

clean:
	rm -rf out/

install-d2:
	curl -fsSL https://d2lang.com/install.sh | sh -s --
