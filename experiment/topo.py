from mininet.topo import Topo
from mininet.node import Host
from args import AQMS


class ExperimentTopo(Topo):
    def build(self, cli_args):
        self.create_hosts(cli_args)
        self.create_switches()
        self.create_links()

    def create_hosts(self, cli_args):
        self.tx_prague = self.addHost(
            "tx_prague",
            ip="10.0.1.1/24",
            cls=PragueHost,
            ecn_fallback=cli_args.ecn_fallback,
            routes=["default via 10.0.1.3"],
        )
        self.tx_classic = self.addHost(
            "tx_classic",
            ip="10.0.1.2/24",
            cls=ClassicHost,
            cca=cli_args.classic_cca,
            routes=["default via 10.0.1.3"],
        )

        self.delay = self.addHost(
            "delay",
            ip="10.0.1.3/24",
            cls=DelayHost,
            delay=cli_args.delay,
            routes=["10.0.3.0/24 via 10.0.2.4"],
        )
        self.router = self.addHost(
            "router",
            ip="10.0.3.4/24",
            cls=RouterHost,
            rate=cli_args.rate,
            aqm=cli_args.aqm,
            btl_limit=int(1000 * cli_args.n_bdp * cli_args.rate * cli_args.delay / 8),
            ecn_threshold=cli_args.ecn_threshold,
            routes=["10.0.1.0/24 via 10.0.2.3"],
        )

        self.rx_prague = self.addHost(
            "rx_prague",
            ip="10.0.3.5/24",
            cls=PragueHost,
            ecn_fallback=cli_args.ecn_fallback,
            routes=["default via 10.0.3.4"],
        )
        self.rx_classic = self.addHost(
            "rx_classic",
            ip="10.0.3.6/24",
            cls=ClassicHost,
            cca=cli_args.classic_cca,
            routes=["default via 10.0.3.4"],
        )

    def create_switches(self):
        self.s1 = self.addSwitch("s1")
        self.s2 = self.addSwitch("s2")

    def create_links(self):
        self.addLink(self.tx_prague, self.s1)
        self.addLink(self.tx_classic, self.s1)
        self.addLink(self.s1, self.delay, intfName2="delay-tx")

        self.addLink(self.router, self.s2, intfName1="router-rx", intfName2="s2-router")
        self.addLink(self.s2, self.rx_prague)
        self.addLink(self.s2, self.rx_classic)

        # Add this link last, so the intfs above become default intf and inherit the default IP
        self.addLink(
            self.delay,
            self.router,
            intfName1="delay-router",
            intfName2="router-delay",
            params1={"ip": "10.0.2.3/24"},
            params2={"ip": "10.0.2.4/24"},
        )


class ExperimentHost(Host):
    def __init__(self, *args, routes, **kwargs):
        super().__init__(*args, **kwargs)

        self.routes = routes

    def config(self, *args, **kwargs):
        super().config(*args, **kwargs)

        self.cmd_check("sysctl -w net.ipv4.ip_forward=1")

        for route in self.routes:
            self.cmd_check("ip route add " + route)

        for intf in self.intfNames():
            for offload in ["gro", "lro", "gso", "tso"]:
                self.cmd_check(f"ethtool -K {intf} {offload} off")

    def cmd_check(self, *args, **kwargs):
        self.cmd(*args, **kwargs)
        self.check(f"cmd with args={args} and kwargs={kwargs}")

    def sendCmd_check(self, *args, **kwargs):
        self.cmd_args = args
        self.cmd_kwargs = kwargs
        self.sendCmd(*args, **kwargs)

    def waitOutput_check(self, *args, **kwargs):
        self.waitOutput(*args, **kwargs)
        self.check(f"cmd with args={self.cmd_args} and kwargs={self.cmd_kwargs}")

    def check(self, cmd):
        exit_code = self.cmd("echo -n $?")
        assert exit_code == "0", f"{cmd} failed with non-zero exit code {exit_code}"


class PragueHost(ExperimentHost):
    def __init__(self, *args, ecn_fallback, **kwargs):
        super().__init__(*args, **kwargs)

        self.ecn_fallback = ecn_fallback

    def config(self, *args, **kwargs):
        super().config(*args, **kwargs)

        self.cmd_check("modprobe tcp_prague")
        self.cmd_check("sysctl -w net.ipv4.tcp_congestion_control=prague")
        self.cmd_check(
            f"echo {self.ecn_fallback} > /sys/module/tcp_prague/parameters/prague_ecn_fallback"
        )

        self.cmd_check("modprobe sch_fq")
        for intf in self.intfNames():
            self.cmd_check(
                f"tc qdisc add dev {intf} root handle 1: fq limit 20480 flow_limit 10240"
            )


class ClassicHost(ExperimentHost):
    def __init__(self, *args, cca, **kwargs):
        super().__init__(*args, **kwargs)

        self.cca = cca

    def config(self, *args, **kwargs):
        super().config(*args, **kwargs)

        self.cmd_check(f"modprobe tcp_{self.cca}")
        self.cmd_check(f"sysctl -w net.ipv4.tcp_congestion_control={self.cca}")
        self.cmd_check("sysctl -w net.ipv4.tcp_ecn=1")


class DelayHost(ExperimentHost):
    def __init__(self, *args, delay, **kwargs):
        super().__init__(*args, **kwargs)

        self.delay = delay

    def config(self, *args, **kwargs):
        super().config(*args, **kwargs)

        self.cmd_check("modprobe sch_netem")
        for intf in self.intfNames():
            self.cmd_check(
                f"tc qdisc add dev {intf} root netem delay {self.delay / 2}ms limit 60000"
            )


class RouterHost(ExperimentHost):
    def __init__(self, *args, rate, aqm, btl_limit, ecn_threshold, **kwargs):
        super().__init__(*args, **kwargs)

        self.rate = rate
        self.aqm = aqm
        self.btl_limit = btl_limit
        self.btl_pkt_limit = btl_limit // 1500 + 1
        self.ecn_threshold = ecn_threshold

    def config(self, *args, **kwargs):
        super().config(*args, **kwargs)

        assert self.aqm in AQMS, f"Unexpected AQM: {self.aqm}"

        self.cmd_check("modprobe sch_htb")
        self.cmd_check("tc qdisc add dev router-rx root handle 1: htb default 3")
        self.cmd_check(
            f"tc class add dev router-rx parent 1: classid 1:3 htb rate {self.rate}mbit"
        )

        aqm_base = "tc qdisc add dev router-rx parent 1:3 handle 3: "

        if self.aqm == "FIFO":
            self.cmd_check(f"{aqm_base} bfifo limit {self.btl_limit}")
        elif self.aqm == "FIFO (ECN)":
            self.cmd_check("modprobe sch_fq")
            self.cmd_check(
                f"{aqm_base} fq limit {self.btl_pkt_limit} flow_limit {self.btl_pkt_limit} orphan_mask 0 ce_threshold {self.ecn_threshold}ms",
            )
        elif self.aqm == "CoDel":
            self.cmd_check("modprobe sch_codel")
            self.cmd_check(
                f"{aqm_base} codel limit {self.btl_pkt_limit} target {self.ecn_threshold}ms interval 100ms ecn"
            )
        elif self.aqm == "FQ":
            self.cmd_check("modprobe sch_fq")
            self.cmd_check(
                f"{aqm_base} fq limit {self.btl_pkt_limit} flow_limit {self.btl_pkt_limit} ce_threshold {self.ecn_threshold}ms"
            )
        elif self.aqm == "FQ-CoDel":
            self.cmd_check("modprobe sch_fq_codel")
            self.cmd_check(
                f"{aqm_base} fq_codel limit {self.btl_pkt_limit} target {self.ecn_threshold}ms interval 100ms ecn"
            )
        elif self.aqm == "DualPI2":
            self.cmd_check("modprobe sch_dualpi2")
            self.cmd_check(
                f"{aqm_base} dualpi2 limit {self.btl_pkt_limit} target {self.ecn_threshold}ms"
            )
