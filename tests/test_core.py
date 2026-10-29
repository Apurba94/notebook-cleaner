import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from notebook_cleaner.cli import main
from notebook_cleaner.core import clean_notebook, is_clean, scan_secrets, stats

NB = {
    "nbformat": 4, "nbformat_minor": 5,
    "metadata": {"kernelspec": {"name": "python3"}, "language_info": {"name": "python"},
                 "widgets": {"state": {"big": "x" * 100}}, "toc": {"x": 1}},
    "cells": [
        {"cell_type": "markdown", "metadata": {"collapsed": True}, "source": ["# Title"]},
        {"cell_type": "code", "execution_count": 7, "metadata": {"tags": ["parameters"], "ExecuteTime": {}},
         "source": ["api_key = 'abcd1234efgh5678'\n", "print(1)"],
         "outputs": [{"output_type": "stream", "name": "stdout", "text": ["1\n"]},
                     {"output_type": "execute_result", "execution_count": 7, "data": {"text/plain": ["2"]}}]},
        {"cell_type": "code", "execution_count": 3, "metadata": {}, "source": "", "outputs": []},
    ],
}


class CleanTests(unittest.TestCase):
    def test_default_clean(self):
        c = clean_notebook(NB)
        self.assertEqual(set(c["metadata"]), {"kernelspec", "language_info"})
        code = c["cells"][1]
        self.assertEqual((code["outputs"], code["execution_count"]), ([], None))
        self.assertEqual(code["metadata"], {"tags": ["parameters"]})
        self.assertEqual(c["cells"][0]["metadata"], {})
        self.assertEqual(NB["cells"][1]["execution_count"], 7)        # original untouched
        self.assertTrue(is_clean(c))
        self.assertFalse(is_clean(NB))

    def test_keep_outputs_with_size_limit(self):
        c = clean_notebook(NB, keep_outputs=True, max_output_kb=0.06)
        self.assertEqual(len(c["cells"][1]["outputs"]), 1)
        self.assertIsNone(clean_notebook(NB, keep_outputs=True)["cells"][1]["outputs"][1]["execution_count"])

    def test_drop_tags(self):
        self.assertEqual(clean_notebook(NB, keep_tags=False)["cells"][1]["metadata"], {})

    def test_secrets_and_stats(self):
        hits = scan_secrets(NB)
        self.assertEqual([(i, k) for i, k, _ in hits], [(1, "api-key-assignment")])
        self.assertNotIn("abcd1234efgh5678", hits[0][2])
        s = stats(NB)
        self.assertEqual((s["code_cells"], s["out_of_order"], s["empty_code_cells"]), (2, True, 1))

    def test_cli_check_and_clean(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "a.ipynb")
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(NB, fh)
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(main([p, "--check"]), 1)
                self.assertEqual(main([p]), 0)
                self.assertEqual(main([p, "--check"]), 0)
                self.assertEqual(main([p, "--secrets"]), 1)


if __name__ == "__main__":
    unittest.main()
