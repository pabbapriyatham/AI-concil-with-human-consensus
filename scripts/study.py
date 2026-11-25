"""Prepare and score a local, blinded Mahthildis study."""

import argparse
import json
from pathlib import Path

from app.evaluation.study import ReviewSubmission, calibration_split, prepare_study, score_study


def write_new_json(path, value):
    with path.open("x", encoding="utf8") as output:
        json.dump(value, output, ensure_ascii=False, indent=2)
        output.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("experiment", type=Path)
    prepare.add_argument("output", type=Path, help="New directory for reviewer-packet.json and private-key.json")
    score = commands.add_parser("score")
    score.add_argument("key", type=Path)
    score.add_argument("first", type=Path)
    score.add_argument("second", type=Path)
    score.add_argument("output", type=Path)
    score.add_argument("--adjudication", type=Path)
    calibration = commands.add_parser("calibration")
    calibration.add_argument("train", type=Path)
    calibration.add_argument("test", type=Path)
    calibration.add_argument("output", type=Path)
    calibration.add_argument("--system", choices=["E", "F"], default="F")
    args = parser.parse_args()

    if args.command == "prepare":
        experiment = json.loads(args.experiment.read_text(encoding="utf8"))
        packet, key = prepare_study(experiment)
        args.output.mkdir()
        write_new_json(args.output / "reviewer-packet.json", packet)
        write_new_json(args.output / "private-key.json", key)
        return 0

    if args.command == "calibration":
        train = json.loads(args.train.read_text(encoding="utf8"))
        test = json.loads(args.test.read_text(encoding="utf8"))
        rows = calibration_split(train, test, args.system)
        with args.output.open("x", encoding="utf8") as output:
            for row in rows:
                output.write(json.dumps(row) + "\n")
        return 0

    key = json.loads(args.key.read_text(encoding="utf8"))
    first = ReviewSubmission.model_validate_json(args.first.read_bytes())
    second = ReviewSubmission.model_validate_json(args.second.read_bytes())
    adjudication = ReviewSubmission.model_validate_json(args.adjudication.read_bytes()) if args.adjudication else None
    result = score_study(key, first, second, adjudication)
    write_new_json(args.output, result)
    return 2 if "unresolved_candidate_ids" in result else 0


if __name__ == "__main__":
    raise SystemExit(main())
