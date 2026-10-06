"""Check a Build Broadcast edition against the GitHub record before it is published.

For every change that names a PR, this checks:
  - files / lines added / lines removed / branch match GitHub exactly;
  - "Opened by" and "Merged by" match the PR's author and merger;
  - every time in the story matches a real GitHub event (PR opened, review, comment,
    commit or merge) to the minute, in Lagos time;
  - every quoted phrase appears word for word in the review conversation of some PR
    in the folder (quotes may be cut with "..." and may end where the original goes on).

--prs is a folder holding, for each PR number n, the raw GitHub API responses:
    pr<n>.json   GET repos/{owner}/{repo}/pulls/<n>
    rev<n>.json  GET repos/{owner}/{repo}/pulls/<n>/reviews
    rc<n>.json   GET repos/{owner}/{repo}/pulls/<n>/comments
    ic<n>.json   GET repos/{owner}/{repo}/issues/<n>/comments
    cm<n>.json   GET repos/{owner}/{repo}/pulls/<n>/commits

Exit code 0 means every check passed. Anything else lists what failed.

Usage:
    python3 verify_edition.py --edition edition.json --prs prs/
"""
import argparse, json, re, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

LAGOS = timezone(timedelta(hours=1))   # West Africa Time, no daylight saving
NAMES = {"cogent-demon": "Thomas", "Nahum-qaelum": "Nahum", "Nahum Enebong": "Nahum"}


def who(login):
    return NAMES.get(login or "", "a contributor")


def norm(s):
    s = (s or "").replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-").replace("−", "-")
    return re.sub(r"\s+", " ", s).strip().lower()


def when(iso):
    t = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(LAGOS)
    return f"{t:%a} {t.day} {t:%b}, {t.hour % 12 or 12}:{t:%M} {'am' if t.hour < 12 else 'pm'}"


def load(folder, kind, n):
    p = Path(folder) / f"{kind}{n}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else ([] if kind != "pr" else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edition", required=True)
    ap.add_argument("--prs", required=True)
    a = ap.parse_args()
    ed = json.loads(Path(a.edition).read_text(encoding="utf-8"))
    problems = []

    # Every PR in the folder contributes text and event times, so a quote or event that
    # happened on another PR (a finding made while reviewing a different change) still checks.
    texts, times = [], set()
    for p in sorted(Path(a.prs).glob("pr*.json")):
        n = p.stem[2:]
        pr = load(a.prs, "pr", n)
        texts.append(pr.get("body") or "")
        times.add(when(pr["created_at"]))
        if pr.get("merged_at"):
            times.add(when(pr["merged_at"]))
        for kind, stamp in (("rev", "submitted_at"), ("rc", "created_at"), ("ic", "created_at")):
            for x in load(a.prs, kind, n):
                texts.append(x.get("body") or "")
                if x.get(stamp):
                    times.add(when(x[stamp]))
        for c in load(a.prs, "cm", n):
            texts.append(c["commit"]["message"])
            times.add(when(c["commit"]["committer"]["date"]))
            times.add(when(c["commit"]["author"]["date"]))
    corpus = norm("\n".join(texts))

    for i, c in enumerate(ed.get("changes", []), 1):
        tag = f"change {i} ({c.get('title', '')[:40]})"
        st = c.get("stats") or {}
        n = st.get("pr")
        if n:
            pr = load(a.prs, "pr", n)
            if not pr:
                problems.append(f"{tag}: no GitHub data for PR #{n} in {a.prs}")
                continue
            want = {"files": pr["changed_files"], "added": pr["additions"], "removed": pr["deletions"], "branch": pr["head"]["ref"]}
            for k, v in want.items():
                if k in st and st[k] != v:
                    problems.append(f"{tag}: {k} says {st[k]!r}, GitHub says {v!r}")
            ppl = c.get("people") or {}
            if ppl.get("opened") and ppl["opened"] != who(pr["user"]["login"]):
                problems.append(f"{tag}: opened by {ppl['opened']!r}, GitHub says {who(pr['user']['login'])!r}")
            if pr.get("merged_by") and ppl.get("merged") and ppl["merged"] != who(pr["merged_by"]["login"]):
                problems.append(f"{tag}: merged by {ppl['merged']!r}, GitHub says {who(pr['merged_by']['login'])!r}")
            story = c.get("story") or []
            if story and pr.get("merged_at") and re.match(r"merged", story[-1].get("what", ""), re.I):
                if story[-1].get("when") != when(pr["merged_at"]):
                    problems.append(f"{tag}: merge time says {story[-1].get('when')!r}, GitHub says {when(pr['merged_at'])!r}")
        for s in c.get("story") or []:
            if s.get("when") and s["when"] not in times:
                problems.append(f"{tag}: no GitHub event at {s['when']!r} ({s.get('who')})")
            for q in re.findall(r'"([^"]+)"', s.get("what", "")):
                for part in re.split(r"\.\.\.|…", q):
                    part = part.strip()
                    if part and norm(part) not in corpus:
                        problems.append(f"{tag}: quote not found word for word: {part!r}")

    if problems:
        print(f"{len(problems)} problem(s):")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    print(f"edition {ed.get('number')}: all checks passed ({len(ed.get('changes', []))} changes)")


if __name__ == "__main__":
    main()
