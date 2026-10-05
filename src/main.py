import sys


def read_lines(path):
    with open(path, "rb") as f:
        data = f.read()
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    return lines


def _append(res, i, j, length):
    """Append a match range, merging with the previous one if contiguous."""
    if res:
        pi, pj, pl = res[-1]
        if pi + pl == i and pj + pl == j:
            res[-1] = (pi, pj, pl + length)
            return
    res.append((i, j, length))


def _solve(a, b, out):
    """
    Linear-space Myers (middle snake, divide and conquer) on int lists.
    Appends matching ranges (i, j, length) to out, in order.
    """
    n = len(a)
    m = len(b)
    off = n + m + 2
    vf = [0] * (2 * off + 3)
    vb = [0] * (2 * off + 3)

    def middle(alo, ahi, blo, bhi):
        N = ahi - alo
        M = bhi - blo
        delta = N - M
        odd = delta & 1
        maxd = (N + M + 1) // 2
        vf[off + 1] = 0
        vb[off + 1] = 0
        for d in range(maxd + 1):
            # forward
            for k in range(-d, d + 1, 2):
                if k == -d or (k != d and vf[off + k - 1] < vf[off + k + 1]):
                    x = vf[off + k + 1]
                else:
                    x = vf[off + k - 1] + 1
                y = x - k
                xs = x
                ys = y
                while x < N and y < M and a[alo + x] == b[blo + y]:
                    x += 1
                    y += 1
                vf[off + k] = x
                if odd and delta - d + 1 <= k <= delta + d - 1:
                    if x + vb[off + delta - k] >= N:
                        return alo + xs, blo + ys, alo + x, blo + y
            # backward (on reversed sequences)
            for k in range(-d, d + 1, 2):
                if k == -d or (k != d and vb[off + k - 1] < vb[off + k + 1]):
                    x = vb[off + k + 1]
                else:
                    x = vb[off + k - 1] + 1
                y = x - k
                xs = x
                ys = y
                while (x < N and y < M
                       and a[alo + N - 1 - x] == b[blo + M - 1 - y]):
                    x += 1
                    y += 1
                vb[off + k] = x
                if not odd and -d <= delta - k <= d:
                    if x + vf[off + delta - k] >= N:
                        return (alo + N - x, blo + M - y,
                                alo + N - xs, blo + M - ys)
        raise RuntimeError("middle snake not found")

    def rec(alo, ahi, blo, bhi):
        s = alo
        t = blo
        while s < ahi and t < bhi and a[s] == b[t]:
            s += 1
            t += 1
        if s > alo:
            out.append((alo, blo, s - alo))
        ea = ahi
        eb = bhi
        while ea > s and eb > t and a[ea - 1] == b[eb - 1]:
            ea -= 1
            eb -= 1
        if s < ea and t < eb:
            x1, y1, x2, y2 = middle(s, ea, t, eb)
            rec(s, x1, t, y1)
            if x2 > x1:
                out.append((x1, y1, x2 - x1))
            rec(x2, ea, y2, eb)
        if ea < ahi:
            out.append((ea, eb, ahi - ea))

    rec(0, n, 0, m)


def match_ranges(a, b):
    """
    Minimal diff of two sequences of hashables.
    Returns ordered list of matching ranges (i, j, length).
    """
    n = len(a)
    m = len(b)
    res = []

    lo = 0
    while lo < n and lo < m and a[lo] == b[lo]:
        lo += 1
    if lo:
        res.append((0, 0, lo))

    ha = n
    hb = m
    while ha > lo and hb > lo and a[ha - 1] == b[hb - 1]:
        ha -= 1
        hb -= 1

    if ha > lo and hb > lo:
        # Lines present on only one side must be deleted/inserted anyway.
        common = set(a[lo:ha]) & set(b[lo:hb])
        ia = [i for i in range(lo, ha) if a[i] in common]
        ib = [j for j in range(lo, hb) if b[j] in common]
        if ia and ib:
            ids = {}
            fa = [ids.setdefault(a[i], len(ids)) for i in ia]
            fb = [ids[b[j]] for j in ib]
            fr = []
            _solve(fa, fb, fr)
            for fi, fj, l in fr:
                for t in range(l):
                    _append(res, ia[fi + t], ib[fj + t], 1)

    if ha < n:
        _append(res, ha, hb, n - ha)
    return res


def char_ranges(old, new):
    """Changed character ranges (code points) for one line pair."""
    a = [ord(c) for c in old]
    b = [ord(c) for c in new]
    matches = match_ranges(a, b)

    def gaps(total, idx):
        ranges = []
        pos = 0
        for r in matches:
            start = r[idx]
            if start > pos:
                ranges.append((pos, start))
            pos = start + r[2]
        if pos < total:
            ranges.append((pos, total))
        return ranges

    return gaps(len(a), 0), gaps(len(b), 1)


def fmt(ranges):
    if not ranges:
        return "."
    return ",".join("%d-%d" % r for r in ranges)


def blocks(a, b, matches):
    """Yield ('keep', i, j, len) or ('change', ai, ae, bj, be)."""
    pa = 0
    pb = 0
    for i, j, l in matches:
        if i > pa or j > pb:
            yield ("change", pa, i, pb, j)
        yield ("keep", i, j, l)
        pa = i + l
        pb = j + l
    if pa < len(a) or pb < len(b):
        yield ("change", pa, len(a), pb, len(b))


def run(command, a, b):
    matches = match_ranges(a, b)
    out = []
    for blk in blocks(a, b, matches):
        if blk[0] == "keep":
            _, i, j, l = blk
            for line in a[i:i + l]:
                out.append(b" " + line + b"\n")
        else:
            _, ai, ae, bj, be = blk
            for line in a[ai:ae]:
                out.append(b"-" + line + b"\n")
            pairs = min(ae - ai, be - bj)
            for p in range(be - bj):
                nl = b[bj + p]
                out.append(b"+" + nl + b"\n")
                if command == "highlight" and p < pairs:
                    ol = a[ai + p]
                    orng, nrng = char_ranges(ol.decode("utf-8"),
                                             nl.decode("utf-8"))
                    out.append(("? %s | %s\n" % (fmt(orng), fmt(nrng)))
                               .encode("utf-8"))
    return b"".join(out)


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in ("lines", "highlight"):
        print("usage: main.py lines|highlight A_PATH B_PATH", file=sys.stderr)
        return 2
    try:
        a = read_lines(sys.argv[2])
        b = read_lines(sys.argv[3])
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    sys.stdout.buffer.write(run(sys.argv[1], a, b))
    return 0


if __name__ == "__main__":
    sys.setrecursionlimit(10000)
    raise SystemExit(main())