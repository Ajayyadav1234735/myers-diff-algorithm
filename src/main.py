
import sys


# Read the file in binary mode.
# Binary mode is required because the assignment compares exact bytes.
def read_lines(path):
    with open(path, "rb") as f:
        data = f.read()

    # Split the file into lines using the newline byte.
    lines = data.split(b"\n")

    # If the file ends with a newline, split() creates an extra empty line.
    # Remove that extra empty line.
    if lines and lines[-1] == b"":
        lines.pop()

    return lines


# Add a matching range to the result.
#
# i      = starting index in sequence A
# j      = starting index in sequence B
# length = number of matching elements
def _append(res, i, j, length):

    # If a previous range exists, check whether
    # the new range is directly connected to it.
    if res:
        pi, pj, pl = res[-1]

        # Merge contiguous matching ranges.
        if pi + pl == i and pj + pl == j:
            res[-1] = (pi, pj, pl + length)
            return

    # Otherwise, add a new matching range.
    res.append((i, j, length))


def _solve(a, b, out):
    """
    Linear-space Myers algorithm using divide and conquer.

    It finds matching ranges between two sequences.

    Each matching range is stored as:
        (i, j, length)

    Meaning:
        a[i:i+length] == b[j:j+length]
    """

    n = len(a)
    m = len(b)

    # Offset converts negative diagonal indexes
    # into valid array indexes.
    off = n + m + 2

    # Array used for the forward Myers search.
    vf = [0] * (2 * off + 3)

    # Array used for the backward Myers search.
    vb = [0] * (2 * off + 3)


    def middle(alo, ahi, blo, bhi):
        """
        Find the middle snake of the current subproblem.

        Myers performs both forward and backward searches.
        When they meet, the middle snake is found.
        """

        # Length of the current part of sequence A.
        N = ahi - alo

        # Length of the current part of sequence B.
        M = bhi - blo

        # Difference between the sequence lengths.
        delta = N - M

        # Check whether delta is odd.
        odd = delta & 1

        # Maximum edit distance needed to find the middle.
        maxd = (N + M + 1) // 2

        # Initialize the forward search.
        vf[off + 1] = 0

        # Initialize the backward search.
        vb[off + 1] = 0

        # d represents the current edit distance.
        for d in range(maxd + 1):

            # -----------------------------
            # FORWARD SEARCH
            # -----------------------------

            # k represents a diagonal in the edit graph.
            for k in range(-d, d + 1, 2):

                # Choose the best previous diagonal.
                if k == -d or (
                    k != d
                    and vf[off + k - 1] < vf[off + k + 1]
                ):
                    x = vf[off + k + 1]

                else:
                    # Move through a deletion.
                    x = vf[off + k - 1] + 1

                # Calculate y from the diagonal.
                y = x - k

                # Save the starting position of the snake.
                xs = x
                ys = y

                # Continue while elements are equal.
                while (
                    x < N
                    and y < M
                    and a[alo + x] == b[blo + y]
                ):
                    x += 1
                    y += 1

                # Store the furthest x reached on this diagonal.
                vf[off + k] = x

                # Check whether forward and backward searches meet.
                if (
                    odd
                    and delta - d + 1 <= k <= delta + d - 1
                ):
                    if x + vb[off + delta - k] >= N:

                        # Return the middle snake coordinates.
                        return (
                            alo + xs,
                            blo + ys,
                            alo + x,
                            blo + y
                        )


            # -----------------------------
            # BACKWARD SEARCH
            # -----------------------------

            for k in range(-d, d + 1, 2):

                # Choose the best previous diagonal.
                if k == -d or (
                    k != d
                    and vb[off + k - 1] < vb[off + k + 1]
                ):
                    x = vb[off + k + 1]

                else:
                    # Move through a deletion.
                    x = vb[off + k - 1] + 1

                # Calculate y from the diagonal.
                y = x - k

                # Save the starting position.
                xs = x
                ys = y

                # Continue backward while elements are equal.
                while (
                    x < N
                    and y < M
                    and a[alo + N - 1 - x]
                    == b[blo + M - 1 - y]
                ):
                    x += 1
                    y += 1

                # Store the furthest position reached.
                vb[off + k] = x

                # Check whether forward and backward searches meet.
                if not odd and -d <= delta - k <= d:

                    if x + vf[off + delta - k] >= N:

                        # Return the middle snake coordinates.
                        return (
                            alo + N - x,
                            blo + M - y,
                            alo + N - xs,
                            blo + M - ys
                        )

        # The middle snake should normally always be found.
        raise RuntimeError("middle snake not found")


    def rec(alo, ahi, blo, bhi):
        """
        Recursively solve the current subproblem.

        The problem is divided around the middle snake.
        """

        # Starting positions.
        s = alo
        t = blo

        # Find the common prefix.
        while (
            s < ahi
            and t < bhi
            and a[s] == b[t]
        ):
            s += 1
            t += 1

        # Store the common prefix.
        if s > alo:
            out.append((alo, blo, s - alo))


        # Start from the end of the current subproblem.
        ea = ahi
        eb = bhi

        # Find the common suffix.
        while (
            ea > s
            and eb > t
            and a[ea - 1] == b[eb - 1]
        ):
            ea -= 1
            eb -= 1

        # If a different middle section exists,
        # divide the problem using the middle snake.
        if s < ea and t < eb:

            # Find the middle snake.
            x1, y1, x2, y2 = middle(
                s, ea, t, eb
            )

            # Solve the left part recursively.
            rec(s, x1, t, y1)

            # Add the middle snake if it is not empty.
            if x2 > x1:
                out.append(
                    (x1, y1, x2 - x1)
                )

            # Solve the right part recursively.
            rec(x2, ea, y2, eb)

        # Add the common suffix.
        if ea < ahi:
            out.append(
                (ea, eb, ahi - ea)
            )


    # Start the recursive Myers algorithm.
    rec(0, n, 0, m)


def match_ranges(a, b):
    """
    Find matching ranges between two sequences.

    Each range has the form:
        (i, j, length)

    The result represents a minimum edit diff.
    """

    n = len(a)
    m = len(b)

    # Store all matching ranges.
    res = []


    # -----------------------------
    # FIND COMMON PREFIX
    # -----------------------------

    lo = 0

    # Move forward while both sequences are equal.
    while (
        lo < n
        and lo < m
        and a[lo] == b[lo]
    ):
        lo += 1

    # Store the common prefix.
    if lo:
        res.append((0, 0, lo))


    # -----------------------------
    # FIND COMMON SUFFIX
    # -----------------------------

    ha = n
    hb = m

    # Move backward while both sequences are equal.
    while (
        ha > lo
        and hb > lo
        and a[ha - 1] == b[hb - 1]
    ):
        ha -= 1
        hb -= 1


    # Process the middle section where differences may exist.
    if ha > lo and hb > lo:

        # Find values that appear in both middle sections.
        common = set(a[lo:ha]) & set(b[lo:hb])

        # Store indexes of common elements in A.
        ia = [
            i
            for i in range(lo, ha)
            if a[i] in common
        ]

        # Store indexes of common elements in B.
        ib = [
            j
            for j in range(lo, hb)
            if b[j] in common
        ]

        # Continue only if common elements exist.
        if ia and ib:

            # Assign a unique integer ID to each value.
            ids = {}

            # Convert values from A into integer IDs.
            fa = [
                ids.setdefault(a[i], len(ids))
                for i in ia
            ]

            # Convert values from B using the same IDs.
            fb = [
                ids[b[j]]
                for j in ib
            ]

            # Store matching ranges found by Myers.
            fr = []

            # Run the Myers algorithm.
            _solve(fa, fb, fr)

            # Convert the compressed ranges
            # back into original sequence indexes.
            for fi, fj, l in fr:

                for t in range(l):

                    _append(
                        res,
                        ia[fi + t],
                        ib[fj + t],
                        1
                    )


    # Add the common suffix.
    if ha < n:
        _append(
            res,
            ha,
            hb,
            n - ha
        )

    return res


def char_ranges(old, new):
    """
    Find minimum changed character ranges
    between two lines.

    Character positions are Unicode code-point positions.
    """

    # Convert each character to its Unicode code point.
    a = [ord(c) for c in old]
    b = [ord(c) for c in new]

    # Find matching character ranges.
    matches = match_ranges(a, b)


    def gaps(total, idx):
        """
        Find the ranges that are not part of matching ranges.

        These ranges represent changed characters.
        """

        ranges = []

        # Current position.
        pos = 0

        # Process every matching range.
        for r in matches:

            # idx = 0 means old sequence.
            # idx = 1 means new sequence.
            start = r[idx]

            # Characters before the matching range are changed.
            if start > pos:
                ranges.append(
                    (pos, start)
                )

            # Move to the end of the matching range.
            pos = start + r[2]

        # Remaining characters are changed.
        if pos < total:
            ranges.append(
                (pos, total)
            )

        return ranges


    # Return changed ranges for old and new strings.
    return (
        gaps(len(a), 0),
        gaps(len(b), 1)
    )


def fmt(ranges):
    """
    Convert character ranges into the required format.

    Example:
        [(2, 4), (6, 8)]

    becomes:
        2-4,6-8

    If there are no changed characters:
        .
    """

    if not ranges:
        return "."

    return ",".join(
        "%d-%d" % r
        for r in ranges
    )


def blocks(a, b, matches):
    """
    Divide the diff into:

    1. keep  - unchanged lines
    2. change - deleted and/or inserted lines
    """

    # Current position in sequence A.
    pa = 0

    # Current position in sequence B.
    pb = 0

    # Process every matching range.
    for i, j, l in matches:

        # Anything before the matching range is a change block.
        if i > pa or j > pb:
            yield (
                "change",
                pa,
                i,
                pb,
                j
            )

        # Matching range is a keep block.
        yield (
            "keep",
            i,
            j,
            l
        )

        # Move past the matching range.
        pa = i + l
        pb = j + l


    # Process any remaining lines.
    if pa < len(a) or pb < len(b):
        yield (
            "change",
            pa,
            len(a),
            pb,
            len(b)
        )


def run(command, a, b):
    """
    Generate the final diff output.

    command can be:
        lines
        highlight
    """

    # Find minimum matching ranges.
    matches = match_ranges(a, b)

    # Store output chunks.
    out = []

    # Process every block.
    for blk in blocks(a, b, matches):

        # -----------------------------
        # KEEP BLOCK
        # -----------------------------

        if blk[0] == "keep":

            _, i, j, l = blk

            # Add unchanged lines with a leading space.
            for line in a[i:i + l]:
                out.append(
                    b" " + line + b"\n"
                )


        # -----------------------------
        # CHANGE BLOCK
        # -----------------------------

        else:

            _, ai, ae, bj, be = blk

            # Deleted lines must appear before inserted lines.
            for line in a[ai:ae]:
                out.append(
                    b"-" + line + b"\n"
                )

            # Number of delete/insert pairs.
            pairs = min(
                ae - ai,
                be - bj
            )

            # Process inserted lines.
            for p in range(be - bj):

                # Current inserted line.
                nl = b[bj + p]

                # Add the inserted line.
                out.append(
                    b"+" + nl + b"\n"
                )

                # In highlight mode, paired inserted lines
                # get a '?' line immediately after them.
                if command == "highlight" and p < pairs:

                    # Corresponding deleted line.
                    ol = a[ai + p]

                    # Decode both lines as UTF-8.
                    orng, nrng = char_ranges(
                        ol.decode("utf-8"),
                        nl.decode("utf-8")
                    )

                    # Add character-level highlight information.
                    out.append(
                        (
                            "? %s | %s\n"
                            % (
                                fmt(orng),
                                fmt(nrng)
                            )
                        ).encode("utf-8")
                    )

    # Combine all output chunks.
    return b"".join(out)


def main():

    # The program must be called as:
    #
    # main.py lines A B
    # or
    # main.py highlight A B
    #
    if (
        len(sys.argv) != 4
        or sys.argv[1] not in ("lines", "highlight")
    ):
        print(
            "usage: main.py lines|highlight A_PATH B_PATH",
            file=sys.stderr
        )
        return 2


    # Read both input files.
    try:
        a = read_lines(sys.argv[2])
        b = read_lines(sys.argv[3])

    # If a file cannot be read,
    # print the error to stderr and return exit code 2.
    except OSError as exc:
        print(
            str(exc),
            file=sys.stderr
        )
        return 2


    # Generate the diff and write it to stdout.
    sys.stdout.buffer.write(
        run(
            sys.argv[1],
            a,
            b
        )
    )

    return 0


# Start the program here.
if __name__ == "__main__":

    # Increase recursion limit for the recursive Myers algorithm.
    sys.setrecursionlimit(10000)

    # Execute main() and use its result as the exit code.
    raise SystemExit(main())
