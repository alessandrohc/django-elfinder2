import re


def get_kilobyte(value):
	return int(value) * 1024


def get_bytes(val: str | int) -> int:
	"""Returns val converted to bytes."""
	val = str(val)
	# Remove "b", "B", and whitespace from string
	val = val.strip("bB \t\n\r\0\x0B")

	# Get the last character
	last = val[-1].lower()

	# Convert base value to integer
	val = re.sub(r'\D', '', val)
	val = int(val) if val else 0

	# Convert according to suffix
	if last == 'k':
		val = get_kilobyte(val)
	elif last == 'm':
		val = get_kilobyte(val) * 1024
	elif last == 'g':
		val = get_kilobyte(val) * 1024 ** 2
	elif last == 't':
		val = get_kilobyte(val) * 1024 ** 3
	elif last == 'p':
		val = get_kilobyte(val) * 1024 ** 4
	elif last == 'e':
		val = get_kilobyte(val) * 1024 ** 5
	elif last == 'z':
		val = get_kilobyte(val) * 1024 ** 6
	elif last == 'y':
		val = get_kilobyte(val) * 1024 ** 7
	return val
