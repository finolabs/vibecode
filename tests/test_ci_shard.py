import importlib.util
import pathlib
import re
import tempfile
import unittest
import unittest.mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ci_shard", ROOT / "scripts" / "ci_shard.py")
ci_shard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci_shard)


def fake(count):
    return unittest.TestSuite(unittest.FunctionTestCase(lambda: None) for _ in range(count))


class PartitionTests(unittest.TestCase):
    def test_every_module_lands_in_exactly_one_shard(self):
        suites = [(f"test_{i}", fake(i % 7 + 1)) for i in range(30)]
        for count in (1, 2, 4, 5):
            with self.subTest(count=count):
                shards = ci_shard.partition(suites, count)
                names = [name for shard in shards for name, _ in shard]
                self.assertEqual(sorted(names), sorted(name for name, _ in suites))

    def test_split_is_balanced_and_deterministic(self):
        suites = [("test_a", fake(9)), ("test_b", fake(5)), ("test_c", fake(4)), ("test_d", fake(1))]
        shards = ci_shard.partition(suites, 2)
        self.assertEqual([[name for name, _ in shard] for shard in shards], [["test_a", "test_d"], ["test_b", "test_c"]])
        self.assertEqual(shards, ci_shard.partition(list(reversed(suites)), 2))

    def test_a_module_that_fails_to_import_keeps_its_name(self):
        with tempfile.TemporaryDirectory() as folder:
            (pathlib.Path(folder) / "test_broken.py").write_text("import a_module_that_does_not_exist\n")
            suites = list(unittest.TestLoader().discover(folder))
        self.assertEqual([ci_shard.module_name(suite) for suite in suites], ["test_broken"])

    def test_an_empty_shard_fails(self):
        with unittest.mock.patch.object(ci_shard.unittest.defaultTestLoader, "discover", return_value=unittest.TestSuite()):
            self.assertEqual(ci_shard.main(["1", "1"]), 1)

    def test_bad_arguments_are_refused(self):
        for argv in ([], ["0", "4"], ["5", "4"], ["x", "4"], ["1"]):
            with self.subTest(argv=argv):
                self.assertEqual(ci_shard.main(argv), 2)


class WorkflowTests(unittest.TestCase):
    def test_matrix_runs_every_shard_and_validate_needs_them(self):
        workflow = (ROOT / ".github/workflows/validate.yml").read_text()
        shards = re.search(r"shard: \[([0-9, ]+)\]", workflow).group(1).split(", ")
        count = re.search(r"scripts/ci_shard\.py \"\$\{\{ matrix\.shard \}\}\" (\d+)", workflow).group(1)
        self.assertEqual(shards, [str(i) for i in range(1, int(count) + 1)])
        validate = workflow.split("\n  validate:\n", 1)[1]
        self.assertIn("    if: always()\n", validate)
        self.assertIn("    needs: [checks, tests]\n", validate)
        self.assertIn('[ "$CHECKS" = success ] && [ "$TESTS" = success ]', validate)


if __name__ == "__main__":
    unittest.main()
