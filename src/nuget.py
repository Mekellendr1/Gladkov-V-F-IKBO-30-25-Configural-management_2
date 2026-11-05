"""NuGet v3 repository client for fetching package dependencies."""

import json
import urllib.error
import urllib.request
from xml.etree.ElementTree import ParseError, fromstring

PACKAGE_BASE_RESOURCE = "PackageBaseAddress/3.0.0"
TIMEOUT = 30
HTTP_NOT_FOUND = 404


class NuGetError(Exception):
    """Raised on NuGet repository communication errors."""


def fetch_json(url):
    """Download a JSON document from the given URL."""
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise NuGetError("HTTP %d for %s" % (error.code, url))
    except urllib.error.URLError as error:
        raise NuGetError("network error: %s" % error.reason)
    except json.JSONDecodeError:
        raise NuGetError("invalid JSON response from %s" % url)


def find_package_base_url(service_index):
    """Locate the PackageBaseAddress/3.0.0 endpoint."""
    if not isinstance(service_index, dict):
        raise NuGetError("service index must be a JSON object")
    resources = service_index.get("resources", [])
    if not isinstance(resources, list):
        raise NuGetError("service index resources must be an array")
    for resource in resources:
        if resource.get("@type") == PACKAGE_BASE_RESOURCE:
            return resource.get("@id")
    raise NuGetError("PackageBaseAddress/3.0.0 not found")


def nuspec_url(package_base, package_id, version):
    """Build the nuspec URL for the given package and version."""
    base = package_base.rstrip("/") + "/"
    name = package_id.lower()
    ver = version.lower()
    return "%s%s/%s/%s.nuspec" % (base, name, ver, name)


def fetch_nuspec(package_base, package_id, version):
    """Download the nuspec document as raw XML text."""
    url = nuspec_url(package_base, package_id, version)
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        if error.code == HTTP_NOT_FOUND:
            raise NuGetError("package %s %s not found"
                             % (package_id, version))
        raise NuGetError("HTTP %d fetching %s" % (error.code, url))
    except urllib.error.URLError as error:
        raise NuGetError("network error: %s" % error.reason)


def parse_dependencies(nuspec_xml):
    """Extract direct dependencies from the nuspec XML document."""
    try:
        root = fromstring(nuspec_xml)
    except ParseError:
        raise NuGetError("invalid nuspec XML")
    deps = []
    seen = set()
    for element in root.iter():
        tag = element.tag
        local = tag.split("}")[1] if "}" in tag else tag
        if local == "dependency":
            dep_id = element.attrib.get("id", "").strip()
            dep_ver = element.attrib.get("version", "").strip()
            if dep_id and dep_id not in seen:
                seen.add(dep_id)
                deps.append({"id": dep_id, "version": dep_ver})
    return deps
