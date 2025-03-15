#!/usr/bin/env python3

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

# third_party
import requests

CHUNK_SIZE = 8192
SCRIPT_DIR = Path(__file__).resolve().parent
KTFMT = SCRIPT_DIR / 'bin' / 'ktfmt.jar'

KTFMT_VERSION = '0.54'
KTFMT_SHA256 = "5e7eb28a0b2006d1cefbc9213bfc73a8191ec2f85d639ec4fc4ec0cd04212e82"
KTFMT_URL = f"https://github.com/facebook/ktfmt/releases/download/v{KTFMT_VERSION}/ktfmt-{KTFMT_VERSION}-jar-with-dependencies.jar"


def java_path():
  if os.environ.get('JAVA_HOME'):
    return (Path(os.environ['JAVA_HOME']) / 'bin' / 'java').resolve()
  java = shutil.which('java')
  if not java:
    raise RuntimeError("java not found")

  return Path(java).resolve()


def ensure_ktfmt():
  if KTFMT.exists():
    maybe_right = True
    with open(KTFMT, "rb") as f:
      hasher = hashlib.sha256()
      while True:
        data = f.read(CHUNK_SIZE)
        if not data:
          break
        hasher.update(data)
      if hasher.hexdigest() != KTFMT_SHA256:
        maybe_right = False

    if not maybe_right:
      KTFMT.unlink()

    if maybe_right:
      return

  # Download ktfmt
  r = requests.get(KTFMT_URL, stream=True)
  temp_file = None
  try:
    r.raise_for_status()
    temp_file = KTFMT.with_suffix('.tmp')

    hasher = hashlib.sha256()
    with open(temp_file, 'wb') as f:
      while True:
        data = r.raw.read(CHUNK_SIZE)
        if not data:
          break
        hasher.update(data)
        f.write(data)

    if hasher.hexdigest() != KTFMT_SHA256:
      raise Exception("Checksum mismatch")

    temp_file.rename(KTFMT)
  finally:
    if temp_file:
      temp_file.unlink(missing_ok=True)
    r.close()


def main(argv):
  files = argv
  if not files:
    return 0

  files = [os.path.abspath(f) for f in files]
  ensure_ktfmt()

  java = java_path()
  args = [str(java), '-jar', str(KTFMT)] + files
  subprocess.run(args, check=True)
  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
