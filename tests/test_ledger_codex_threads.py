"""Tests for the Codex session digest in skills/delegate/scripts/ledger.py (`finish` and `codex-threads`)."""

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.data_root_fixture import account

LEDGER = Path(__file__).resolve().parent.parent / "skills/delegate/scripts/ledger.py"
ONE = "01a1cda1-c953-7e60-8015-d3de3e5b0a08"
TWO = "01a21dff-709a-7100-945b-8819b75223a9"


def digest(session):
    return hashlib.sha256(session.encode()).hexdigest()[:16]


class CodexThreadTest(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parent.parent / ".finolabs" / "tmp"
        scratch.mkdir(parents=True, exist_ok=True)
        self.dir = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.dir.cleanup)
        base = Path(self.dir.name).resolve()
        base.chmod(0o755)
        self.home = account(self, base / "home")
        self.path = self.home / ".finolabs/vibecode/ledger.jsonl"
        self.path.parent.mkdir(parents=True, mode=0o700)
        self.home.joinpath(".finolabs").chmod(0o700)
        self.logs = base / "work" / ".finolabs" / "logs"
        self.codex = base / "codex-home"
        spec = importlib.util.spec_from_file_location("codex_thread_ledger", LEDGER)
        self.ledger = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.ledger)
        import log_scan
        for patch in (mock.patch.object(log_scan, "run_log_folder", return_value=self.logs),
                      mock.patch.object(self.ledger, "this_project", return_value="demo"),
                      mock.patch.dict(os.environ, {"FNL_WORKTREE_CLEAN": "manual", "CODEX_HOME": str(self.codex)})):
            patch.start()
            self.addCleanup(patch.stop)

    def call(self, *argv):
        args = self.ledger.build_parser().parse_args(list(argv))
        out, err = io.StringIO(), io.StringIO()
        code = 0
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                args.func(args)
            except SystemExit as error:
                code = error.code
        return code, out.getvalue(), err.getvalue()

    def write(self, records):
        self.path.write_text("".join(json.dumps(r) + "\n" for r in records))
        self.path.chmod(0o600)

    def records(self):
        return [json.loads(line) for line in self.path.read_text().splitlines()]

    def start(self, ident, agent="codex", project="demo", ts="2026-11-10T01:00:00+00:00"):
        return {"event": "start", "id": ident, "ts": ts, "project": project, "task": "t", "kind": "review",
                "grade": "easy", "coordinator": "claude", "agent": agent, "model": "m", "reason": "routing",
                "budget_min": 30}

    def done(self, ident, outcome="accepted", ts="2026-11-10T01:20:00+00:00", **extra):
        return {"event": "finish", "id": ident, "ts": ts, "outcome": outcome, "rework_rounds": 0, "tests": "not-run",
                "note": "", "log_scan": "no_findings", **extra}

    def log(self, name, text):
        self.logs.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.logs.chmod(0o700)
        path = self.logs / name
        path.write_text(text)
        path.chmod(0o600)
        return path

    def finish(self, ident, log):
        return self.call("finish", ident, "--outcome", "rejected", "--log-path", str(log))

    def session_file(self, day, session, suffix=".jsonl"):
        folder = self.codex / "sessions" / day
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"rollout-{day.replace('/', '-')}T01-00-00-{session}{suffix}"
        path.write_text("{}\n")
        return path

    # finish

    def test_a_codex_log_header_stores_only_the_digest(self):
        self.write([self.start("d1")])
        log = self.log("d1.log", f"OpenAI Codex v0.169.0\n--------\nworkdir: /w\nsession id: {ONE}\n--------\nok\n")
        code, _, err = self.finish("d1", log)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.records()[-1]["codex_thread"], digest(ONE))
        self.assertNotIn(ONE, self.path.read_text())
        self.assertNotIn(ONE, err)

    def test_a_json_event_stream_stores_the_thread_digest(self):
        self.write([self.start("d1")])
        log = self.log("d1.log", json.dumps({"type": "thread.started", "thread_id": ONE}) + "\n"
                       + json.dumps({"type": "turn.completed"}) + "\n")
        code, _, err = self.finish("d1", log)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.records()[-1]["codex_thread"], digest(ONE))

    def test_the_same_id_twice_is_one_session(self):
        self.write([self.start("d1")])
        log = self.log("d1.log", f"session id: {ONE}\n" + json.dumps({"type": "thread.started", "thread_id": ONE}))
        self.assertEqual(self.finish("d1", log)[0], 0)
        self.assertEqual(self.records()[-1]["codex_thread"], digest(ONE))

    def test_no_digest_for_two_ids_no_id_another_agent_or_no_log(self):
        cases = (("two", "codex", f"session id: {ONE}\nsession id: {TWO}\n"),
                 ("none", "codex", "ordinary output\n"),
                 ("other", "claude", f"session id: {ONE}\n"),
                 ("upper", "codex", f"session id: {ONE.upper()}\n"))
        for ident, agent, text in cases:
            with self.subTest(case=ident):
                self.write([self.start(ident, agent=agent)])
                code, _, err = self.finish(ident, self.log(ident + ".log", text))
                self.assertEqual(code, 0, err)
                self.assertNotIn("codex_thread", self.records()[-1])
        self.write([self.start("bare")])
        self.assertEqual(self.call("finish", "bare", "--outcome", "rejected")[0], 0)
        self.assertNotIn("codex_thread", self.records()[-1])

    # codex-threads

    def test_lists_the_archive_command_of_each_saved_session_it_finds(self):
        self.write([self.start("d1"), self.done("d1", codex_thread=digest(ONE)),
                    self.start("d2"), self.done("d2", codex_thread=digest(TWO))])
        self.session_file("2026/11/10", ONE)
        before = self.path.read_bytes()
        code, out, err = self.call("codex-threads")
        self.assertEqual(code, 0, err)
        self.assertEqual(out.splitlines(), [f"codex archive {ONE}  # d1 demo: t",
                                            "1 accepted Codex dispatch has no saved session to archive"])
        self.assertEqual(self.path.read_bytes(), before)

    def test_only_accepted_codex_dispatches_of_this_project_count(self):
        self.write([self.start("d1"), self.done("d1", outcome="rejected", codex_thread=digest(ONE)),
                    self.start("d2", project="other"), self.done("d2", codex_thread=digest(TWO)),
                    self.start("d3"), self.done("d3")])
        self.session_file("2026/11/10", ONE)
        self.session_file("2026/11/10", TWO)
        code, out, err = self.call("codex-threads")
        self.assertEqual(code, 0, err)
        self.assertEqual(out.splitlines(), ["No accepted Codex dispatch with a recorded session"])

    def test_dispatch_narrows_the_list(self):
        self.write([self.start("d1"), self.done("d1", codex_thread=digest(ONE)),
                    self.start("d2"), self.done("d2", codex_thread=digest(TWO))])
        self.session_file("2026/11/10", ONE)
        self.session_file("2026/11/11", TWO, ".jsonl.zst")
        code, out, _ = self.call("codex-threads", "--dispatch", "d2")
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), [f"codex archive {TWO}  # d2 demo: t"])

    def test_links_other_days_and_other_names_are_not_matched(self):
        self.write([self.start("d1"), self.done("d1", codex_thread=digest(ONE))])
        real = self.session_file("2026/11/20", ONE)  # outside the dispatch's days
        link = self.codex / "sessions/2026/11/10"
        link.mkdir(parents=True)
        (link / real.name).symlink_to(real)
        (link / f"notes-{ONE}.jsonl").write_text("{}\n")
        code, out, _ = self.call("codex-threads")
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), ["1 accepted Codex dispatch has no saved session to archive"])

    def test_a_missing_codex_home_finds_nothing_and_fails_nothing(self):
        self.write([self.start("d1"), self.done("d1", codex_thread=digest(ONE))])
        code, out, _ = self.call("codex-threads")
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), ["1 accepted Codex dispatch has no saved session to archive"])

    def test_an_unknown_dispatch_is_refused(self):
        self.write([self.start("d1"), self.done("d1", codex_thread=digest(ONE))])
        code, _, _ = self.call("codex-threads", "--dispatch", "d9")
        self.assertEqual(code, "ledger: no accepted Codex dispatch d9 in this project")


if __name__ == "__main__":
    unittest.main()
