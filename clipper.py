"""SVG clipping with Clipper2 through pyclipr."""

import argparse
import math
import re
import subprocess
import sys
import threading
from collections.abc import Sequence
from pathlib import Path
from tkinter import IntVar, StringVar, Tk, filedialog, messagebox, ttk

from lxml import etree

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
SVG_PATH = f"{{{SVG_NAMESPACE}}}path"
SVG_LINE = f"{{{SVG_NAMESPACE}}}line"
SVG_POLYLINE = f"{{{SVG_NAMESPACE}}}polyline"
SVG_POLYGON = f"{{{SVG_NAMESPACE}}}polygon"
CLIPPER_SCALE_FACTOR = 1000
PATH_TOKEN = re.compile(r"[A-Za-z]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
PATH_COMMANDS = {"M", "L", "H", "V", "Z"}
PATH_POINT_TAGS = {SVG_POLYLINE, SVG_POLYGON}


class _FlatteningRequiredError(ValueError):
    """An SVG feature requires Vpype to flatten or convert it before clipping."""


class PathGeometry:
    """A flattened SVG subpath and its source element."""

    def __init__(
        self,
        element: etree._Element,
        parent: etree._Element,
        position: int,
        points: list[tuple[float, float]],
        closed: bool,
    ) -> None:
        self.element = element
        self.parent = parent
        self.position = position
        self.points = points
        self.closed = closed
        self.bounds = (
            min(x for x, _ in points),
            min(y for _, y in points),
            max(x for x, _ in points),
            max(y for _, y in points),
        )


def _bounds_overlap(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> bool:
    """Return whether two axis-aligned bounding boxes intersect or touch."""
    return (
        first[0] <= second[2]
        and second[0] <= first[2]
        and first[1] <= second[3]
        and second[1] <= first[3]
    )


def _parse_viewbox(
    tree: etree._ElementTree,
) -> tuple[float, float, float, float] | None:
    """Parse and validate the root SVG viewBox, if present."""
    viewbox = tree.getroot().get("viewBox")
    if viewbox is None:
        return None
    values = re.split(r"[\s,]+", viewbox.strip())
    if len(values) != 4:
        raise ValueError("SVG viewBox must contain four numbers.")
    try:
        x, y, width, height = (float(value) for value in values)
    except ValueError as error:
        raise ValueError("SVG viewBox must contain four numbers.") from error
    if not all(math.isfinite(value) for value in (x, y, width, height)):
        raise ValueError("SVG viewBox values must be finite.")
    if width <= 0 or height <= 0:
        raise ValueError("SVG viewBox width and height must be positive.")
    return x, y, x + width, y + height


def _make_geometry(
    source: PathGeometry,
    points: list[tuple[float, float]],
    closed: bool,
) -> PathGeometry:
    return PathGeometry(
        source.element,
        source.parent,
        source.position,
        points,
        closed,
    )


def _clip_closed_area_to_viewbox(
    subject: PathGeometry,
    viewbox: PathGeometry,
) -> list[PathGeometry]:
    """Intersect a closed path's filled area with the SVG page rectangle."""
    try:
        import pyclipr
    except ImportError as error:
        raise RuntimeError(
            "Clipper requires pyclipr. Install it with `pip install pyclipr`."
        ) from error

    clipper = pyclipr.Clipper()
    clipper.scaleFactor = CLIPPER_SCALE_FACTOR
    clipper.addPath(subject.points, pyclipr.Subject, False)
    clipper.addPath(viewbox.points, pyclipr.Clip, False)
    paths = clipper.execute(pyclipr.Intersection, pyclipr.FillRule.NonZero)
    clipped = [
        _make_geometry(
            subject,
            [(float(point[0]), float(point[1])) for point in path],
            True,
        )
        for path in paths
        if len(path) >= 3
    ]
    return clipped


def parse_path_data(data: str) -> list[tuple[list[tuple[float, float]], bool]]:
    """Parse flattened SVG path data containing only move/line/close commands."""
    tokens: list[str] = []
    position = 0
    for match in PATH_TOKEN.finditer(data):
        if data[position : match.start()].strip(" ,\t\r\n"):
            raise ValueError("SVG path data contains invalid characters.")
        tokens.append(match.group())
        position = match.end()
    if data[position:].strip(" ,\t\r\n"):
        raise ValueError("SVG path data contains invalid characters.")
    if not tokens:
        return []

    paths: list[tuple[list[tuple[float, float]], bool]] = []
    points: list[tuple[float, float]] = []
    closed = False
    command = ""
    index = 0
    x = y = 0.0

    def finish() -> None:
        nonlocal points, closed
        if points:
            if len(points) < 2:
                raise ValueError("Each SVG path must contain at least two points.")
            paths.append((points, closed))
        points = []
        closed = False

    while index < len(tokens):
        token = tokens[index]
        if token.isalpha():
            command = token
            index += 1
            if command.upper() not in PATH_COMMANDS:
                raise _FlatteningRequiredError(
                    f"Unsupported SVG path command {command!r}; "
                    "flatten the SVG with Vpype before clipping."
                )
            if command.upper() == "Z":
                if not points:
                    raise ValueError("SVG path closes before a subpath begins.")
                x, y = points[0]
                closed = True
                finish()
                if index < len(tokens) and not tokens[index].isalpha():
                    raise ValueError("SVG path data has numbers after a close command.")
                continue
        elif not command:
            raise ValueError("SVG path data must begin with a move command.")

        upper_command = command.upper()
        relative = command.islower()
        if upper_command == "M":
            if index + 1 >= len(tokens) or tokens[index].isalpha():
                raise ValueError("SVG move command requires an x/y coordinate pair.")
            if points:
                finish()
            px, py = float(tokens[index]), float(tokens[index + 1])
            index += 2
            if relative:
                px += x
                py += y
            if not math.isfinite(px) or not math.isfinite(py):
                raise ValueError("SVG path coordinates must be finite numbers.")
            x, y = px, py
            points = [(x, y)]
            command = "l" if relative else "L"
            continue

        if not points:
            raise ValueError(
                "SVG path data must begin each subpath with a move command."
            )

        if upper_command in {"L", "H", "V"}:
            operand_count = 2 if upper_command == "L" else 1
            if index + operand_count > len(tokens) or any(
                item.isalpha() for item in tokens[index : index + operand_count]
            ):
                raise ValueError(f"SVG {upper_command} command has incomplete values.")
            if upper_command == "L":
                px, py = float(tokens[index]), float(tokens[index + 1])
                index += 2
                if relative:
                    px += x
                    py += y
            elif upper_command == "H":
                px = float(tokens[index])
                index += 1
                py = y
                if relative:
                    px += x
            else:
                py = float(tokens[index])
                index += 1
                px = x
                if relative:
                    py += y
            if not math.isfinite(px) or not math.isfinite(py):
                raise ValueError("SVG path coordinates must be finite numbers.")
            x, y = px, py
            points.append((x, y))
        else:
            raise _FlatteningRequiredError(
                f"Unsupported SVG path command {command!r}; "
                "flatten the SVG with Vpype before clipping."
            )

    finish()
    if not paths:
        raise ValueError("SVG path contains no drawable subpaths.")
    return paths


def parse_points(data: str) -> list[tuple[float, float]]:
    """Parse the coordinate list used by SVG polyline and polygon elements."""
    tokens: list[str] = []
    position = 0
    for match in re.finditer(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?", data):
        if data[position : match.start()].strip(" ,\t\r\n"):
            raise ValueError("SVG point list contains invalid characters.")
        tokens.append(match.group())
        position = match.end()
    if data[position:].strip(" ,\t\r\n"):
        raise ValueError("SVG point list contains invalid characters.")
    if not tokens or len(tokens) % 2:
        raise ValueError("SVG polyline points must contain x/y coordinate pairs.")

    coordinates = [float(token) for token in tokens]
    if not all(math.isfinite(value) for value in coordinates):
        raise ValueError("SVG point coordinates must be finite numbers.")
    points = list(zip(coordinates[::2], coordinates[1::2]))
    if len(points) < 2:
        raise ValueError("Each SVG line must contain at least two points.")
    return points


def _read_svg(
    input_file: str | Path,
) -> tuple[etree._ElementTree, list[PathGeometry]]:
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    tree = etree.parse(str(input_file), parser)
    root = tree.getroot()
    paths: list[PathGeometry] = []
    skipped_tags = {"defs", "clipPath", "mask", "marker", "pattern", "symbol"}

    for element in root.iter():
        if element.tag not in {SVG_PATH, SVG_LINE, *PATH_POINT_TAGS}:
            continue
        if any(
            isinstance(parent.tag, str)
            and etree.QName(parent).localname in skipped_tags
            for parent in element.iterancestors()
        ):
            continue
        if "transform" in element.attrib or any(
            "transform" in parent.attrib for parent in element.iterancestors()
        ):
            raise _FlatteningRequiredError(
                "Transformed SVG paths are not supported; flatten the SVG with Vpype."
            )
        if element.getparent() is None:
            continue
        source_data = element.get("d", "")
        parent = element.getparent()
        position = parent.index(element)
        if element.tag == SVG_LINE:
            try:
                coordinates = [
                    float(element.get(name, "0")) for name in ("x1", "y1", "x2", "y2")
                ]
            except ValueError as error:
                raise ValueError("SVG line coordinates must be numbers.") from error
            if not all(math.isfinite(value) for value in coordinates):
                raise ValueError("SVG line coordinates must be finite numbers.")
            points = [
                (coordinates[0], coordinates[1]),
                (coordinates[2], coordinates[3]),
            ]
            subpaths = [(points, False)]
        elif element.tag in PATH_POINT_TAGS:
            points = parse_points(element.get("points", ""))
            closed = element.tag == SVG_POLYGON or points[0] == points[-1]
            if closed and points[0] == points[-1]:
                points = points[:-1]
            subpaths = [(points, closed)]
        else:
            subpaths = parse_path_data(source_data)
        for points, closed in subpaths:
            paths.append(PathGeometry(element, parent, position, points, closed))

    if not paths:
        raise _FlatteningRequiredError(
            "No flattened SVG paths found. Convert the SVG to paths with Vpype first."
        )
    shape_tags = {
        "circle",
        "ellipse",
        "image",
        "rect",
        "text",
        "use",
    }
    if any(
        etree.QName(element).localname in shape_tags
        and not any(
            isinstance(parent.tag, str)
            and etree.QName(parent).localname in skipped_tags
            for parent in element.iterancestors()
        )
        for element in root.iter()
        if isinstance(element.tag, str)
    ):
        raise _FlatteningRequiredError(
            "SVG contains unconverted shapes; convert the SVG to paths with Vpype first."
        )
    return tree, paths


def _flatten_svg(input_file: str | Path, operation: str) -> None:
    """Flatten and simplify an SVG in place using Vpype."""
    parse_attributes = (
        ["-a", "stroke"]
        if operation == "mask"
        else [
            "-a",
            "d",
            "-a",
            "points",
            "-a",
            "x1",
            "-a",
            "x2",
            "-a",
            "y1",
            "-a",
            "y2",
        ]
    )
    command = [
        "vpype",
        "read",
        *parse_attributes,
        "--no-crop",
        str(input_file),
        "write",
        str(input_file),
    ]
    try:
        subprocess.run(command, check=True)
    except FileNotFoundError as error:
        raise RuntimeError(
            "Vpype is required to automatically flatten this SVG, but its "
            "executable was not found."
        ) from error
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"Vpype failed to flatten {input_file} (exit code {error.returncode})."
        ) from error


def _format_path(points: Sequence[tuple[float, float]], closed: bool) -> str:
    if not points:
        raise ValueError("Clipper returned an empty path.")
    commands = [f"M {_format_number(points[0][0])} {_format_number(points[0][1])}"]
    commands.extend(f"L {_format_number(x)} {_format_number(y)}" for x, y in points[1:])
    if closed:
        commands.append("Z")
    return " ".join(commands)


def _format_number(value: float) -> str:
    rounded = round(float(value), 6)
    if not math.isfinite(rounded):
        raise ValueError("Clipper returned a non-finite coordinate.")
    return format(rounded, ".6f").rstrip("0").rstrip(".") or "0"


def _join_fragments(
    fragments: Sequence[list[tuple[float, float]]],
) -> list[tuple[list[tuple[float, float]], bool]]:
    remaining = [list(fragment) for fragment in fragments if len(fragment) >= 2]
    joined: list[tuple[list[tuple[float, float]], bool]] = []
    while remaining:
        chain = remaining.pop(0)
        changed = True
        while changed:
            changed = False
            for index, fragment in enumerate(remaining):
                if chain[-1] == fragment[0]:
                    chain.extend(fragment[1:])
                elif chain[-1] == fragment[-1]:
                    chain.extend(reversed(fragment[:-1]))
                elif chain[0] == fragment[-1]:
                    chain = fragment[:-1] + chain
                elif chain[0] == fragment[0]:
                    chain = list(reversed(fragment[1:])) + chain
                else:
                    continue
                remaining.pop(index)
                changed = True
                break
        closed = chain[0] == chain[-1]
        if closed:
            chain.pop()
        joined.append((chain, closed))
    return joined


def _clip_one(
    subject: PathGeometry,
    clips: Sequence[PathGeometry],
    operation: str,
) -> list[tuple[list[tuple[float, float]], bool]]:
    if not clips:
        return [(subject.points, subject.closed)]

    try:
        import pyclipr
    except ImportError as error:
        raise RuntimeError(
            "Clipper requires pyclipr. Install it with `pip install pyclipr`."
        ) from error

    clipper = pyclipr.Clipper()
    clipper.scaleFactor = CLIPPER_SCALE_FACTOR
    if subject.closed:
        subject_points = subject.points
        if subject_points[0] == subject_points[-1]:
            subject_points = subject_points[:-1]
        edges = zip(subject_points, [*subject_points[1:], subject_points[0]])
        for start, end in edges:
            if start != end:
                clipper.addPath([start, end], pyclipr.Subject, True)
    else:
        clipper.addPath(subject.points, pyclipr.Subject, True)
    for clip in clips:
        clipper.addPath(clip.points, pyclipr.Clip, not clip.closed)

    clip_type = (
        pyclipr.Intersection if operation == "intersection" else pyclipr.Difference
    )
    closed_paths, open_paths = clipper.execute(
        clip_type, pyclipr.FillRule.NonZero, returnOpenPaths=True
    )
    results: list[tuple[list[tuple[float, float]], bool]] = []
    for path in closed_paths:
        points = [(float(point[0]), float(point[1])) for point in path]
        if len(points) >= 3:
            results.append((points, True))
    fragments = [
        [(float(point[0]), float(point[1])) for point in path]
        for path in open_paths
        if len(path) >= 2
    ]
    if subject.closed:
        results.extend(_join_fragments(fragments))
    else:
        results.extend((path, False) for path in fragments)
    return results


def clip_svg(
    input_file: str | Path,
    output_file: str | Path,
    operation: str,
    *,
    mask_file: str | Path | None = None,
    keep_inside: bool = True,
    include_mask: bool = True,
) -> None:
    """Clip an SVG using drawing-order occlusion or a separate mask SVG."""
    if operation not in {"hidden-line", "mask"}:
        raise ValueError("Operation must be 'hidden-line' or 'mask'.")
    try:
        tree, paths = _read_svg(input_file)
    except _FlatteningRequiredError:
        _flatten_svg(input_file, operation)
        tree, paths = _read_svg(input_file)
    mask_paths: list[PathGeometry] = []
    if operation == "mask":
        if mask_file is None:
            raise ValueError("A separate mask SVG file is required for mask mode.")
        try:
            _, mask_geometry = _read_svg(mask_file)
        except _FlatteningRequiredError:
            _flatten_svg(mask_file, operation)
            _, mask_geometry = _read_svg(mask_file)
        mask_paths = [path for path in mask_geometry if path.closed]
        if not mask_paths:
            raise ValueError("The mask SVG must contain at least one closed path.")
    viewbox_bounds = _parse_viewbox(tree) if operation == "hidden-line" else None
    viewbox_geometry = (
        _make_geometry(
            paths[0],
            [
                (viewbox_bounds[0], viewbox_bounds[1]),
                (viewbox_bounds[2], viewbox_bounds[1]),
                (viewbox_bounds[2], viewbox_bounds[3]),
                (viewbox_bounds[0], viewbox_bounds[3]),
            ],
            True,
        )
        if viewbox_bounds is not None
        else None
    )
    replacements: dict[int, list[tuple[list[tuple[float, float]], bool]]] = {}
    occluders_by_path: list[list[PathGeometry]] = [[] for _ in paths]
    if viewbox_geometry is not None and viewbox_bounds is not None:
        for index, path in enumerate(paths):
            if not path.closed:
                continue
            if (
                path.bounds[0] >= viewbox_bounds[0]
                and path.bounds[1] >= viewbox_bounds[1]
                and path.bounds[2] <= viewbox_bounds[2]
                and path.bounds[3] <= viewbox_bounds[3]
            ):
                occluders_by_path[index] = [path]
            elif _bounds_overlap(path.bounds, viewbox_bounds):
                clipped_occluders = _clip_closed_area_to_viewbox(path, viewbox_geometry)
                occluders_by_path[index] = clipped_occluders
    else:
        occluders_by_path = [[path] if path.closed else [] for path in paths]

    for index, subject in enumerate(paths):
        if operation == "hidden-line":
            subjects = [subject]
            if viewbox_geometry is not None and viewbox_bounds is not None:
                if not _bounds_overlap(subject.bounds, viewbox_bounds):
                    subjects = []
                elif not (
                    subject.bounds[0] >= viewbox_bounds[0]
                    and subject.bounds[1] >= viewbox_bounds[1]
                    and subject.bounds[2] <= viewbox_bounds[2]
                    and subject.bounds[3] <= viewbox_bounds[3]
                ):
                    clipped_subjects = _clip_one(
                        subject, [viewbox_geometry], "intersection"
                    )
                    subjects = [
                        _make_geometry(subject, points, closed)
                        for points, closed in clipped_subjects
                    ]
            if not subjects:
                replacements.setdefault(id(subject.element), [])
                continue

            clip_paths = []
            for path_index in range(index + 1, len(paths)):
                for path in occluders_by_path[path_index]:
                    overlaps = False
                    for clipped_subject in subjects:
                        if _bounds_overlap(clipped_subject.bounds, path.bounds):
                            overlaps = True
                            break
                    if overlaps:
                        clip_paths.append(path)
            clip_type = "difference"
        else:
            subject_masks = []
            for mask in mask_paths:
                if _bounds_overlap(subject.bounds, mask.bounds):
                    subject_masks.append(mask)
            if not subject_masks:
                results = [] if keep_inside else [(subject.points, subject.closed)]
                replacements.setdefault(id(subject.element), []).extend(results)
                continue
            clip_paths = subject_masks
            clip_type = "intersection" if keep_inside else "difference"

        if not clip_paths:
            results = (
                [(path.points, path.closed) for path in subjects]
                if operation == "hidden-line"
                else [(subject.points, subject.closed)]
            )
        else:
            results = []
            clipping_subjects = subjects if operation == "hidden-line" else [subject]
            for clipping_subject in clipping_subjects:
                subject_clips = [
                    path
                    for path in clip_paths
                    if _bounds_overlap(clipping_subject.bounds, path.bounds)
                ]
                if not subject_clips:
                    results.append((clipping_subject.points, clipping_subject.closed))
                    continue
                clipped_results = _clip_one(clipping_subject, subject_clips, clip_type)
                results.extend(clipped_results)
        replacements.setdefault(id(subject.element), []).extend(results)

    elements: dict[int, tuple[etree._Element, etree._Element, int]] = {}
    for path in paths:
        elements[id(path.element)] = (path.element, path.parent, path.position)
    grouped_outputs: dict[int, list[tuple[list[tuple[float, float]], bool]]] = {}
    for path in paths:
        grouped_outputs.setdefault(id(path.element), [])
    for element_id, results in replacements.items():
        grouped_outputs[element_id] = results

    for element_id, (element, parent, position) in sorted(
        elements.items(), key=lambda item: (id(item[1][1]), -item[1][2])
    ):
        results = grouped_outputs[element_id]
        parent.remove(element)
        for result_index, (points, closed) in enumerate(results):
            output_element = etree.Element(SVG_PATH, attrib=dict(element.attrib))
            output_element.attrib.pop("points", None)
            if element.tag == SVG_LINE:
                for name in ("x1", "y1", "x2", "y2"):
                    output_element.attrib.pop(name, None)
            output_element.set("d", _format_path(points, closed))
            original_id = element.get("id")
            if original_id and result_index:
                output_element.set("id", f"{original_id}_clip_{result_index + 1}")
            parent.insert(position + result_index, output_element)
    if operation == "mask" and include_mask:
        root = tree.getroot()
        used_ids = {
            element.get("id")
            for element in root.iter()
            if element.get("id") is not None
        }
        for mask in mask_paths:
            ancestors = list(reversed(list(mask.element.iterancestors())))
            parent = root
            for ancestor in ancestors:
                if ancestor is root:
                    continue
                copied_group = etree.Element(ancestor.tag)
                copied_group.attrib.update(
                    (name, value)
                    for name, value in ancestor.attrib.items()
                    if name != "id"
                )
                parent.append(copied_group)
                parent = copied_group
            output_element = etree.Element(SVG_PATH, attrib=dict(mask.element.attrib))
            output_element.attrib.pop("points", None)
            output_element.set("d", _format_path(mask.points, mask.closed))
            original_id = output_element.get("id")
            if original_id:
                unique_id = original_id
                suffix = 2
                while unique_id in used_ids:
                    unique_id = f"{original_id}_mask_{suffix}"
                    suffix += 1
                output_element.set("id", unique_id)
                used_ids.add(unique_id)
            parent.append(output_element)
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(
        output_path.as_posix(),
        encoding="utf-8",
        xml_declaration=True,
        pretty_print=True,
    )


def _clip_output_path(input_file: str | Path) -> str:
    input_path = Path(input_file)
    return input_path.with_name(f"{input_path.stem}_Clip.svg").as_posix()


def build_argument_parser() -> argparse.ArgumentParser:
    """Create the standalone command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Clip flattened SVG paths with Clipper2 through pyclipr."
    )
    subparsers = parser.add_subparsers(dest="operation", required=True)

    hidden = subparsers.add_parser(
        "hidden-line", help="remove portions covered by later closed paths"
    )
    hidden.add_argument("input", type=Path, help="input SVG")
    hidden.add_argument("output", type=Path, help="output SVG")

    mask = subparsers.add_parser("mask", help="clip paths against closed mask paths")
    mask.add_argument("input", type=Path, help="input SVG")
    mask.add_argument("output", type=Path, help="output SVG")
    mask.add_argument(
        "--mask-file",
        type=Path,
        required=True,
        help="separate SVG containing closed masking paths",
    )
    mask.add_argument(
        "--outside",
        action="store_true",
        help="keep geometry outside the mask instead of inside",
    )
    mask.add_argument(
        "--exclude-mask",
        action="store_true",
        help="remove the masking path from the output",
    )
    return parser


def cli(argv: Sequence[str] | None = None) -> int:
    """Run the standalone command-line interface."""
    args = build_argument_parser().parse_args(argv)
    try:
        clip_svg(
            args.input,
            args.output,
            args.operation,
            mask_file=getattr(args, "mask_file", None),
            keep_inside=not getattr(args, "outside", False),
            include_mask=not getattr(args, "exclude_mask", False),
        )
    except (OSError, etree.XMLSyntaxError, RuntimeError, ValueError) as error:
        print(f"clipper: error: {error}", file=sys.stderr)
        return 2
    print(f"Wrote {args.output.as_posix()}")
    return 0


def main(input_files: tuple[str, ...] = ()) -> tuple[str, ...]:
    """Create the Clipper GUI and process the selected SVG files."""
    global window
    from gui_helpers import disable_combobox_scroll, set_title_icon
    from settings import init, set_theme
    from utils import on_closing

    output_files: list[str] = []
    window = Tk()
    disable_combobox_scroll(window)
    set_title_icon(window, "Clipper")
    window.resizable(False, False)
    init()
    set_theme(window)
    operation = StringVar(window, value="hidden-line")
    mask_file = StringVar(window)
    include_mask = IntVar(window, value=1)
    keep_inside = IntVar(window, value=1)

    ttk.Label(window, text="Clipper2 SVG Clipping").grid(
        row=0, column=0, columnspan=3, padx=10, pady=(10, 4)
    )
    ttk.Radiobutton(
        window, text="Hidden-line removal", variable=operation, value="hidden-line"
    ).grid(row=1, column=0, columnspan=3, sticky="w", padx=10)
    ttk.Label(
        window,
        text="Later closed paths hide earlier paths.",
        wraplength=340,
    ).grid(row=2, column=0, columnspan=3, sticky="w", padx=28)
    ttk.Radiobutton(
        window, text="Clip to separate mask SVG", variable=operation, value="mask"
    ).grid(row=3, column=0, columnspan=3, sticky="w", padx=10)
    ttk.Label(window, text="Mask SVG file:").grid(
        row=4, column=0, sticky="e", padx=(10, 4), pady=4
    )
    ttk.Entry(window, textvariable=mask_file, width=32).grid(
        row=4, column=1, sticky="ew"
    )
    ttk.Button(
        window,
        text="Browse...",
        command=lambda: mask_file.set(
            filedialog.askopenfilename(
                title="Select mask SVG",
                filetypes=(("SVG files", "*.svg"), ("All files", "*.*")),
                parent=window,
            )
        ),
    ).grid(row=4, column=2, sticky="w", padx=(4, 10))
    ttk.Checkbutton(
        window, text="Keep geometry inside mask", variable=keep_inside
    ).grid(row=5, column=0, columnspan=3, sticky="w", padx=28)
    ttk.Checkbutton(window, text="Include mask in output", variable=include_mask).grid(
        row=6, column=0, columnspan=3, sticky="w", padx=28
    )
    status = ttk.Label(window, text=f"{len(input_files)} SVG file(s) selected")
    status.grid(row=7, column=0, columnspan=3, padx=10, pady=6)

    def process_files(
        selected_operation: str,
        selected_mask_file: str | None,
        selected_keep_inside: bool,
        selected_include_mask: bool,
    ) -> None:
        try:
            created: list[str] = []
            for input_file in input_files:
                output = _clip_output_path(input_file)
                clip_svg(
                    input_file,
                    output,
                    selected_operation,
                    mask_file=selected_mask_file,
                    keep_inside=selected_keep_inside,
                    include_mask=selected_include_mask,
                )
                created.append(output)
        except (OSError, etree.XMLSyntaxError, RuntimeError, ValueError) as error:
            window.after(0, lambda error=error: show_error(error))
            return

        def finish() -> None:
            output_files.extend(created)
            status.configure(text=f"Created {len(created)} output file(s)")
            on_closing(window)

        window.after(0, finish)

    def show_error(error: Exception) -> None:
        messagebox.showerror("Clipper error", str(error), parent=window)
        run_button.configure(state="normal")
        cancel_button.configure(state="normal")

    def run() -> None:
        if not input_files:
            messagebox.showerror(
                "Clipper", "No input SVG files selected.", parent=window
            )
            return
        selected_operation = operation.get()
        selected_mask_file = mask_file.get() if selected_operation == "mask" else None
        if selected_operation == "mask" and (
            not selected_mask_file or not Path(selected_mask_file).is_file()
        ):
            messagebox.showerror(
                "Clipper error",
                "Select an existing mask SVG file.",
                parent=window,
            )
            return
        run_button.configure(state="disabled")
        cancel_button.configure(state="disabled")
        status.configure(text="Processing...")
        threading.Thread(
            target=process_files,
            args=(
                selected_operation,
                selected_mask_file,
                bool(keep_inside.get()),
                bool(include_mask.get()),
            ),
            daemon=True,
        ).start()

    def close() -> None:
        if run_button.instate(["disabled"]):
            return
        on_closing(window)

    run_button = ttk.Button(window, text="Run", command=run)
    run_button.grid(row=8, column=0, padx=10, pady=(4, 10), sticky="e")
    cancel_button = ttk.Button(window, text="Cancel", command=close)
    cancel_button.grid(row=8, column=1, padx=10, pady=(4, 10), sticky="w")
    window.protocol("WM_DELETE_WINDOW", close)
    window.mainloop()
    return tuple(output_files)


if __name__ == "__main__":
    raise SystemExit(cli())
