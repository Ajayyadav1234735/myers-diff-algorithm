import sys


def read_lines(path):
    with open(path, "rb") as f:
        data = f.read()

    lines = data.split(b"\n")

    # If file ends with newline, don't create an extra empty line.
    if lines and lines[-1] == b"":
        lines.pop()

    return lines


def myers_diff(a, b):
    """
    Myers shortest edit script.

    Returns:
        (" ", value) -> keep
        ("-", value) -> delete
        ("+", value) -> insert
    """

    n = len(a)
    m = len(b)

    if n == 0:
        return [("+", x) for x in b]

    if m == 0:
        return [("-", x) for x in a]

    # V[k] = furthest x reached on diagonal k.
    v = {1: 0}
    trace = []

    final_d = 0

    for d in range(n + m + 1):

        found = False

        for k in range(-d, d + 1, 2):

            if k == -d:
                x = v.get(k + 1, 0)

            elif k == d:
                x = v.get(k - 1, 0) + 1

            elif v.get(k - 1, -10**18) < v.get(k + 1, -10**18):
                x = v.get(k + 1, 0)

            else:
                x = v.get(k - 1, 0) + 1

            y = x - k

            # Follow the diagonal while elements are equal.
            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1

            v[k] = x

            if x >= n and y >= m:
                found = True
                final_d = d
                break

        # Save V after this d.
        trace.append(v.copy())

        if found:
            break

    # Backtrack.
    x = n
    y = m
    result = []

    for d in range(final_d, 0, -1):

        previous_v = trace[d - 1]

        k = x - y

        if (
            k == -d
            or (
                k != d
                and previous_v.get(k - 1, -10**18)
                < previous_v.get(k + 1, -10**18)
            )
        ):
            previous_k = k + 1
        else:
            previous_k = k - 1

        previous_x = previous_v[previous_k]
        previous_y = previous_x - previous_k

        # Matching diagonal = keep.
        while x > previous_x and y > previous_y:
            result.append((" ", a[x - 1]))
            x -= 1
            y -= 1

        # We arrived here either through insertion or deletion.
        if x == previous_x:
            result.append(("+", b[y - 1]))
            y -= 1
        else:
            result.append(("-", a[x - 1]))
            x -= 1

    # Remaining prefix.
    while x > 0 and y > 0:
        result.append((" ", a[x - 1]))
        x -= 1
        y -= 1

    while x > 0:
        result.append(("-", a[x - 1]))
        x -= 1

    while y > 0:
        result.append(("+", b[y - 1]))
        y -= 1

    result.reverse()

    return normalize_change_blocks(result)


def normalize_change_blocks(diff):
    """
    For every consecutive change block, put all deletions
    before all insertions.
    """

    result = []
    i = 0

    while i < len(diff):

        if diff[i][0] == " ":
            result.append(diff[i])
            i += 1
            continue

        deletes = []
        inserts = []

        while i < len(diff) and diff[i][0] != " ":
            op, value = diff[i]

            if op == "-":
                deletes.append(value)
            elif op == "+":
                inserts.append(value)

            i += 1

        for value in deletes:
            result.append(("-", value))

        for value in inserts:
            result.append(("+", value))

    return result


def format_ranges(ranges_old, ranges_new):
    def format_one(ranges):
        if not ranges:
            return "."

        return ",".join(
            f"{start}-{end}"
            for start, end in ranges
        )

    return f"{format_one(ranges_old)} | {format_one(ranges_new)}"


def character_ranges(old_text, new_text):
    """
    Find the minimum changed character ranges.

    Character positions are Python Unicode code-point positions.
    """

    diff = myers_diff(list(old_text), list(new_text))

    old_ranges = []
    new_ranges = []

    old_pos = 0
    new_pos = 0

    old_start = None
    old_end = None

    new_start = None
    new_end = None

    def close_old():
        nonlocal old_start, old_end

        if old_start is not None:
            old_ranges.append((old_start, old_end))
            old_start = None
            old_end = None

    def close_new():
        nonlocal new_start, new_end

        if new_start is not None:
            new_ranges.append((new_start, new_end))
            new_start = None
            new_end = None

    for op, char in diff:

        if op == " ":
            close_old()
            close_new()

            old_pos += 1
            new_pos += 1

        elif op == "-":

            if old_start is None:
                old_start = old_pos

            old_end = old_pos + 1
            old_pos += 1

        elif op == "+":

            if new_start is None:
                new_start = new_pos

            new_end = new_pos + 1
            new_pos += 1

    close_old()
    close_new()

    return old_ranges, new_ranges


def make_lines_output(diff):
    """
    Part A output.
    """

    output = []

    for op, line in diff:
        output.append(op.encode("ascii") + line + b"\n")

    return b"".join(output)


def make_highlight_output(diff):
    """
    Part B output.

    For every change block:
      - print all '-' lines first
      - then '+' lines
      - after each paired '+' line print its '?' line

    Pairing is:
      first '-' with first '+'
      second '-' with second '+'
      etc.
    """

    output = []

    i = 0

    while i < len(diff):

        # Keep line.
        if diff[i][0] == " ":
            output.append((" ", diff[i][1]))
            i += 1
            continue

        # Collect one complete change block.
        deletes = []
        inserts = []

        while i < len(diff) and diff[i][0] != " ":

            op, line = diff[i]

            if op == "-":
                deletes.append(line)

            elif op == "+":
                inserts.append(line)

            i += 1

        # All deletes must come first.
        for line in deletes:
            output.append(("-", line))

        pair_count = min(len(deletes), len(inserts))

        # Insert lines.
        for j, new_line in enumerate(inserts):

            output.append(("+", new_line))

            # Only paired '+' lines receive '?'.
            if j < pair_count:

                old_line = deletes[j]

                # Part B test data is UTF-8 text.
                old_text = old_line.decode("utf-8")
                new_text = new_line.decode("utf-8")

                old_ranges, new_ranges = character_ranges(
                    old_text,
                    new_text
                )

                highlight = format_ranges(
                    old_ranges,
                    new_ranges
                )

                # IMPORTANT: '?' must be followed by one space.
                output.append(
                    ("?", b" " + highlight.encode("utf-8"))
                )

    return output


def main():
    if len(sys.argv) != 4:
        print(
            "usage: main.py lines|highlight A_PATH B_PATH",
            file=sys.stderr
        )
        return 2

    command = sys.argv[1]

    if command not in ("lines", "highlight"):
        print(
            "usage: main.py lines|highlight A_PATH B_PATH",
            file=sys.stderr
        )
        return 2

    a_path = sys.argv[2]
    b_path = sys.argv[3]

    try:
        a = read_lines(a_path)
        b = read_lines(b_path)

    except (OSError, IOError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    diff = myers_diff(a, b)

    if command == "lines":
        data = make_lines_output(diff)

    else:
        highlighted = make_highlight_output(diff)

        chunks = []

        for op, line in highlighted:
            chunks.append(
                op.encode("ascii") + line + b"\n"
            )

        data = b"".join(chunks)

    sys.stdout.buffer.write(data)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())