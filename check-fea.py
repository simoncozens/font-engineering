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

# Make FontBakery able to find the update_shaping_test_data package.
sys.path.append(str(Path(__file__).parent.parent))



profile_imports = ()
profile = profile_factory(
    default_section=Section("Shaping Checks")
)

PROFILE_CHECKS = [
    "com.google.fonts/check/shaping/regression",
]

def get_shaping_parameters(test, defaults):
    params = {}
    for el in ["script", "language", "direction", "comparison_mode", "features"]:
        params[el] = test.get(el, defaults.get(el))
    return params


@check(id="com.google.fonts/check/shaping/regression")
def com_google_fonts_check_shaping_regression(ttFont):
    """Check that texts shape as per expectation"""
    filename = Path(ttFont.reader.file.name)
    vharfbuzz = Vharfbuzz(filename)
    shaping_file_found = False
    shaping_basedir = Path("qa", "shaping")
    for shaping_file in shaping_basedir.glob("*.json"):
        shaping_file_found = True
        shaping_input_doc = json.loads(shaping_file.read_text())
        defaults = shaping_input_doc.get("configuration", {}).get("defaults", {})

        try:
            shaping_tests = shaping_input_doc["tests"]
        except KeyError:
            yield FAIL, (f"{shaping_file}: Must have an 'tests' key dict.")
            return

        failed_tests = []
        for test in shaping_tests:
            if "expectation" not in test:  # Not a regression test
                continue

            try:
                shaping_text = test["input"]
            except KeyError as e:
                yield FAIL, (f"{shaping_file}: 'input' key dict is missing from test.")
                return

            if "test_type" in test:
                yield FAIL, (f"{shaping_file}: a regression test ('{shaping_text}') should not have a test type.")
                return

            exclude_fonts = test.get("exclude", [])
            if basename(filename) in exclude_fonts:
                continue

            only_fonts = test.get("only")
            if only_fonts and basename(filename) not in only_fonts:
                continue

            parameters = get_shaping_parameters(test, defaults)
            expectation = test["expectation"]
            if isinstance(expectation, dict):
                try:
                    expectation = expectation.get(filename.name, expectation["default"])
                except KeyError as e:
                    yield FAIL, (f"{shaping_file}: no expectation found for {filename.name}.")
                    return

            output_buf = vharfbuzz.shape(shaping_text, parameters)
            output_serialized = vharfbuzz.serialize_buf(output_buf, glyphsonly="+" not in expectation)

            if output_serialized != expectation:
                failed_tests.append( (test, expectation, output_buf, output_serialized) )

        if not failed_tests:
            yield PASS, f"{shaping_file}: No regression detected"
            continue

        report_items = []
        for test, expected, output_buf, output_serialized in failed_tests:
            # Make HTML report here.
            report_items.append(
                f" * Input '{test['input']}'\n"
                f"   expected: {expected}\n"
                f"   got: {output_serialized}\n"
            )

        yield FAIL, (
            f"{shaping_file}: Expected and actual shaping not matching.\n" + "\n".join(report_items)
        )

    if not shaping_file_found:
        yield SKIP, "No test files found."



# @check(id="com.google.fonts/check/shaping/forbidden")
# def com_google_fonts_check_shaping_forbidden(ttFont):
#     """Check that no forbidden glyphs are found while shaping"""
#     filename = Path(ttFont.reader.file.name)
#     vharfbuzz = Vharfbuzz(filename)
#     shaping_file_found = False
#     shaping_basedir = Path("qa", "shaping")
#     for shaping_file in shaping_basedir.glob("*.json"):


profile.auto_register(globals())
profile.test_expected_checks(PROFILE_CHECKS, exclusive=True)
