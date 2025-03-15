#!/usr/bin/env python3

import contextlib
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BUILDIFIER = SCRIPT_DIR / 'bin' / 'buildifier'
BUILDIFIER_VERSION_FILE = SCRIPT_DIR / 'bin' / 'buildifier.version'

BUILDIFIER_VERSION = 'ff5a15a14fa3939a985e61cc1afdb734216225e9'
BUILDIFIER_REPO = 'https://github.com/bazelbuild/buildtools.git'


@contextlib.contextmanager
def temporaryWorkingDirectory(path):
  _old_cwd = os.getcwd()
  os.chdir(os.path.abspath(path))

  try:
    yield
  finally:
    os.chdir(_old_cwd)


def ensure_buildifier():
  if BUILDIFIER.exists():
    try:
      with open(BUILDIFIER_VERSION_FILE, 'r') as f:
        if f.read().strip() == BUILDIFIER_VERSION:
          return
    except FileNotFoundError:
      pass

    BUILDIFIER.unlink()
    BUILDIFIER_VERSION_FILE.unlink(missing_ok=True)

  # Download buildifier
  git = shutil.which('git')
  if not git:
    raise RuntimeError("git not found")

  go = shutil.which('go')
  if not go:
    raise RuntimeError("go not found")

  tempdir = Path(tempfile.mkdtemp())
  try:
    with temporaryWorkingDirectory(tempdir):
      r = subprocess.run([git, 'clone', BUILDIFIER_REPO, '.'],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
      if r.returncode != 0:
        raise RuntimeError(
            f"Failed to clone buildifier: {r.stderr.decode('utf-8')}")
      r = subprocess.run([git, 'checkout', BUILDIFIER_VERSION],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
      if r.returncode != 0:
        raise RuntimeError(f"Failed to checkout buildifier: {r.stderr.decode}")
      r = subprocess.run([go, 'build', '-o', BUILDIFIER, './buildifier'],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         check=True)
      if r.returncode != 0:
        raise RuntimeError(
            f"Failed to build buildifier: {r.stderr.decode('utf-8')}")
    with open(BUILDIFIER_VERSION_FILE, 'w') as f:
      f.write(BUILDIFIER_VERSION + '\n')

  finally:
    shutil.rmtree(tempdir, ignore_errors=True)


def main(argv):
  files = argv
  if not files:
    return 0

  files = [os.path.abspath(f) for f in files]
  ensure_buildifier()

  args = [str(BUILDIFIER)] + files
  subprocess.run(args, check=True)
  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
