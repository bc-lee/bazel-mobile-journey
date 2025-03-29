#!/usr/bin/env python3
"""
Copyright 2018 Google Inc. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

__doc__ = """
This script gives the version string that is given in the command line argument.
It uses the same logic as bazelisk to determine the version string.
Useful for CI pipelines. Original code is from https://github.com/bazelbuild/bazelisk/blob/de8fc98a29ecc383f02e3a4339583c305326f619/bazelisk.py
and modified to be used to get the version string.

Usage:
  bazel_version.py <string, such as "latest", "last_rc", "7.4.0", "7.x", "7.*">
"""

import json
import os
import platform
import re
import sys
import time
from contextlib import closing
from urllib.request import urlopen, Request

ONE_HOUR = 60 * 60  # one hour in seconds

RE_Latest_version = re.compile(r"^(\d+)\.x$")
RE_Latest_version_with_candidate = re.compile(r"^(\d+)\.\*$")


# Custom version parsing implementation
class InvalidVersion(Exception):
  """Raised when a version string is invalid."""
  pass


class Version:
  """A parsed semantic version."""

  def __init__(self, version_str):
    self.version_str = version_str
    self.is_prerelease = False

    # Parse the version string
    match = re.match(r'^(\d+)(?:\.(\d+))?(?:\.(\d+))?(.*)$', version_str)
    if not match:
      raise InvalidVersion(f"Invalid version: '{version_str}'")

    # Extract components
    major, minor, micro, suffix = match.groups()

    self.major = int(major)
    self.minor = int(minor or 0)
    self.micro = int(micro or 0)
    self.suffix = suffix or ""

    # Check if this is a prerelease (has rc, alpha, beta, etc.)
    if self.suffix and re.search(r'(rc|alpha|beta|dev|pre)', self.suffix,
                                 re.IGNORECASE):
      self.is_prerelease = True

  def __lt__(self, other):
    """Compare versions."""
    if not isinstance(other, Version):
      return NotImplemented

    # Compare major.minor.micro
    for s, o in zip([self.major, self.minor, self.micro],
                    [other.major, other.minor, other.micro]):
      if s != o:
        return s < o

    # If we get here, the major.minor.micro parts are equal

    # No suffix is greater than any suffix (e.g., 1.0.0 > 1.0.0rc1)
    if not self.suffix and other.suffix:
      return False
    if self.suffix and not other.suffix:
      return True

    # Both have suffixes, compare them lexicographically
    # This is a simplification - in reality we'd want to handle
    # rc1 < rc2 < rc10, etc., but this works for basic cases
    return self.suffix < other.suffix

  def __eq__(self, other):
    """Check if versions are equal."""
    if not isinstance(other, Version):
      return NotImplemented
    return (self.major == other.major and self.minor == other.minor and
            self.micro == other.micro and self.suffix == other.suffix)

  def __repr__(self):
    return f"Version('{self.version_str}')"


def parse_version(version_str):
  """Parse a version string into a Version object."""
  return Version(version_str)


def get_bazelisk_directory():
  operating_system = platform.system().lower()

  if operating_system == "windows":
    base_dir = os.environ.get("LocalAppData")
    if base_dir is None:
      raise Exception("%LocalAppData% is not defined")
  elif operating_system == "darwin":
    base_dir = os.environ.get("HOME")
    if base_dir is None:
      raise Exception("$HOME is not defined")
    base_dir = os.path.join(base_dir, "Library", "Caches")
  elif operating_system == "linux":
    base_dir = os.environ.get("XDG_CACHE_HOME")
    if base_dir is None:
      base_dir = os.environ.get("HOME")
      if base_dir is None:
        raise Exception("neither $XDG_CACHE_HOME nor $HOME are defined")
      base_dir = os.path.join(base_dir, ".cache")
  else:
    raise Exception(
        "Unsupported operating system '{}'".format(operating_system))

  return os.path.join(base_dir, "bazelisk")


def read_remote_text_file(url):
  headers = {}

  # Add GitHub token if available
  github_token = os.environ.get("BAZELISK_GITHUB_TOKEN")
  if github_token and "github.com" in url:
    headers["Authorization"] = f"token {github_token}"

  req = urlopen(Request(url, headers=headers))
  with closing(req) as res:
    body = res.read()
    try:
      return body.decode(res.info().get_content_charset("iso-8859-1"))
    except AttributeError:
      # Python 2.x compatibility hack
      return body.decode(res.info().getparam("charset") or "iso-8859-1")


def get_releases_json(bazelisk_directory):
  """Returns the most recent versions of Bazel, in descending order."""
  releases_path = os.path.join(bazelisk_directory, "releases.json")

  # Use a cached version if it's fresh enough.
  if os.path.exists(releases_path):
    if abs(time.time() - os.path.getmtime(releases_path)) < ONE_HOUR:
      with open(releases_path, "rb") as f:
        try:
          return json.loads(f.read().decode("utf-8"))
        except ValueError:
          print("WARN: Could not parse cached releases.json.")
          try:
            os.remove(releases_path)
          except Exception as e:
            pass

  url = "https://api.github.com/repos/bazelbuild/bazel/releases"
  body = read_remote_text_file(url)
  with open(releases_path, "wb") as f:
    f.write(body.encode("utf-8"))
  return json.loads(body)


def parse_versions(releases):
  """Parse and categorize all versions from releases data."""
  all_versions = []
  rc_versions = []
  stable_versions = []

  for release in releases:
    try:
      # Parse the version and add to our list
      version_str = release["tag_name"]
      parsed_version = Version(version_str)
      all_versions.append((parsed_version, release["tag_name"]))

      # Separate RCs and stable releases
      if release.get('prerelease', False):
        rc_versions.append((parsed_version, release["tag_name"]))
      else:
        stable_versions.append((parsed_version, release["tag_name"]))
    except (ValueError, InvalidVersion):
      # Skip any releases with invalid version strings
      continue

  # Sort all lists by version (highest first)
  all_versions.sort(reverse=True)
  rc_versions.sort(reverse=True)
  stable_versions.sort(reverse=True)

  return all_versions, rc_versions, stable_versions


def get_highest_version(versions):
  """Return the highest version from a list of (parsed_version, tag_name) tuples."""
  if not versions:
    return None
  return versions[0][1]  # Return the tag_name of the highest version


def get_latest_rc(releases):
  """Returns the latest release candidate based on semantic versioning.
  If no release candidates are available, returns the latest stable release.
  If both a stable release and its RC exist (e.g., 8.1.1 and 8.1.1rc1),
  the stable release is preferred as it's considered newer."""
  all_versions, rc_versions, stable_versions = parse_versions(releases)

  # If there are no RCs, return the latest stable release
  if not rc_versions:
    if stable_versions:
      return get_highest_version(stable_versions)
    raise ValueError("No valid versions found")

  # Get the highest RC version
  highest_rc = rc_versions[0][0]  # This is the parsed version object
  highest_rc_tag = rc_versions[0][1]  # This is the tag name

  # Check if there's a stable version that corresponds to this RC
  # For example, if highest RC is 8.1.1rc1, check if 8.1.1 exists
  for stable_version, stable_tag in stable_versions:
    # If the stable version has the same major.minor.micro as the RC,
    # it should be preferred over the RC
    if (stable_version.major == highest_rc.major and
        stable_version.minor == highest_rc.minor and
        stable_version.micro == highest_rc.micro):
      return stable_tag

  # If no corresponding stable version exists, return the highest RC
  return highest_rc_tag


def get_latest_stable(releases):
  """Returns the latest stable release."""
  _, _, stable_versions = parse_versions(releases)

  if stable_versions:
    return get_highest_version(stable_versions)

  raise ValueError("No stable versions found")


def get_version_by_pattern(releases, major_version, include_prerelease=False):
  """Returns the highest version matching the given major version pattern."""
  all_versions, _, _ = parse_versions(releases)

  # Filter versions by major version
  filtered = [(version, tag)
              for version, tag in all_versions
              if str(version.major) == major_version and
              (include_prerelease or not version.is_prerelease)]

  if not filtered:
    raise ValueError(f"No version found for major version '{major_version}'")

  return get_highest_version(filtered)


def get_exact_version(releases, version_str):
  """Returns the exact version if it exists in releases."""
  for release in releases:
    if release["tag_name"] == version_str:
      return release["tag_name"]

  raise ValueError(f"Version '{version_str}' not found in releases")


def resolve_version_string(bazel_version, releases_json):
  """Resolves a version string to an actual Bazel version.

  Args:
    bazel_version: A string like "latest", "last_rc", "7.4.0", "7.x", "7.*"
    releases_json: The JSON data from GitHub releases API

  Returns:
    A string with the resolved Bazel version

  Raises:
    ValueError: If the version string cannot be resolved
  """
  # Handle different version patterns
  if bazel_version == "latest":
    return get_latest_stable(releases_json)
  elif bazel_version == "last_rc":
    return get_latest_rc(releases_json)
  else:
    # Check for pattern matches
    match = RE_Latest_version.match(bazel_version)
    if match:
      return get_version_by_pattern(releases_json, match.group(1))
    else:
      match = RE_Latest_version_with_candidate.match(bazel_version)
      if match:
        return get_version_by_pattern(
            releases_json, match.group(1), include_prerelease=True)
      else:
        # Try to find exact version
        return get_exact_version(releases_json, bazel_version)


def main():
  if len(sys.argv) != 2:
    print(__doc__)
    return 1

  bazel_version = sys.argv[1]

  try:
    bazelisk_directory = get_bazelisk_directory()
    os.makedirs(bazelisk_directory, exist_ok=True)

    releases_json = get_releases_json(bazelisk_directory)

    result = resolve_version_string(bazel_version, releases_json)
    print(result)
    return 0
  except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    return 1


if __name__ == '__main__':
  sys.exit(main())
