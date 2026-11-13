"""Summarize completed human review CSVs; never infer or fabricate labels."""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def summarize_human(directory):
    directory = Path(directory)
    output = {}
    for name, field in [("coherence", "score_0_2"), ("grounding", "score_0_2"), ("metadata", "human_correct")]:
        with (directory / f"audit_{name}.csv").open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        pending = [r for r in rows if r.get("status") != "human_reviewed" or not r.get("reviewer", "").strip()
                   or not r.get("reason", "").strip() or r.get(field, "") == ""]
        if pending:
            raise ValueError(f"{name}: {len(pending)} records still pending human review")
        groups = defaultdict(list)
        for row in rows:
            value = int(row[field])
            if value not in ({0, 1} if name == "metadata" else {0, 1, 2}):
                raise ValueError(f"Invalid {name} label")
            groups[row["strategy"]].append((row, value))
        output[name] = {}
        for strategy, records in groups.items():
            if name == "coherence":
                locations = defaultdict(list)
                for row, value in records:
                    locations[(row["page"], row["anchor"])].append(value)
                values = [sum(v) / len(v) for v in locations.values()]
                output[name][strategy] = {"source_locations": len(values), "chunks": len(records), "mean": sum(values) / len(values)}
            else:
                values = [value for _, value in records]
                output[name][strategy] = {"n": len(values), "sum": sum(values), "mean": sum(values) / len(values),
                                         "counts": {str(i): values.count(i) for i in range(3 if name == "grounding" else 2)}}
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    result = summarize_human(args.directory)
    (args.directory / "human_audit_summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
