#!/usr/bin/env python3

__doc__ = """Check if files are formatted using swift format."""

import argparse
import shlex
import shutil
import subprocess
import sys


def main(argv=None):
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('filenames', nargs='*', help='Filenames to check.')
  args = parser.parse_args(argv)
  files = args.filenames
  if not files:
    print('No files to check.')
    return 0

  swift_path = shutil.which('swift')
  if not swift_path:
    raise RuntimeError('swift not found in PATH.')

  cmd = [swift_path, 'format', '--in-place'] + files
  print(f'Running: {shlex.join(cmd)}')
  subprocess.run(cmd, check=True)
  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
