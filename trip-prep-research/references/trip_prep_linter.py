#!/usr/bin/env python3
"""trip_prep_linter.py — validates mobile trip itinerary format.

Checks:
1. Bold name lines are properly closed with **
2. Bold names are followed by indented - bullet sub-items (≥2 bullets)
3. No [Choice A/B/C] labels in venue blocks
4. Direction links use Apple Maps format with &dirflg= parameter
"""

import re
import sys


def lint_itinerary(path: str) -> list[str]:
    with open(path) as f:
        lines = f.readlines()

    errors = []
    i = 0

    # Skip everything before the first "## Day" header (metadata block)
    while i < len(lines) and not re.match(r'^##\s+Day', lines[i]):
        i += 1

    while i < len(lines):
        line = lines[i].rstrip()

        # Skip day/section headers
        if not line or re.match(r'^#{1,3}\s', line):
            i += 1
            continue

        # Bold name: must start with ** and have matching closing **
        if line.startswith('**'):
            rest = line[2:]
            if '**' not in rest:
                errors.append(f"Line {i+1}: Bold marker opened but not closed: {line}")
            else:
                # opening ** ok, check sub-items follow
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1

                # Must be followed by a bullet
                if j < len(lines) and not lines[j].strip().startswith('- '):
                    errors.append(
                        f"Line {i+1}: Bold name not followed by bullet sub-items: {line}"
                    )

                # Count consecutive bullets
                bullet_count = 0
                while j < len(lines) and lines[j].strip().startswith('- '):
                    bullet_count += 1
                    j += 1

                if bullet_count < 2:
                    errors.append(
                        f"Line {i+1}: Venue has only {bullet_count} bullet(s), needs ≥2: {line}"
                    )

                # Check for [Choice A/B/C] anywhere in the block
                block_lines = lines[i:j]
                block_text = '\n'.join(block_lines)
                if re.search(r'\[Choice\s+[A-Z]/[A-Z]', block_text):
                    errors.append(
                        f"Line {i+1}: [Choice A/B/C] label found in venue block: {line}"
                    )

                # Check direction link format
                for bl in block_lines:
                    if '[📍 Directions]' in bl:
                        if 'maps.apple.com' not in bl:
                            errors.append(
                                f"Line {i+1}: Direction link is not Apple Maps format: {bl.strip()}"
                            )
                        if '&dirflg=' not in bl:
                            errors.append(
                                f"Line {i+1}: Direction link missing &dirflg= parameter: {bl.strip()}"
                            )

                i = j
                continue

        i += 1

    return errors


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'itinerary.md'
    errs = lint_itinerary(path)
    if errs:
        print(f"FORMAT ERRORS ({len(errs)}):")
        for e in errs:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("OK — format valid")
