# Copyright 2020 Google Sans Authors
# Copyright 2021 Simon Cozens

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import sys
import textwrap
from pathlib import Path
from fontbakery.callable import check, condition
from fontbakery.checkrunner import FAIL, PASS, SKIP, Section
from fontbakery.fonts_profile import profile_factory
from vharfbuzz import Vharfbuzz
from os.path import basename
from stringbrewer import StringBrewer
from collidoscope import Collidoscope


# Make FontBakery able to find the update_shaping_test_data package.
sys.path.append(str(Path(__file__).parent.parent))


profile_imports = ()
profile = profile_factory(default_section=Section("Shaping Checks"))

PROFILE_CHECKS = [
    "com.google.fonts/check/shaping/regression",
    "com.google.fonts/check/shaping/forbidden",
    "com.google.fonts/check/shaping/collides",
]


def get_from_test_with_default(test, configuration, el, default=None):
    defaults = configuration.get("defaults", {})
    return test.get(el, defaults.get(el, default))


def get_shaping_parameters(test, configuration):
    params = {}
    for el in ["script", "language", "direction", "comparison_mode", "features"]:
        params[el] = get_from_test_with_default(test, configuration, el)
    return params


# This is a very generic "do something with shaping" test runner.
# It'll be given concrete meaning later.
def run_a_set_of_tests(ttFont, run_a_test, test_filter, generate_report):
    filename = Path(ttFont.reader.file.name)
    vharfbuzz = Vharfbuzz(filename)
    shaping_file_found = False
    shaping_basedir = Path("qa", "shaping_tests")
    ran_a_test = False
    for shaping_file in shaping_basedir.glob("*.json"):
        shaping_file_found = True
        try:
            shaping_input_doc = json.loads(shaping_file.read_text())
        except Exception as e:
            yield FAIL, (f"{shaping_file}: Invalid JSON: {e}.")
            return

        configuration = shaping_input_doc.get("configuration", {})
        try:
            shaping_tests = shaping_input_doc["tests"]
        except KeyError:
            yield FAIL, (f"{shaping_file}: Must have an 'tests' key dict.")
            return

        failed_tests = []
        for test in shaping_tests:
            if not test_filter(test, configuration):
                continue
            try:
                shaping_text = test["input"]
            except KeyError as e:
                yield FAIL, (f"{shaping_file}: 'input' key dict is missing from test.")
                return

            exclude_fonts = test.get("exclude", [])
            if basename(filename) in exclude_fonts:
                continue

            only_fonts = test.get("only")
            if only_fonts and basename(filename) not in only_fonts:
                continue

            run_a_test(filename, vharfbuzz, test, configuration, failed_tests)
            ran_a_test = True

        if ran_a_test:
            if not failed_tests:
                yield PASS, f"{shaping_file}: No regression detected"
                return
            else:
                yield from generate_report(shaping_file, failed_tests)

    if not shaping_file_found:
        yield SKIP, "No test files found."
    if not ran_a_test:
        yield SKIP, "No applicable tests ran."


# Do shaping results match expectations?


@check(id="com.google.fonts/check/shaping/regression")
def com_google_fonts_check_shaping_regression(ttFont):
    """Check that texts shape as per expectation"""
    yield from run_a_set_of_tests(
        ttFont,
        run_shaping_regression,
        lambda test, configuration: "expectation" in test,
        gereate_shaping_regression_report,
    )


def run_shaping_regression(filename, vharfbuzz, test, configuration, failed_tests):
    shaping_text = test["input"]
    parameters = get_shaping_parameters(test, configuration)
    output_buf = vharfbuzz.shape(shaping_text, parameters)
    expectation = test["expectation"]
    if isinstance(expectation, dict):
        expectation = expectation.get(filename.name, expectation["default"])
    output_serialized = vharfbuzz.serialize_buf(
        output_buf, glyphsonly="+" not in expectation
    )

    if output_serialized != expectation:
        failed_tests.append((test, expectation, output_buf, output_serialized))


def gereate_shaping_regression_report(shaping_file, failed_tests):
    report_items = []
    for test, expected, output_buf, output_serialized in failed_tests:
        # Make HTML report here.
        report_items.append(
            f" * Input '{test['input']}'\n"
            f"   expected: {expected}\n"
            f"   got: {output_serialized}"
        )

    yield FAIL, (
        f"{shaping_file}: Expected and actual shaping not matching.\n"
        + "\n".join(report_items)
    )


# Are there any naughty glyphs?


@check(id="com.google.fonts/check/shaping/forbidden")
def com_google_fonts_check_shaping_forbidden(ttFont):
    """Check that no forbidden glyphs are found while shaping"""
    yield from run_a_set_of_tests(
        ttFont,
        run_forbidden_glyph_test,
        lambda test, configuration: "forbidden_glyphs" in configuration,
        forbidden_glyph_test_results,
    )


def run_forbidden_glyph_test(filename, vharfbuzz, test, configuration, failed_tests):
    is_stringbrewer = (
        get_from_test_with_default(test, configuration, "input_type", "string")
        == "pattern"
    )
    parameters = get_shaping_parameters(test, configuration)
    forbidden_glyphs = configuration["forbidden_glyphs"]
    if is_stringbrewer:
        sb = StringBrewer(
            recipe=test["input"], ingredients=configuration["ingredients"]
        )
        strings = sb.generate_all()
    else:
        strings = [test["input"]]

    for shaping_text in strings:
        output_buf = vharfbuzz.shape(shaping_text, parameters)
        output_serialized = vharfbuzz.serialize_buf(output_buf, glyphsonly=True)
        glyph_names = output_serialized.split("|")
        for forbidden in forbidden_glyphs:
            if forbidden in glyph_names:
                failed_tests.append((shaping_text, output_serialized, forbidden))


def forbidden_glyph_test_results(shaping_file, failed_tests):
    report_items = []
    for shaping_text, output_serialized, forbidden in failed_tests:
        # Make HTML report here.
        report_items.append(
            f"      * {shaping_text} produced '{forbidden}'\n       {output_serialized}"
        )

    yield FAIL, (
        f"{shaping_file}: Forbidden glyphs found while shaping.\n"
        + "\n".join(report_items)
    )


# Are there any collisions?


@check(id="com.google.fonts/check/shaping/collides")
def com_google_fonts_check_shaping_collides(ttFont):
    """Check that no collisions are found while shaping"""
    yield from run_a_set_of_tests(
        ttFont,
        run_collides_glyph_test,
        lambda test, configuration: "collidoscope" in test
        or "collidoscope" in configuration,
        collides_glyph_test_results,
    )


def run_collides_glyph_test(filename, vharfbuzz, test, configuration, failed_tests):
    is_stringbrewer = (
        get_from_test_with_default(test, configuration, "input_type", "string")
        == "pattern"
    )
    parameters = get_shaping_parameters(test, configuration)
    collidoscope_configuration = test.get(
        "collidoscope", configuration.get("collidoscope")
    )
    col = Collidoscope(
        filename, collidoscope_configuration, direction=parameters["direction"] or "LTR"
    )
    if is_stringbrewer:
        sb = StringBrewer(
            recipe=test["input"], ingredients=configuration["ingredients"]
        )
        strings = sb.generate_all()
    else:
        strings = [test["input"]]

    for shaping_text in strings:
        output_buf = vharfbuzz.shape(shaping_text, parameters)
        glyphs = col.get_glyphs(shaping_text, buf=output_buf)
        collisions = col.has_collisions(glyphs)
        if collisions:
            bumps = [f"{c.glyph1}/{c.glyph2}" for c in collisions]
            failed_tests.append((shaping_text, bumps))


def collides_glyph_test_results(shaping_file, failed_tests):
    report_items = []
    seen_bumps = {}
    for shaping_text, bumps in failed_tests:
        # Make HTML report here.
        if tuple(bumps) in seen_bumps:
            continue
        seen_bumps[tuple(bumps)] = True
        report_items.append(
            f"      * {',' .join(bumps)} collision found in e.g. '{shaping_text}'"
        )

    yield FAIL, (
        f"{shaping_file}: Collisions found while shaping.\n" + "\n".join(report_items)
    )


profile.auto_register(globals())
profile.test_expected_checks(PROFILE_CHECKS, exclusive=True)
