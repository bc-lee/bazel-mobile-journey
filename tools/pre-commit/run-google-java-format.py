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
GOOGLE_JAVA_FORMAT = SCRIPT_DIR / 'bin' / 'google-java-format.jar'

GOOGLE_JAVA_FORMAT_VERSION = '1.25.2'
GOOGLE_JAVA_FORMAT_SHA256 = "25157797a0a972c2290b5bc71530c4f7ad646458025e3484412a6e5a9b8c9aa6"
GOOGLE_JAVA_FORMAT_URL = f"https://github.com/google/google-java-format/releases/download/v{GOOGLE_JAVA_FORMAT_VERSION}/google-java-format-{GOOGLE_JAVA_FORMAT_VERSION}-all-deps.jar"


def java_path():
  if os.environ.get('JAVA_HOME'):
    return (Path(os.environ['JAVA_HOME']) / 'bin' / 'java').resolve()
  java = shutil.which('java')
  if not java:
    raise RuntimeError("java not found")

  return Path(java).resolve()


def ensure_google_java_format():
  if GOOGLE_JAVA_FORMAT.exists():
    maybe_right = True
    with open(GOOGLE_JAVA_FORMAT, "rb") as f:
      hasher = hashlib.sha256()
      while True:
        data = f.read(CHUNK_SIZE)
        if not data:
          break
        hasher.update(data)
      if hasher.hexdigest() != GOOGLE_JAVA_FORMAT_SHA256:
        maybe_right = False

    if not maybe_right:
      GOOGLE_JAVA_FORMAT.unlink()

    if maybe_right:
      return

  # Download google-java-format
  r = requests.get(GOOGLE_JAVA_FORMAT_URL, stream=True)
  temp_file = None
  try:
    r.raise_for_status()
    temp_file = GOOGLE_JAVA_FORMAT.with_suffix('.tmp')

    hasher = hashlib.sha256()
    with open(temp_file, 'wb') as f:
      while True:
        data = r.raw.read(CHUNK_SIZE)
        if not data:
          break

        f.write(data)
        hasher.update(data)

    if hasher.hexdigest() != GOOGLE_JAVA_FORMAT_SHA256:
      raise Exception(
          f"Downloaded sha256 mismatch: {hasher.hexdigest()} != {GOOGLE_JAVA_FORMAT_SHA256}"
      )

    shutil.move(temp_file, GOOGLE_JAVA_FORMAT)

  finally:
    if temp_file is not None:
      temp_file.unlink(missing_ok=True)
    r.close()


def main(argv):
  files = argv
  if not files:
    return 0

  files = [os.path.abspath(f) for f in files]
  ensure_google_java_format()

  java = java_path()
  args = [str(java), '-jar', str(GOOGLE_JAVA_FORMAT), '-i'] + files
  subprocess.run(args, check=True)
  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
