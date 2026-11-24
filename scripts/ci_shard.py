#!/usr/bin/env python3
"""Run one shard of the script suite, as CI does: `python3 scripts/ci_shard.py <index> <count>`.

It discovers `tests/` exactly as `python3 -m unittest discover -s tests` does, splits the
test modules into <count> shards by test count (largest first, each to the lightest shard,
ties by name), and runs shard <index> (1-based). Every module lands in exactly one shard,
so the shards together are the full suite. Exit 0 when the shard passes, 1 otherwise.
"""
import sys
import unittest


def module_name(suite):
    """The test module a discovered top-level suite came from, or None for an empty one."""
    for test in _tests(suite):
        return test.id().split(".", 1)[0]
    return None


def _tests(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _tests(item)
        else:
            yield item


def partition(suites, count):
    """Split (name, suite) pairs into `count` lists, balanced by test count."""
    shards = [[] for _ in range(count)]
    load = [0] * count
    for name, suite in sorted(suites, key=lambda pair: (-pair[1].countTestCases(), pair[0])):
        lightest = load.index(min(load))
        shards[lightest].append((name, suite))
        load[lightest] += suite.countTestCases()
    return shards


def main(argv):
    if len(argv) != 2 or not all(arg.isdigit() for arg in argv) or not 1 <= int(argv[0]) <= int(argv[1]):
        print("usage: ci_shard.py <index> <count>, 1 <= index <= count", file=sys.stderr)
        return 2
    index, count = int(argv[0]), int(argv[1])
    discovered = unittest.defaultTestLoader.discover("tests")
    suites = [(module_name(suite), suite) for suite in discovered if module_name(suite)]
    mine = partition(suites, count)[index - 1]
    print(f"shard {index} of {count}: " + " ".join(name for name, _ in mine), flush=True)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(suite for _, suite in mine))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
