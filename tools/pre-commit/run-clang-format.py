#!/usr/bin/env python3

import hashlib
import os
import platform
import subprocess
import sys
from pathlib import Path

# third_party
import requests

CHUNK_SIZE = 8192
SCRIPT_DIR = Path(__file__).resolve().parent
CLANG_FORMAT = SCRIPT_DIR / 'bin' / 'clang-format'

# Copied from https://chromium.googlesource.com/chromium/src/buildtools/+/fa96185dc5d13c6666b4850d03cddc06be4e4f35/DEPS
# fmt: off
CLANG_FORMAT_DATA = [
  {
    "os": "linux",
    "arch": "x86_64",
    "bucket": "chromium-clang-format",
    "object_name": "79a7b4e5336339c17b828de10d80611ff0f85961",
    "sha256": "889266a51681d55bd4b9e02c9a104fa6ee22ecdfa7e8253532e5ea47e2e4cb4a",
    "size": 3899440,
  },
  {
    "os": "mac",
    "arch": "x86_64",
    "bucket": "chromium-clang-format",
    "object_name": "7d46d237f9664f41ef46b10c1392dcb559250f25",
    "sha256": "0c3c13febeb0495ef0086509c24605ecae9e3d968ff9669d12514b8a55c7824e",
    "size": 3204008,
  }, {
    "os": "mac",
    "arch": "arm64",
    "bucket": "chromium-clang-format",
    "object_name": "8503422f469ae56cc74f0ea2c03f2d872f4a2303",
    "sha256": "dabf93691361e8bd1d07466d67584072ece5c24e2b812c16458b8ff801c33e29",
    "size": 3212560
  }
]
# fmt: on


def ensure_clang_format():
  operation_system, arch = sys.platform, platform.machine()
  if operation_system == "darwin":
    operation_system = "mac"
  matched_data = None
  for data in CLANG_FORMAT_DATA:
    if data["os"] == operation_system and data["arch"] == arch:
      matched_data = data
      break
  if matched_data is None:
    raise Exception(f"Unsupported platform: {operation_system} {arch}")

  bucket = matched_data["bucket"]
  object_name = matched_data["object_name"]
  sha256 = matched_data["sha256"]
  size = matched_data["size"]

  if CLANG_FORMAT.exists():
    maybe_right = True
    stat_info = CLANG_FORMAT.stat()

    if stat_info.st_size != size:
      maybe_right = False

    if maybe_right:
      with open(CLANG_FORMAT, "rb") as f:
        hasher = hashlib.sha256()
        while True:
          data = f.read(CHUNK_SIZE)
          if not data:
            break
          hasher.update(data)
        if hasher.hexdigest() != sha256:
          maybe_right = False

    if not maybe_right:
      CLANG_FORMAT.unlink()

    if maybe_right and not (stat_info.st_mode & 0o100):
      os.chmod(CLANG_FORMAT, 0o755)

    if maybe_right:
      return

  # Download clang-format
  r = requests.get(
      f'https://storage.googleapis.com/{bucket}/{object_name}', stream=True)
  temp_file = None
  try:
    r.raise_for_status()
    temp_file = CLANG_FORMAT.with_suffix('.tmp')

    download_size = 0
    hasher = hashlib.sha256()
    with temp_file.open('wb') as f:
      while True:
        data = r.raw.read(CHUNK_SIZE)
        if not data:
          break

        f.write(data)
        download_size += len(data)
        hasher.update(data)

    if download_size != size:
      raise Exception(f"Downloaded size mismatch: {download_size} != {size}")

    if hasher.hexdigest() != sha256:
      raise Exception(
          f"Downloaded sha256 mismatch: {hasher.hexdigest()} != {sha256}")

    temp_file.rename(CLANG_FORMAT)
    os.chmod(CLANG_FORMAT, 0o755)

  finally:
    if temp_file is not None:
      temp_file.unlink(missing_ok=True)
    r.close()


def main(argv):
  files = argv
  if not files:
    return 0

  files = [os.path.abspath(f) for f in files]
  ensure_clang_format()

  cmd = [str(CLANG_FORMAT), '-i'] + files
  subprocess.run(cmd, check=True)
  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
