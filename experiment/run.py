import os
import time
from subprocess import Popen
from signal import SIGINT

from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel

from args import args
from topo import ExperimentTopo

setLogLevel("info")

if not os.path.exists(args.folder):
    os.makedirs(args.folder)

net = Mininet(topo=ExperimentTopo(cli_args=args))
tx_prague = net.getNodeByName("tx_prague")
rx_prague = net.getNodeByName("rx_prague")
tx_classic = net.getNodeByName("tx_classic")
rx_classic = net.getNodeByName("rx_classic")
router = net.getNodeByName("router")

net.start()
net.pingAll()

if args.skip_experiment:
    CLI(net)
    net.stop()
    exit(0)

processes = []

if args.trace:
    for file in args.trace:
        cmd = [
            "bpftrace",
            file,
            "-o",
            f"{args.folder}/{os.path.basename(file)}-results.ndjson",
            "-f",
            "json",
        ]
        process = Popen(cmd)
        processes.append(process)

if args.tcpdump:
    process = Popen(["tcpdump", "-i", "s2-router", "-w", f"{args.folder}/dump.pcap"])
    processes.append(process)

time.sleep(1)

rx_prague.cmd_check("iperf3 -s -1 -D -J")
rx_classic.cmd_check("iperf3 -s -1 -D -J")

time.sleep(1)

tx_classic.sendCmd_check(
    f"iperf3 -c {rx_classic.IP()} -t {args.duration} -P 1 -C {args.classic_cca} -O {args.omit} -J --get-server-output | jq -c > '{args.folder}/classic-results.json'"
)
tx_prague.cmd_check(
    f"iperf3 -c {rx_prague.IP()} -t {args.duration} -P 1 -C prague -O {args.omit} -J --get-server-output | jq -c > '{args.folder}/prague-results.json'"
)
tx_classic.waitOutput_check()

time.sleep(1)

for proc in processes:
    proc.send_signal(SIGINT)
for proc in processes:
    proc.wait()

if args.dropped_packets:
    # Show only the qdisc with handle 1: (the htb),
    # as DualPI2 currently has no proper json support.
    # Using -j and dumping the DualPI2 leads to a corrupt
    # json file, as the text representation is printed instead.
    # The number of dropped packets was identical
    # between the htb and the lower AQM in our experiments.
    router.cmd_check(
        f'tc -s -j qdisc show dev router-rx handle 1: > "{args.folder}/router-rx-stats.json"'
    )

time.sleep(1)
net.stop()
