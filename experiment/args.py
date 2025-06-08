from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

AQMS = ["DualPI2", "FIFO", "FIFO (ECN)", "CoDel", "FQ", "FQ-CoDel"]

parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument(
    "-f", "--folder", help="Destination folder for output files", default="."
)
parser.add_argument("-d", "--delay", default=10, help="RTT in ms", type=int)
parser.add_argument("-r", "--rate", default=100, help="Data rate in Mbps", type=int)
parser.add_argument(
    "-e", "--ecn-threshold", default=5, help="ECN threshold of DualPI2 in ms", type=int
)
parser.add_argument(
    "-n",
    "--n-bdp",
    default=2,
    help="The buffer size multiplyer. The final buffer size will be n-bdp times the bandwidth delay product.",
    type=float,
)
parser.add_argument(
    "-b",
    "--ecn-fallback",
    default=1,
    help="Whether ECN fallback should be on (1) or off (0)",
)
parser.add_argument(
    "-t", "--duration", default=60, help="The duration of each test in s", type=int
)
parser.add_argument(
    "-c",
    "--classic-cca",
    default='cubic',
    choices=['cubic', 'bbr2'],
    help="The classic CCA to compete against prague",
)
parser.add_argument(
    "-s",
    "--skip-experiment",
    default=False,
    action="store_true",
    help="Run a CLI and then skip the experiment (useful to validate the current setup)",
)
parser.add_argument(
    "-a",
    "--aqm",
    default="DualPI2",
    choices=AQMS,
    help="The AQM to use",
)
parser.add_argument(
    "-T",
    "--trace",
    nargs="+",
    help="Launch the given file with bpftrace",
)
parser.add_argument(
    "-D",
    "--dropped-packets",
    default=False,
    action="store_true",
    help="Create a router-rx-stats.json file with the number of dropped packets",
)
parser.add_argument(
    "-O",
    "--omit",
    default=0,
    type=int,
    help="The number of seconds to do a pretest, to skip past TCP slow start",
)
parser.add_argument(
    "--tcpdump",
    default=False,
    action='store_true',
    help="Store all packets with tcpdump"
)
args = parser.parse_args()
