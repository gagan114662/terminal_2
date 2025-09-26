.PHONY: test

test:
	@/bin/sh -c 'python3 <<'\''PY'\'' \
print("Hello from Python") \
print("Line 2") \
PY'
	@echo "After Python"
