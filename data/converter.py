from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import pandas as pd
from pathlib import Path
import json

parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("-f", "--folder", help="Where to look for input files")
parser.add_argument("-o", "--output", help="Where to write the output csv")
parser.add_argument("-c", "--columns", nargs="+", help="The names of columns")
parser.add_argument(
    "-s",
    "--strip",
    nargs="+",
    help="We sometimes added a character preceding a number to hint which value this is. You may specify these columns here so the converter strips this character.",
)
args = parser.parse_args()

folder = Path(args.folder)
rows = []
for path in folder.glob("*/" * len(args.columns)):
    row = [
        part[1:] if col in args.strip else part
        for part, col in zip(path.relative_to(folder).parts, args.columns)
    ]

    file = path / "prague-results.json"
    with file.open() as f:
        data = json.load(f)
    row.append(data["server_output_json"]["end"]["sum_received"]["bits_per_second"])

    file = path / "classic-results.json"
    with file.open() as f:
        data = json.load(f)
    row.append(data["server_output_json"]["end"]["sum_received"]["bits_per_second"])

    file = path / "router-rx-stats.json"
    if file.exists():
        with file.open() as f:
            data = json.load(f)
        row.append(data[0]["drops"])
    else:
        row.append(None)

    file = path / "trace-classic-ecn.bt-results.ndjson"
    if file.exists():
        with file.open() as f:
            data = {}
            for line in f:
                data |= json.loads(line)["data"]
        row.append(data["@classic"])
        row.append(data["@transition"])
        row.append(data["@scalable"])
    else:
        row += [None] * 3

    rows.append(row)

df = pd.DataFrame(
    rows,
    columns=args.columns
    + [
        "prague throughput",
        "classic throughput",
        "drops",
        "classic",
        "transition",
        "scalable",
    ],
)

df.to_csv(args.output, index=False)
