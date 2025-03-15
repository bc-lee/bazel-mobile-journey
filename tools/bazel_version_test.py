#!/usr/bin/env python3
"""
Unit tests for bazel_version.py
"""

import os
import sys
import unittest
from io import StringIO
from unittest import mock

# Add the parent directory to the path so we can import bazel_version
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import bazel_version


class TestBazelVersion(unittest.TestCase):
  """Test cases for bazel_version.py"""

  def setUp(self):
    """Set up test fixtures"""
    # Sample releases data for testing
    self.mock_releases = [{
        "tag_name": "6.0.0",
        "prerelease": False
    }, {
        "tag_name": "6.1.0",
        "prerelease": False
    }, {
        "tag_name": "6.1.1",
        "prerelease": False
    }, {
        "tag_name": "6.2.0rc1",
        "prerelease": True
    }, {
        "tag_name": "6.2.0rc2",
        "prerelease": True
    }, {
        "tag_name": "6.2.0",
        "prerelease": False
    }, {
        "tag_name": "7.0.0rc1",
        "prerelease": True
    }, {
        "tag_name": "7.0.0rc2",
        "prerelease": True
    }, {
        "tag_name": "7.0.0",
        "prerelease": False
    }, {
        "tag_name": "7.0.1",
        "prerelease": False
    }, {
        "tag_name": "7.1.0rc1",
        "prerelease": True
    }, {
        "tag_name": "invalid-version",
        "prerelease": False
    }]

  def test_version_class(self):
    """Test the custom Version class"""
    # Test basic version parsing
    v1 = bazel_version.Version("1.2.3")
    self.assertEqual(v1.major, 1)
    self.assertEqual(v1.minor, 2)
    self.assertEqual(v1.micro, 3)
    self.assertEqual(v1.suffix, "")
    self.assertFalse(v1.is_prerelease)

    # Test version with suffix
    v2 = bazel_version.Version("1.2.3rc1")
    self.assertEqual(v2.major, 1)
    self.assertEqual(v2.minor, 2)
    self.assertEqual(v2.micro, 3)
    self.assertEqual(v2.suffix, "rc1")
    self.assertTrue(v2.is_prerelease)

    # Test version with only major.minor
    v3 = bazel_version.Version("1.2")
    self.assertEqual(v3.major, 1)
    self.assertEqual(v3.minor, 2)
    self.assertEqual(v3.micro, 0)
    self.assertEqual(v3.suffix, "")

    # Test version with only major
    v4 = bazel_version.Version("1")
    self.assertEqual(v4.major, 1)
    self.assertEqual(v4.minor, 0)
    self.assertEqual(v4.micro, 0)
    self.assertEqual(v4.suffix, "")

    # Test invalid version
    with self.assertRaises(bazel_version.InvalidVersion):
      bazel_version.Version("invalid")

  def test_version_comparison(self):
    """Test version comparison logic"""
    # Test basic ordering
    v1 = bazel_version.Version("1.0.0")
    v2 = bazel_version.Version("2.0.0")
    v3 = bazel_version.Version("1.1.0")
    v4 = bazel_version.Version("1.0.1")

    self.assertTrue(v1 < v2)  # Major version comparison
    self.assertTrue(v1 < v3)  # Minor version comparison
    self.assertTrue(v1 < v4)  # Micro version comparison
    self.assertTrue(v3 < v2)  # 1.1.0 < 2.0.0
    self.assertTrue(v4 < v3)  # 1.0.1 < 1.1.0

    # Test RC versions
    v5 = bazel_version.Version("1.0.0rc1")
    v6 = bazel_version.Version("1.0.0")

    self.assertTrue(v5 < v6)  # RC is less than stable
    self.assertFalse(v6 < v5)  # Stable is not less than RC

    # Test equality
    v7 = bazel_version.Version("1.0.0")

    self.assertEqual(v7, v1)
    self.assertNotEqual(v7, v2)

  def test_parse_versions(self):
    """Test parsing and categorizing versions from releases data"""
    all_versions, rc_versions, stable_versions = bazel_version.parse_versions(
        self.mock_releases)

    # Check counts (excluding the invalid version)
    self.assertEqual(len(all_versions), 11)
    self.assertEqual(len(rc_versions), 5)
    self.assertEqual(len(stable_versions), 6)

    # Check sorting (highest first)
    self.assertEqual(all_versions[0][1], "7.1.0rc1")
    self.assertEqual(stable_versions[0][1], "7.0.1")
    self.assertEqual(rc_versions[0][1], "7.1.0rc1")

  def test_get_highest_version(self):
    """Test getting the highest version from a list"""
    # Create a sample list of (parsed_version, tag_name) tuples
    versions = [(bazel_version.Version("6.0.0"), "6.0.0"),
                (bazel_version.Version("7.0.0"), "7.0.0"),
                (bazel_version.Version("6.1.0"), "6.1.0")]

    # Sort the versions by the parsed_version (highest first)
    versions.sort(key=lambda x: x[0], reverse=True)

    highest = bazel_version.get_highest_version(versions)
    self.assertEqual(highest, "7.0.0")

    # Test with empty list
    self.assertIsNone(bazel_version.get_highest_version([]))

  def test_get_latest_stable(self):
    """Test getting the latest stable release"""
    latest_stable = bazel_version.get_latest_stable(self.mock_releases)
    self.assertEqual(latest_stable, "7.0.1")

    # Test with no stable releases
    with self.assertRaises(ValueError):
      bazel_version.get_latest_stable([{
          "tag_name": "7.0.0rc1",
          "prerelease": True
      }])

  def test_get_latest_rc(self):
    """Test getting the latest release candidate"""
    latest_rc = bazel_version.get_latest_rc(self.mock_releases)
    self.assertEqual(latest_rc, "7.1.0rc1")

    # Test when stable version exists for RC
    mock_data = [{
        "tag_name": "6.0.0rc1",
        "prerelease": True
    }, {
        "tag_name": "6.0.0",
        "prerelease": False
    }]
    self.assertEqual(bazel_version.get_latest_rc(mock_data), "6.0.0")

    # Test with no RC releases
    mock_data = [{"tag_name": "6.0.0", "prerelease": False}]
    self.assertEqual(bazel_version.get_latest_rc(mock_data), "6.0.0")

    # Test with no releases at all
    with self.assertRaises(ValueError):
      bazel_version.get_latest_rc([])

  def test_get_version_by_pattern(self):
    """Test getting version by major version pattern"""
    # Test getting latest 6.x (stable only)
    version = bazel_version.get_version_by_pattern(self.mock_releases, "6")
    self.assertEqual(version, "6.2.0")

    # Test getting latest 7.x (stable only)
    version = bazel_version.get_version_by_pattern(self.mock_releases, "7")
    self.assertEqual(version, "7.0.1")

    # Test getting latest 7.x (including prereleases)
    version = bazel_version.get_version_by_pattern(
        self.mock_releases, "7", include_prerelease=True)
    self.assertEqual(version, "7.1.0rc1")

    # Test with non-existent major version
    with self.assertRaises(ValueError):
      bazel_version.get_version_by_pattern(self.mock_releases, "8")

  def test_get_exact_version(self):
    """Test getting an exact version"""
    version = bazel_version.get_exact_version(self.mock_releases, "7.0.0")
    self.assertEqual(version, "7.0.0")

    # Test with non-existent version
    with self.assertRaises(ValueError):
      bazel_version.get_exact_version(self.mock_releases, "8.0.0")

  def test_resolve_version_string_latest(self):
    """Test resolving 'latest' version string"""
    version = bazel_version.resolve_version_string("latest", self.mock_releases)
    self.assertEqual(version, "7.0.1")

  def test_resolve_version_string_last_rc(self):
    """Test resolving 'last_rc' version string"""
    version = bazel_version.resolve_version_string("last_rc",
                                                   self.mock_releases)
    self.assertEqual(version, "7.1.0rc1")

  def test_resolve_version_string_major_x(self):
    """Test resolving 'N.x' version string"""
    version = bazel_version.resolve_version_string("6.x", self.mock_releases)
    self.assertEqual(version, "6.2.0")

  def test_resolve_version_string_major_star(self):
    """Test resolving 'N.*' version string"""
    version = bazel_version.resolve_version_string("7.*", self.mock_releases)
    self.assertEqual(version, "7.1.0rc1")

  def test_resolve_version_string_exact(self):
    """Test resolving exact version string"""
    version = bazel_version.resolve_version_string("7.0.0", self.mock_releases)
    self.assertEqual(version, "7.0.0")

  @mock.patch('sys.stdout', new_callable=StringIO)
  @mock.patch('sys.argv')
  def test_main_no_args(self, mock_argv, mock_stdout):
    """Test main function with no arguments"""
    # Setup mocks
    mock_argv.__getitem__.side_effect = lambda idx: ["bazel_version.py"][idx]
    mock_argv.__len__.return_value = 1

    # Run main
    exit_code = bazel_version.main()

    # Verify
    self.assertEqual(exit_code, 1)
    self.assertTrue("Usage:" in mock_stdout.getvalue())


if __name__ == '__main__':
  unittest.main()
