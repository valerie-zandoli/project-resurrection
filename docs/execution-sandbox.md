# Execution rules for generated code (DRAFT, needs Anastasiya's agreement)

Drafted 2026-10-22 by Valerie with Claude Code.  The Simulation Developer agent writes code and the harness runs it.  An "isolated run directory" is not a sandbox, and LaNice's Access Control lesson names code execution as the largest risk ("can call" is not "should be allowed").  These rules are enforced by code, not by a prompt.

## Rules for any code the Simulation Developer generates

1. Run it as a separate process (`subprocess.run([python, "-I", script, config])`) with a fixed working directory `runs/<run_id>/round_<n>/`.  Nothing runs inside the harness process.
2. Pass a scrubbed environment:  `PATH` and `PYTHONHASHSEED` only.  No API key, token, or home directory reaches the process.
3. Copy the two research CSVs into the run directory read-only (mode 444) and record their content hashes (pull request 9).
4. Kill the process at a time limit (start at 300 seconds) and cap output size (start at 10 MB).  A killed run returns `stop` with the reason; it never retries silently.
5. Set CPU-time and memory limits in the child with `resource.setrlimit`.
6. Compare the file tree before and after the run.  A file written outside the run directory fails the round.
7. Tripwire only, not a defense:  scan the script with `ast` and flag imports of `socket`, `subprocess`, `requests`, `urllib`, and `shutil`, and calls to `os.system`.  A deny list can be evaded, so the code says "tripwire."
8. Real isolation (layer two):  on macOS, `sandbox-exec` with a profile that denies the network and writes outside the run directory, or a container with the network off.  Until layer two exists, generated code runs only after a person has read it.

## Tests (all five pass before any live run; bars written first)

1. Code that prints its environment shows no key.
2. Code that opens a socket fails.
3. An infinite loop is killed at the limit and the round reports `stop`.
4. Code that writes outside the run directory fails the round.
5. Oversize output is cut and flagged.

## Stated limit

Rules 1 to 7 reduce accidents and sloppy code.  Only layer two contains hostile code.

## Open decisions for Anastasiya (Developer role owner)

- The time, size, and memory limits.
- Whether layer two is `sandbox-exec` or a container on her machine.
