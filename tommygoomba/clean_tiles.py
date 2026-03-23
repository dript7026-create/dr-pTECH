#!/usr/bin/env python3
"""
clean_tiles.py

Make an existing generated C tiles file more readable by compressing long
runs of repeated 0x00 byte literals into a short sample plus a comment.

Usage: python clean_tiles.py tiles.c > tiles.cleaned.c
"""
import sys
import re


def compress_hex_runs(lines, min_run=32, sample_keep=16):
    # pattern matches 0xNN (case-insensitive)
    hex_pat = re.compile(r'0x[0-9A-Fa-f]{2}')
    out_lines = []
    for line in lines:
        parts = hex_pat.split(line)
        tokens = hex_pat.findall(line)
        if not tokens:
            out_lines.append(line)
            continue
        # rebuild while compressing runs
        new_line = ''
        i = 0
        for part, tok in zip(parts, tokens + ['']):
            new_line += part
            if not tok:
                continue
            # check for run starting at this token
            run_len = 1
            j = i + 1
            while j < len(tokens) and tokens[j].lower() == '0x00':
                run_len += 1
                j += 1
            if run_len >= min_run and tok.lower() == '0x00':
                # keep a small sample then insert comment
                keep = min(sample_keep, run_len)
                new_line += ','.join(['0x00'] * keep)
                new_line += ', /* {} zeros omitted */'.format(run_len - keep)
                i = j
                # skip the parts corresponding to the consumed tokens
                # advance parts iterator accordingly
                # find how many parts to skip
            else:
                new_line += tok
                i += 1
        out_lines.append(new_line)
    return out_lines


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='input tiles.c')
    parser.add_argument('--output', '-o', help='output cleaned file (optional)')
    args = parser.parse_args()

    path = args.input
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    cleaned = compress_hex_runs(lines)
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as out:
            out.writelines(cleaned)
    else:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stdout.writelines(cleaned)


if __name__ == '__main__':
    main()
