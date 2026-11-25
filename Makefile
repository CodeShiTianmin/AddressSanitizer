# AddressSanitizer (USENIX ATC'12) replication - top-level entry points.
# All targets run inside the pinned Docker image (see Dockerfile).
# Set NATIVE=1 to run directly on a host that already has clang-18 + python3.

IMAGE   ?= asan-repl:1.0
ifeq ($(NATIVE),1)
RUN :=
else
RUN := scripts/in_docker.sh
endif

.PHONY: all image fetch inputs build env smoke run main controls redzone malloc-profile analyze report clean distclean binsize

all: image fetch inputs build run analyze report

image:                      ## build the pinned experiment container
	docker build -t $(IMAGE) .

fetch:                      ## download + sha256-verify third-party sources
	scripts/fetch.sh

inputs: fetch               ## generate deterministic workload inputs into data/
	$(RUN) python3 scripts/gen_inputs.py

build: fetch                ## build all benchmarks in all configurations (base asan asanwo asanlean)
	$(RUN) scripts/build_all.sh

env:                        ## record hardware / software environment
	$(RUN) scripts/env_info.sh > results/env.txt
	scripts/host_info.sh >> results/env.txt

smoke: build inputs         ## one quick run of every variant (sanity check, not recorded in results/)
	$(RUN) python3 scripts/run_experiments.py main --runs 1 --tag smoke

run: env main controls redzone malloc-profile binsize

binsize:                    ## executable size of every build
	$(RUN) python3 scripts/run_experiments.py binsize

main:                       ## C1-C3: base vs ASan vs ASan writes-only (15 runs)
	$(RUN) python3 scripts/run_experiments.py main
controls:                   ## controlled re-runs (modern defaults, lean instrumentation)
	$(RUN) python3 scripts/run_experiments.py controls
redzone:                    ## extension: heap redzone sweep
	$(RUN) python3 scripts/run_experiments.py redzone
malloc-profile:             ## allocation counts of the base binaries
	$(RUN) python3 scripts/run_experiments.py malloc-profile

analyze:                    ## tables + figures from results/raw -> results/ and report/figures
	$(RUN) python3 analysis/analyze.py

report: analyze             ## compile report/report.pdf
	$(RUN) bash -c "cd report && pdflatex -interaction=nonstopmode -halt-on-error report.tex >/dev/null && pdflatex -interaction=nonstopmode -halt-on-error report.tex >/dev/null && echo report/report.pdf"

clean:                      ## remove builds and scratch files (keeps downloads, data, results)
	rm -rf build scratch

distclean: clean
	rm -rf downloads data
