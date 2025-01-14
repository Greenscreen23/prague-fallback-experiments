from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

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
    "--n-ddp",
    default=2,
    help="The buffer size multiplyer. The final buffer size will be n-ddp times the data rate delay product.",
    type=float,
)
parser.add_argument(
    "-b",
    "--ecn-fallback",
    default=1,
    help="Whether ECN fallback should be on (1) or off (0)",
)
parser.add_argument(
    "-i", "--iterations", default=1, help="The number of iterations to run", type=int
)
parser.add_argument(
    "-t", "--duration", default=60, help="The duration of each test in s", type=int
)
parser.add_argument(
    "-c",
    "--cli",
    default=False,
    action="store_true",
    help="Run a CLI before the experiment",
)
parser.add_argument(
    "-s",
    "--skip-experiment",
    default=False,
    action="store_true",
    help="Skip the experiment (useful in combination with --cli)",
)
parser.add_argument(
    "-a",
    "--aqm",
    default="DualPI2",
    choices=["DualPI2", "FIFO", "FIFO (ECN)", "CoDel", "FQ", "FQ-CoDel"],
    help="The AQM to use",
)
parser.add_argument(
    "-g",
    "--trace-prague",
    nargs="+",
    help="Launch the given file with bpftrace",
)
parser.add_argument(
    "-p",
    "--create-pcap",
    default=False,
    action="store_true",
    help="Create a pcap file with the entire traffic.",
)
parser.add_argument(
    "-C",
    "--disable-cubic",
    default=False,
    action="store_true",
    help="Disable the cubic flow",
)
parser.add_argument(
    "-N",
    "--disable-nagle",
    default=False,
    action="store_true",
    help="Disable the nagles algorithm flow",
)
parser.add_argument(
    "-q",
    "--quickack",
    default=False,
    action="store_true",
    help="Enable quickack on all interfaces",
)
args = parser.parse_args()
