"""Tests for Clipper SVG path parsing, clipping, and the CLI."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lxml import etree

from clipper import (
    _bounds_overlap,
    _clip_output_path,
    cli,
    clip_svg,
    parse_path_data,
    parse_points,
)


SVG_NAMESPACE = {"svg": "http://www.w3.org/2000/svg"}


class ClipperTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.input_path = Path(self.temp_dir.name) / "input.svg"
        self.mask_path = Path(self.temp_dir.name) / "mask.svg"
        self.output_path = Path(self.temp_dir.name) / "output.svg"

    def write_svg(self, paths):
        self.input_path.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'width="10" height="10" viewBox="0 0 10 10">'
            + paths
            + "</svg>",
            encoding="utf-8",
        )

    def write_mask_svg(self, paths):
        self.mask_path.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'width="10" height="10" viewBox="0 0 10 10">'
            + paths
            + "</svg>",
            encoding="utf-8",
        )

    def read_paths(self):
        tree = etree.parse(str(self.output_path))
        return tree.xpath("//svg:path", namespaces=SVG_NAMESPACE)

    def test_parser_supports_flattened_absolute_and_relative_paths(self):
        parsed = parse_path_data("M 1 1 l 2 0 v 2 h -2 z M 7 7 L 8 8")

        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0], ([(1, 1), (3, 1), (3, 3), (1, 3)], True))
        self.assertEqual(parsed[1], ([(7, 7), (8, 8)], False))

    def test_parser_rejects_curve_commands(self):
        with self.assertRaisesRegex(ValueError, "flatten the SVG with Vpype"):
            parse_path_data("M 0 0 C 1 1 2 2 3 3")

    def test_parser_rejects_invalid_characters(self):
        with self.assertRaisesRegex(ValueError, "invalid characters"):
            parse_path_data("M 0 0 L 1 1 @")

    def test_clip_flattens_unflattened_svg_with_vpype(self):
        self.write_svg('<path d="M 0 0 C 1 1 2 2 3 3"/>')

        def flatten_svg(command, *, check):
            self.assertTrue(check)
            self.assertEqual(command[-2], "write")
            self.input_path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" '
                'width="10" height="10" viewBox="0 0 10 10">'
                '<path d="M 0 0 L 3 3"/>'
                "</svg>",
                encoding="utf-8",
            )

        with patch("clipper.subprocess.run", side_effect=flatten_svg) as run_mock:
            clip_svg(self.input_path, self.output_path, "hidden-line")

        run_mock.assert_called_once_with(
            [
                "vpype",
                "read",
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
                "--no-crop",
                str(self.input_path),
                "linesimplify",
                "write",
                str(self.input_path),
            ],
            check=True,
        )
        self.assertEqual(self.read_paths()[0].get("d"), "M 0 0 L 3 3")

    def test_mask_flattens_unflattened_svg_with_vpype(self):
        self.write_svg('<path id="line" d="M 0 5 L 10 5"/>')
        self.write_mask_svg('<path id="mask" d="M 2 2 C 3 2 7 2 8 2 Z"/>')

        def flatten_svg(command, *, check):
            self.assertTrue(check)
            self.assertEqual(command[2:4], ["-a", "stroke"])
            self.assertEqual(command[-2], "write")
            self.mask_path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" '
                'width="10" height="10" viewBox="0 0 10 10">'
                '<path id="mask" d="M 2 2 L 8 2 L 8 8 L 2 8 Z"/>'
                "</svg>",
                encoding="utf-8",
            )

        with patch("clipper.subprocess.run", side_effect=flatten_svg) as run_mock:
            clip_svg(
                self.input_path,
                self.output_path,
                "mask",
                mask_file=self.mask_path,
                include_mask=False,
            )

        run_mock.assert_called_once()
        line = next(path for path in self.read_paths() if path.get("id") == "line")
        self.assertEqual(line.get("d"), "M 2 5 L 8 5")

    def test_mask_flattens_input_svg_with_stroke_attribute(self):
        self.write_svg('<circle cx="5" cy="5" r="1"/>')
        self.write_mask_svg('<path id="mask" d="M 2 2 L 8 2 L 8 8 L 2 8 Z"/>')

        def flatten_svg(command, *, check):
            self.assertTrue(check)
            self.assertEqual(command[2:4], ["-a", "stroke"])
            self.input_path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" '
                'width="10" height="10" viewBox="0 0 10 10">'
                '<path id="line" d="M 0 5 L 10 5"/>'
                "</svg>",
                encoding="utf-8",
            )

        with patch("clipper.subprocess.run", side_effect=flatten_svg) as run_mock:
            clip_svg(
                self.input_path,
                self.output_path,
                "mask",
                mask_file=self.mask_path,
                include_mask=False,
            )

        run_mock.assert_called_once()
        line = next(path for path in self.read_paths() if path.get("id") == "line")
        self.assertEqual(line.get("d"), "M 2 5 L 8 5")

    def test_clip_does_not_run_vpype_for_flattened_svg(self):
        self.write_svg('<path d="M 0 0 L 10 0"/>')

        with patch("clipper.subprocess.run") as run_mock:
            clip_svg(self.input_path, self.output_path, "hidden-line")

        run_mock.assert_not_called()

    def test_clip_accepts_lines_from_vpype_flattening(self):
        self.write_svg('<circle cx="5" cy="5" r="1"/>')

        def flatten_svg(command, *, check):
            self.assertTrue(check)
            self.input_path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" '
                'width="10" height="10" viewBox="0 0 10 10">'
                '<line id="line" x1="0" y1="5" x2="10" y2="5"/>'
                "</svg>",
                encoding="utf-8",
            )

        with patch("clipper.subprocess.run", side_effect=flatten_svg) as run_mock:
            clip_svg(self.input_path, self.output_path, "hidden-line")

        run_mock.assert_called_once()
        line = self.read_paths()[0]
        self.assertEqual(line.get("id"), "line")
        self.assertEqual(line.get("d"), "M 0 5 L 10 5")
        self.assertFalse({"x1", "y1", "x2", "y2"} & set(line.attrib.keys()))

    def test_mask_flattens_svg_shapes_with_vpype(self):
        self.write_svg('<path id="line" d="M 0 5 L 10 5"/>')
        self.write_mask_svg(
            '<polygon id="mask" points="2,2 8,2 8,8 2,8"/>'
            '<circle id="point" cx="5" cy="5" r="0.5"/>'
        )

        def flatten_svg(command, *, check):
            self.assertTrue(check)
            self.assertEqual(command[-2], "write")
            self.mask_path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" '
                'width="10" height="10" viewBox="0 0 10 10">'
                '<polygon id="mask" points="2,2 8,2 8,8 2,8"/>'
                "</svg>",
                encoding="utf-8",
            )

        with patch("clipper.subprocess.run") as run_mock:
            run_mock.side_effect = flatten_svg
            clip_svg(
                self.input_path,
                self.output_path,
                "mask",
                mask_file=self.mask_path,
                include_mask=False,
            )

        run_mock.assert_called_once()
        paths = self.read_paths()
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0].get("id"), "line")
        self.assertEqual(paths[0].get("d"), "M 2 5 L 8 5")

    def test_clip_reports_missing_vpype_when_flattening_is_needed(self):
        self.write_svg('<path d="M 0 0 C 1 1 2 2 3 3"/>')

        with (
            patch(
                "clipper.subprocess.run",
                side_effect=FileNotFoundError("vpype"),
            ),
            self.assertRaisesRegex(RuntimeError, "Vpype is required"),
        ):
            clip_svg(self.input_path, self.output_path, "hidden-line")

    def test_parser_reads_vpype_polyline_points(self):
        self.assertEqual(parse_points("0.0,54.243 5.1948,53.5577"), [(0, 54.243), (5.1948, 53.5577)])

    def test_bounds_overlap_includes_touching_edges(self):
        bounds = (0, 0, 1, 1)

        self.assertTrue(_bounds_overlap(bounds, (1, 0, 2, 1)))
        self.assertFalse(_bounds_overlap(bounds, (1.01, 0, 2, 1)))

    def test_clip_output_path_uses_forward_slashes(self):
        output = _clip_output_path(
            r"C:\Users\ericl\Downloads\Float_Outrageous_seed_834975_colors_8_scale_1_P.svg"
        )

        self.assertEqual(
            output,
            "C:/Users/ericl/Downloads/"
            "Float_Outrageous_seed_834975_colors_8_scale_1_P_Clip.svg",
        )

    def test_hidden_line_removes_open_path_under_later_closed_path(self):
        self.write_svg(
            '<path id="line" d="M 0 5 L 10 5" '
            'style="stroke:#123456;stroke-width:0.5;fill:none"/>'
            '<path id="cover" d="M 4 2 L 6 2 L 6 8 L 4 8 Z" '
            'style="stroke:#abcdef;fill:#abcdef"/>'
        )

        clip_svg(self.input_path, self.output_path, "hidden-line")

        paths = self.read_paths()
        line_paths = [path for path in paths if path.get("id", "").startswith("line")]
        self.assertEqual(len(line_paths), 2)
        self.assertEqual(
            line_paths[0].get("style"),
            "stroke:#123456;stroke-width:0.5;fill:none",
        )
        endpoints = {
            tuple(point)
            for path in line_paths
            for points, closed in parse_path_data(path.get("d", ""))
            for point in (points[0], points[-1])
            if not closed
        }
        self.assertEqual(endpoints, {(0.0, 5.0), (4.0, 5.0), (6.0, 5.0), (10.0, 5.0)})
        self.assertTrue(all(path.get("d", "").startswith("M ") for path in line_paths))
        self.assertTrue(all("Z" not in path.get("d", "") for path in line_paths))
        self.assertEqual(len([path for path in paths if path.get("id") == "cover"]), 1)

    def test_hidden_line_accepts_vpype_polylines_and_preserves_group_styles(self):
        self.write_svg(
            '<g stroke="#000000" stroke-width="1" fill="none">'
            '<polyline id="line" points="0,5 10,5"/>'
            '<polyline id="cover" points="4,2 6,2 6,8 4,8 4,2"/>'
            "</g>"
        )

        clip_svg(self.input_path, self.output_path, "hidden-line")

        paths = self.read_paths()
        line_paths = [path for path in paths if path.get("id", "").startswith("line")]
        self.assertEqual(len(line_paths), 2)
        groups = [path.getparent() for path in line_paths]
        self.assertTrue(all(group.get("stroke") == "#000000" for group in groups))
        self.assertTrue(all(group.get("stroke-width") == "1" for group in groups))
        self.assertTrue(all(group.get("fill") == "none" for group in groups))
        self.assertEqual(len([path for path in paths if path.get("id") == "cover"]), 1)

    def test_hidden_line_skips_clipper_for_disjoint_path_bounds(self):
        self.write_svg(
            '<path id="line" d="M 0 0 L 1 1"/>'
            '<path id="cover" d="M 5 5 L 6 5 L 6 6 L 5 6 Z"/>'
        )

        with patch("pyclipr.Clipper") as clipper_factory:
            clip_svg(self.input_path, self.output_path, "hidden-line")

        clipper_factory.assert_not_called()
        paths = self.read_paths()
        self.assertEqual(paths[0].get("d"), "M 0 0 L 1 1")
        self.assertEqual(paths[1].get("d"), "M 5 5 L 6 5 L 6 6 L 5 6 Z")

    def test_hidden_line_clips_off_page_occluder_to_viewbox(self):
        self.write_svg(
            '<path id="line" d="M 0 5 L 10 5"/>'
            '<polygon id="mask" points="-5,-5 5,-5 5,15 -5,15"/>'
        )

        clip_svg(self.input_path, self.output_path, "hidden-line")

        paths = self.read_paths()
        line = next(path for path in paths if path.get("id") == "line")
        points, closed = parse_path_data(line.get("d", ""))[0]
        self.assertFalse(closed)
        self.assertEqual(set(points), {(5.0, 5.0), (10.0, 5.0)})

    def test_hidden_line_removes_off_page_geometry_from_output(self):
        self.write_svg('<path id="off-page" d="M 20 20 L 30 30"/>')

        clip_svg(self.input_path, self.output_path, "hidden-line")

        self.assertEqual(self.read_paths(), [])

    def test_mask_outside_selection_preserves_disjoint_path_without_clipper(self):
        self.write_svg('<path id="line" d="M 0 0 L 1 1"/>')
        self.write_mask_svg('<path id="mask" d="M 5 5 L 6 5 L 6 6 L 5 6 Z"/>')

        with patch("pyclipr.Clipper") as clipper_factory:
            clip_svg(
                self.input_path,
                self.output_path,
                "mask",
                mask_file=self.mask_path,
                keep_inside=False,
                include_mask=False,
            )

        clipper_factory.assert_not_called()
        paths = self.read_paths()
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0].get("d"), "M 0 0 L 1 1")

    def test_hidden_line_clips_closed_path_outline_without_cut_edges(self):
        self.write_svg(
            '<path id="outline" d="M 1 1 L 9 1 L 9 9 L 1 9 Z" '
            'style="stroke:#123456;fill:none"/>'
            '<path id="cover" d="M 4 0 L 6 0 L 6 10 L 4 10 Z"/>'
        )

        clip_svg(self.input_path, self.output_path, "hidden-line")

        paths = self.read_paths()
        outline_paths = [path for path in paths if path.get("id", "").startswith("outline")]
        self.assertEqual(len(outline_paths), 2)
        self.assertTrue(all("Z" not in path.get("d", "") for path in outline_paths))
        self.assertTrue(all(path.get("style") == "stroke:#123456;fill:none" for path in outline_paths))
        fragments = [
            points
            for path in outline_paths
            for points, _closed in parse_path_data(path.get("d", ""))
        ]
        self.assertTrue(
            all(
                not (
                    first[0] == second[0]
                    and first[0] in {4.0, 6.0}
                    and first[1] != second[1]
                )
                for points in fragments
                for first, second in zip(points, points[1:])
            )
        )

    def test_mask_clips_open_path_without_mask_when_excluded(self):
        self.write_mask_svg(
            '<path id="mask" d="M 2 2 L 8 2 L 8 8 L 2 8 Z" '
            'style="stroke:#ff0000;fill:none"/>'
        )
        self.write_svg(
            '<path id="line" d="M 0 5 L 10 5" '
            'style="stroke:#123456;stroke-width:0.5;fill:none"/>'
        )

        clip_svg(
            self.input_path,
            self.output_path,
            "mask",
            mask_file=self.mask_path,
            include_mask=False,
        )

        paths = self.read_paths()
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0].get("id"), "line")
        self.assertEqual(
            paths[0].get("style"),
            "stroke:#123456;stroke-width:0.5;fill:none",
        )
        clipped_line, closed = parse_path_data(paths[0].get("d", ""))[0]
        self.assertFalse(closed)
        self.assertEqual(set(clipped_line), {(2.0, 5.0), (8.0, 5.0)})

    def test_mask_preserves_closed_path_outline_inside_mask(self):
        self.write_mask_svg('<path id="mask" d="M 2 2 L 8 2 L 8 8 L 2 8 Z"/>')
        self.write_svg(
            '<path id="shape" d="M 3 3 L 7 3 L 7 7 L 3 7 Z" '
            'style="stroke:#123456;fill:none"/>'
        )

        clip_svg(
            self.input_path,
            self.output_path,
            "mask",
            mask_file=self.mask_path,
            include_mask=False,
        )

        paths = self.read_paths()
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0].get("id"), "shape")
        self.assertEqual(paths[0].get("style"), "stroke:#123456;fill:none")
        points, closed = parse_path_data(paths[0].get("d", ""))[0]
        self.assertTrue(closed)
        self.assertEqual(set(points), {(3.0, 3.0), (7.0, 3.0), (7.0, 7.0), (3.0, 7.0)})

    def test_mask_can_keep_outside_and_include_mask(self):
        self.write_svg('<path id="line" d="M 0 5 L 10 5"/>')
        self.write_mask_svg('<path id="mask" d="M 2 2 L 8 2 L 8 8 L 2 8 Z"/>')

        clip_svg(
            self.input_path,
            self.output_path,
            "mask",
            mask_file=self.mask_path,
            keep_inside=False,
        )

        paths = self.read_paths()
        self.assertEqual(len([path for path in paths if path.get("id") == "mask"]), 1)
        line_paths = [path for path in paths if path.get("id", "").startswith("line")]
        self.assertEqual(len(line_paths), 2)

    def test_mask_uses_union_of_all_closed_paths(self):
        self.write_svg('<path id="line" d="M 0 5 L 10 5"/>')
        self.write_mask_svg(
            '<path d="M 1 2 L 3 2 L 3 8 L 1 8 Z"/>'
            '<path d="M 9 2 L 7 2 L 7 8 L 9 8 Z"/>'
        )

        clip_svg(
            self.input_path,
            self.output_path,
            "mask",
            mask_file=self.mask_path,
            include_mask=False,
        )

        line_paths = self.read_paths()
        self.assertEqual(len(line_paths), 2)
        endpoints = {
            point
            for path in line_paths
            for points, closed in parse_path_data(path.get("d", ""))
            for point in (points[0], points[-1])
            if not closed
        }
        self.assertEqual(endpoints, {(1.0, 5.0), (3.0, 5.0), (7.0, 5.0), (9.0, 5.0)})

    def test_cli_mask_requires_external_mask_file(self):
        self.write_svg('<path id="line" d="M 0 5 L 10 5"/>')
        self.write_mask_svg(
            '<g stroke="#ff0000">'
            '<path id="mask" d="M 2 2 L 8 2 L 8 8 L 2 8 Z"/>'
            "</g>"
        )

        result = cli(
            [
                "mask",
                str(self.input_path),
                str(self.output_path),
                "--mask-file",
                str(self.mask_path),
            ]
        )

        self.assertEqual(result, 0)
        paths = self.read_paths()
        self.assertEqual(len(paths), 2)
        self.assertEqual(
            next(path for path in paths if path.get("id") == "line").get("d"),
            "M 2 5 L 8 5",
        )
        mask = next(path for path in paths if path.get("id") == "mask")
        self.assertEqual(mask.get("d"), "M 2 2 L 8 2 L 8 8 L 2 8 Z")
        self.assertEqual(mask.getparent().get("stroke"), "#ff0000")

    def test_mask_requires_a_separate_mask_file(self):
        self.write_svg('<path id="line" d="M 0 5 L 10 5"/>')

        with self.assertRaisesRegex(ValueError, "separate mask SVG"):
            clip_svg(self.input_path, self.output_path, "mask")

    def test_cli_writes_output(self):
        self.write_svg('<path d="M 0 0 L 10 0"/>')

        result = cli(["hidden-line", str(self.input_path), str(self.output_path)])

        self.assertEqual(result, 0)
        self.assertTrue(self.output_path.exists())


if __name__ == "__main__":
    unittest.main()
