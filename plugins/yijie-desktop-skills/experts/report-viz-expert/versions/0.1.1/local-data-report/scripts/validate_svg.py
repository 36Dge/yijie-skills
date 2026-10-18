"""Validate a generated SVG from stdin before delivery; Python standard library only."""
import sys
import xml.etree.ElementTree as ET


def main():
    source = sys.stdin.buffer.read(8 * 1024 * 1024 + 1)
    if len(source) > 8 * 1024 * 1024:
        raise ValueError("generated SVG exceeds supported size")
    root = ET.fromstring(source)
    if root.tag != "{http://www.w3.org/2000/svg}svg":
        raise ValueError("output is not an SVG document")
    if not root.get("width") or not root.get("height"):
        raise ValueError("SVG dimensions are missing")
    if not any(node.tag == "{http://www.w3.org/2000/svg}path" for node in root.iter()):
        raise ValueError("SVG has no chart paths")
    print("SVG XML valid")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, ET.ParseError) as error:
        print(f"SVG validation failed: {error}", file=sys.stderr)
        sys.exit(2)
