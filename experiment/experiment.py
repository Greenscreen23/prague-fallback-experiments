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

for i in range(args.iterations):
    net = Mininet(topo=ExperimentTopo(cli_args=args))
    tx_prague = net.getNodeByName("tx_prague")
    rx_prague = net.getNodeByName("rx_prague")
    tx_cubic = net.getNodeByName("tx_cubic")
    rx_cubic = net.getNodeByName("rx_cubic")

    net.start()

    # Test connectivity
    net.pingAll()

    if args.cli:
        CLI(net)

    # Run the experiment
    if not args.skip_experiment:
        if args.trace_prague:
            traces = [
                Popen(
                    [
                        "bpftrace",
                        file,
                        "-o",
                        f"{args.folder}/{os.path.basename(file)}-{i}.out",
                    ]
                )
                for file in args.trace_prague
            ]

        if args.create_pcap:
            tcpdump = Popen(
                ["tcpdump", "-ni", "s2-router", "-w", f"{args.folder}/traffic-{i}.pcap"]
            )

        time.sleep(1)

        rx_prague.cmd("iperf3 -s -1 -p 5000 -D")

        if not args.disable_cubic:
            rx_cubic.cmd("iperf3 -s -1 -p 4000 -D")
            tx_cubic.sendCmd(
                f"sleep 1; iperf3 -c {rx_cubic.IP()} -t {args.duration} {'-N' if args.disable_nagle else ''} -P 1 -p 4000 -C cubic -J > \"{args.folder}/cubic-results-{i}.json\""
            )

        tx_prague.cmd(
            f"sleep 1; iperf3 -c {rx_prague.IP()} -t {args.duration} {'-N' if args.disable_nagle else ''} -P 1 -p 5000 -C prague -J > \"{args.folder}/prague-results-{i}.json\""
        )

        if not args.disable_cubic:
            tx_cubic.waitOutput(False)

        if args.trace_prague:
            for trace in traces:
                trace.send_signal(SIGINT)

        if args.create_pcap:
            tcpdump.send_signal(SIGINT)

        if args.trace_prague:
            for trace in traces:
                trace.wait()

        if args.create_pcap:
            tcpdump.wait()

        time.sleep(1)

    # Stop the network
    net.stop()
