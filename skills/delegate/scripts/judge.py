#!/usr/bin/env python3
"""Bounded evidence judge; host answers are supplied, never generated here. It makes no network call.

The Jev judge was retired by owner decision of 26/11/2026: the small host model is the only judge.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
LIMIT = 65536
ANSWERS = ("yes", "no", "insufficient")
# At most 24 known cases in one validation run.
CASE_LIMIT = 24
MIN_QUOTE = 8
# Closed input fields for each judgment site; caps are UTF-8 bytes.
SITE_SCHEMAS = {
    "verification": {"question": 4096, "evidence": 49152},
    "navigator": {"question": 2048, "evidence": 16384},
    "compaction": {"question": 1024, "evidence": 4096},
    "delegation": {"question": 2048, "evidence": 8192},
}
# Sites that weigh two to six closed options; (fewest, most, bytes per option). An away evaluation gives the
# probability of each option to the deciders as data and never settles the choice (docs/specs/afk-per-project.md C).
CHOICE_SITES = {
    "away-evaluation": {"question": 2048, "options": (2, 6, 512), "evidence": 16384},
}
TABLE_SOURCES = ("host-small",)
RETIRED = "judge: Jev is retired (owner decision, 26/11/2026); the small host model judges"
TABLE_LIMIT = 4096


SECRET_PATTERNS = [(name, re.compile(pattern)) for name, pattern in (
    ("private-key-header", r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----"),
    ("access-key-id", r"\bAKIA[A-Z0-9]{16}\b"),
    ("github-token", r"\b(?:gh[posur]_|github_pat_)[A-Za-z0-9_]+"),
    ("api-key", r"\bsk-[A-Za-z0-9_-]{20,}"),
    ("npm-token", r"\bnpm_[A-Za-z0-9]{36,}\b"),
    ("gitlab-token", r"\bglpat-[A-Za-z0-9_-]{20,}"),
    ("google-api-key", r"\bAIza[A-Za-z0-9_-]{35}(?![A-Za-z0-9_-])"),
    ("stripe-key", r"\b[rs]k_live_[A-Za-z0-9]{20,}"),
    ("jwt", r"\beyJ[A-Za-z0-9_-]{7,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    ("slack-token", r"\bxox[bp]-[A-Za-z0-9-]+"),
    ("secret-assignment", r'''(?i)\b\w*(?:password|passwd|secret|token|api_key|apikey|credential|_pass)\w{0,40}["']?\s*[:=]\s*["']?[^\s"']{8,}'''),
    ("bearer-token", r"(?i)\bAuthorization:\s*Bearer\s+[^\s]{20,}"),
    ("url-credentials", r"\b[A-Za-z][A-Za-z0-9+.-]*://[^\s/:@]+:[^\s/@]+@[^\s/]+"),
)]
MACHINE_PATH = re.compile(r"""/Users/|(?<![A-Za-z0-9.-])/home/|(?<![A-Za-z0-9./-])/(?:var/home|usr/home|root|private|tmp|etc|opt|Volumes)(?=/|\b)|(?<![\w/~])~(?:[A-Za-z_][\w.-]*)?(?=/|\b)|(?<![A-Za-z])[A-Za-z]:[\\/]""")


class Unavailable(ValueError):
    """The payload failed its screening, or no host answer was supplied; the caller uses the small host judge."""


def read_text(path, limit=LIMIT):
    with open(path, "rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("input too large")
    return raw.decode("utf-8")


def result(answer="insufficient", source="host", p=None, quote_ok=None):
    return dict(answer=answer, source=source, p=p, quote_ok=quote_ok)


def check_host(answers, evidence, question=None):
    if (not isinstance(answers, dict) or answers.get("answer") not in ANSWERS
            or set(answers) - {"answer", "quote", "evidence_sha256", "question"}):
        raise ValueError("invalid host answer")
    # Optional bindings are mandatory for verify_claim's persisted answer packets.
    if ("evidence_sha256" in answers and answers["evidence_sha256"] !=
            hashlib.sha256(evidence.encode()).hexdigest()):
        return result(quote_ok=False)
    if "question" in answers and answers["question"] != question:
        return result(quote_ok=False)
    answer = answers["answer"]
    quote = answers.get("quote")
    valid = (isinstance(quote, str) and len(quote.strip()) >= MIN_QUOTE
             and sum(c.isalnum() for c in quote) >= MIN_QUOTE and quote in evidence)
    if answer == "yes":
        return result("yes" if valid else "insufficient", quote_ok=valid)
    return result(answer)


def site_fields(site, fields):
    schema = SITE_SCHEMAS.get(site)
    if schema is None or not isinstance(fields, dict) or set(fields) != set(schema):
        raise Unavailable("payload schema")
    for name, cap in schema.items():
        value = fields[name]
        if not isinstance(value, str) or len(value.encode()) > cap or (name == "question" and not value.strip()):
            raise Unavailable("field: " + name)
        if MACHINE_PATH.search(value) or any(rx.search(value) for _, rx in SECRET_PATTERNS):
            raise Unavailable("field: " + name)
    return fields


def payload(question, evidence, site="verification"):
    """The screened fields the small host model is given for one site."""
    fields = site_fields(site, {"question": question, "evidence": evidence})
    if len(json.dumps(fields).encode()) > LIMIT:
        raise Unavailable("payload size")
    return fields


def sensitive(value):
    return bool(MACHINE_PATH.search(value) or any(rx.search(value) for _, rx in SECRET_PATTERNS))


SENSITIVE_NAME = re.compile(r"KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|SESSIONID|SESSID|(?:^|_)(?:PASS|PASSWD|PASSPHRASE|AUTH|COOKIE|COOKIES|SESSION|PRIVATE)(?:_|$)", re.I)
# Matches only from the start of a candidate name, so a long text with no separator stays linear.
ASSIGNED = re.compile(r"""(?<![^\s=:,'"{}\[\]])([^\s=:,'"{}\[\]]+)['"]?\s*[=:]""")


def assigns_sensitive(value):
    """A sensitive name followed by `=` or `:`, whatever comes next: values have too many shapes to parse safely."""
    return any(SENSITIVE_NAME.search(match[1]) for match in ASSIGNED.finditer(value))


def choice_fields(site, question, options, evidence):
    schema = CHOICE_SITES.get(site)
    if schema is None:
        raise Unavailable("payload schema")
    for name, value in (("question", question), ("evidence", evidence)):
        if (not isinstance(value, str) or len(value.encode()) > schema[name]
                or (name == "question" and not value.strip()) or sensitive(value) or assigns_sensitive(value)):
            raise Unavailable("field: " + name)
    fewest, most, cap = schema["options"]
    if (not isinstance(options, list) or not fewest <= len(options) <= most
            or any(not isinstance(o, str) or not o.strip() or len(o.encode()) > cap or sensitive(o) or assigns_sensitive(o) for o in options)
            or len(set(options)) != len(options)):
        raise Unavailable("field: options")
    return {str(n): option for n, option in enumerate(options, 1)}


def choice_payload(question, options, evidence, site="away-evaluation"):
    """The screened question, numbered options and evidence the small host model weighs."""
    keyed = choice_fields(site, question, options, evidence)
    fields = {"question": question, "options": keyed, "evidence": evidence}
    if len(json.dumps(fields).encode()) > LIMIT:
        raise Unavailable("payload size")
    return fields


def check_table(table, of):
    """The closed table shape: source, k equal to the options, one probability in 0 to 1 per option."""
    if (not isinstance(table, dict) or set(table) != {"source", "of", "probabilities"}
            or table["source"] not in TABLE_SOURCES or type(table["of"]) is not int or table["of"] != of
            or not 2 <= of <= 6 or not isinstance(table["probabilities"], list) or len(table["probabilities"]) != of):
        raise ValueError("table shape")
    for value in table["probabilities"]:
        if type(value) not in (float, int) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("table value")
    return dict(source=table["source"], of=of, probabilities=[float(v) for v in table["probabilities"]])


def configured_judge():
    """Always the host model since Jev was retired (owner decision, 26/11/2026)."""
    return "host"


def matrix_names_jev():
    """Whether a valid, consented assignment matrix still records `Judge: jev`; any failure reads as no."""
    try:
        import data_root as dr
        import assignments
        matrix = assignments.parse(dr.read_data("host.md").decode("utf-8"))
        return matrix.state == "valid" and matrix.consent == "yes" and matrix.judge == "jev"
    except (ImportError, OSError, ValueError, UnicodeError, KeyError, TypeError):
        return False


def judge_source(requested):
    """The judge to use: always `host`; a requested or recorded Jev prints the retirement line once."""
    if requested == "jev" or (requested is None and matrix_names_jev()):
        print(RETIRED, file=sys.stderr)
    return "host"


def validate_cases(cases, source, answers):
    """One harness for either judge, over the same caller-supplied known cases.

    This returns agreement data to the coordinator, never plugin state or events.
    A real measurement needs cases from independent authors, not these unit fixtures.
    """
    if (source != "host" or not isinstance(cases, list)
            or not 1 <= len(cases) <= CASE_LIMIT or not isinstance(answers, dict)):
        raise ValueError("invalid validation cases")
    rows, counts, seen = [], dict(agree=0, insufficient=0, wrong=0), set()
    for case in cases:
        if (not isinstance(case, dict) or set(case) != {"id", "question", "evidence", "expected"}
                or not isinstance(case["id"], str) or not case["id"] or len(case["id"]) > 64
                or case["id"] in seen or case["expected"] not in ANSWERS
                or not isinstance(case["evidence"], str)):
            raise ValueError("invalid validation case")
        seen.add(case["id"])
        if (not isinstance(case["question"], str) or not case["question"].strip()
                or len(case["question"].encode()) > 4096 or len(case["evidence"].encode()) > LIMIT):
            raise ValueError("invalid validation case")
        out = check_host(answers.get(case["id"], dict(answer="insufficient")), case["evidence"], case["question"])
        out["fallback"] = False
        verdict = "agree" if out["answer"] == case["expected"] else "insufficient" if out["answer"] == "insufficient" else "wrong"
        counts[verdict] += 1
        rows.append(dict(id=case["id"], expected=case["expected"], **out))
    return dict(source="host", requested_source=source, fallback=False,
                validation="unvalidated", counts=counts, cases=rows)

def choose(args, evidence):
    """An evaluation site: the host's small model writes the table and check-table checks it; this only screens."""
    if args.site not in CHOICE_SITES or args.answers is not None:
        raise ValueError("options belong to a choice site only")
    options = args.option or []
    if args.dry_run:
        body = choice_payload(args.question, options, evidence, args.site)
        print(json.dumps({"fields": {key: len(json.dumps(value).encode()) for key, value in body.items()}}))
        return 0
    judge_source(args.judge)
    choice_payload(args.question, options, evidence, args.site)
    print("host judge: write the host-small table and run check-table", file=sys.stderr)
    print(json.dumps(dict(source="host-small", of=len(options), probabilities=None)))
    return 3


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    sub = parser.add_subparsers(dest="command", required=True)
    ask = sub.add_parser("ask", allow_abbrev=False)
    ask.add_argument("--question", required=True)
    ask.add_argument("--evidence-file", required=True)
    ask.add_argument("--judge", choices=("jev", "host"), help="jev is retired and reads as host")
    ask.add_argument("--answers", help="host-produced JSON answer file")
    ask.add_argument("--dry-run", action="store_true")
    ask.add_argument("--site", choices=(*SITE_SCHEMAS, *CHOICE_SITES), default="verification")
    ask.add_argument("--option", action="append", help="one closed option of a choice site; repeat 2 to 6 times")
    check = sub.add_parser("check-host", allow_abbrev=False)
    check.add_argument("--answers", required=True)
    check.add_argument("--evidence-file", required=True)
    check.add_argument("--question")
    table = sub.add_parser("check-table", allow_abbrev=False)
    table.add_argument("--file", required=True, help="evaluation table JSON written by the small host model")
    table.add_argument("--of", required=True, type=int, choices=range(2, 7), help="how many options were weighed")
    validate = sub.add_parser("validate", allow_abbrev=False)
    validate.add_argument("--cases", required=True, help="known cases JSON; same file for either judge")
    validate.add_argument("--judge", choices=("jev", "host"), help="jev is retired and reads as host")
    validate.add_argument("--answers", help="host answers JSON keyed by case id")
    args = parser.parse_args()
    try:
        if args.command == "validate":
            cases = json.loads(read_text(args.cases, 2 * 1024 * 1024))
            answers = json.loads(read_text(args.answers, 2 * 1024 * 1024)) if args.answers else {}
            report = validate_cases(cases, judge_source(args.judge), answers)
            print(json.dumps(report, allow_nan=False))
            return 0
        if args.command == "check-table":
            print(json.dumps(check_table(json.loads(read_text(args.file, TABLE_LIMIT)), args.of), allow_nan=False))
            return 0
        evidence = read_text(args.evidence_file)
        if args.command == "ask" and (args.site in CHOICE_SITES or args.option is not None):
            return choose(args, evidence)
        if args.command == "check-host":
            out = check_host(json.loads(read_text(args.answers)), evidence, args.question)
        else:
            if args.dry_run:
                body = payload(args.question, evidence, args.site)
                print(json.dumps({"fields": {key: len(json.dumps(value).encode()) for key, value in body.items()}}))
                return 0
            judge_source(args.judge)
            payload(args.question, evidence, args.site)
            if args.answers:
                out = check_host(json.loads(read_text(args.answers)), evidence, args.question)
            else:
                print("unavailable: host answer required; use check-host after the small host model answers", file=sys.stderr)
                print(json.dumps(result()))
                return 3
        print(json.dumps(out, allow_nan=False))
        return 0
    except Unavailable as error:
        print("unavailable: " + str(error) + "; use the small host judge with the same payload", file=sys.stderr)
        print(json.dumps(dict(result(), fallback=True)))
        return 3
    except (OSError, ValueError, UnicodeError):
        print("judge: invalid input", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
