from mininet.topo import Topo
from mininet.node import Host


class ExperimentTopo(Topo):
    def build(self, cli_args):
        self.create_hosts(cli_args)
        self.create_switches()
        self.create_links()

    def create_hosts(self, cli_args):
        self.tx_prague = self.addHost(
            "tx_prague",
            ip="10.0.10.10/24",
            cls=PragueHost,
            ecn_fallback=cli_args.ecn_fallback,
            routes=[
                f"default via 10.0.10.1{' quickack 1' if cli_args.quickack else ''}"
            ],
        )
        self.rx_prague = self.addHost(
            "rx_prague",
            ip="10.0.12.11/24",
            cls=PragueHost,
            ecn_fallback=cli_args.ecn_fallback,
            routes=[
                f"default via 10.0.12.2{' quickack 1' if cli_args.quickack else ''}"
            ],
        )

        self.tx_cubic = self.addHost(
            "tx_cubic",
            ip="10.0.10.20/24",
            cls=CubicHost,
            routes=[
                f"default via 10.0.10.1{' quickack 1' if cli_args.quickack else ''}"
            ],
        )
        self.rx_cubic = self.addHost(
            "rx_cubic",
            ip="10.0.12.21/24",
            cls=CubicHost,
            routes=[
                f"default via 10.0.12.2{' quickack 1' if cli_args.quickack else ''}"
            ],
        )

        self.delay = self.addHost(
            "delay",
            ip="10.0.10.1/24",
            cls=DelayHost,
            delay=cli_args.delay,
            routes=[
                f"10.0.12.0/24 via 10.0.11.2{' quickack 1' if cli_args.quickack else ''}",
            ],
        )
        self.router = self.addHost(
            "router",
            ip="10.0.12.2/24",
            cls=RouterHost,
            rate=cli_args.rate,
            aqm=cli_args.aqm,
            btl_limit=int(1000 * cli_args.n_ddp * cli_args.rate * cli_args.delay / 8),
            ecn_threshold=cli_args.ecn_threshold,
            routes=[
                f"10.0.10.0/24 via 10.0.11.1{' quickack 1' if cli_args.quickack else ''}"
            ],
        )

    def create_switches(self):
        self.s1 = self.addSwitch("s1")
        self.s2 = self.addSwitch("s2")

    def create_links(self):
        self.addLink(self.tx_prague, self.s1)
        self.addLink(self.tx_cubic, self.s1)
        self.addLink(self.s1, self.delay, intfName2="delay-tx")

        self.addLink(
            self.router,
            self.s2,
            intfName1="router-rx",
            intfName2="s2-router",  # Used for tcpdump
        )
        self.addLink(self.s2, self.rx_prague)
        self.addLink(self.s2, self.rx_cubic)

        # Add this link last, so the intfs above become default intf and inherit the default IP
        self.addLink(
            self.delay,
            self.router,
            intfName1="delay-router",
            intfName2="router-delay",
            params1={"ip": "10.0.11.1/24"},
            params2={"ip": "10.0.11.2/24"},
        )


class ExperimentHost(Host):
    def __init__(self, *args, routes, **kwargs):
        super().__init__(*args, **kwargs)

        self.routes = routes

    def config(self, *args, **kwargs):
        super().config(*args, **kwargs)

        self.cmd("sysctl -w net.ipv4.ip_forward=1")

        for route in self.routes:
            self.cmd("ip route add " + route)

        for intf in self.intfNames():
            for offload in ["gro", "lro", "gso", "tso"]:
                self.cmd(f"ethtool -K {intf} {offload} off")


class PragueHost(ExperimentHost):
    def __init__(self, *args, ecn_fallback, **kwargs):
        super().__init__(*args, **kwargs)

        self.ecn_fallback = ecn_fallback

    def config(self, *args, **kwargs):
        super().config(*args, **kwargs)

        self.cmd("modprobe tcp_prague")
        self.cmd("sysctl -w net.ipv4.tcp_congestion_control=prague")
        self.cmd(
            f"echo {self.ecn_fallback} > /sys/module/tcp_prague/parameters/prague_ecn_fallback"
        )
        self.cmd(
            f"tc qdisc add dev {self.name}-eth0 root handle 1: fq limit 20480 flow_limit 10240"
        )


class CubicHost(ExperimentHost):
    def config(self, *args, **kwargs):
        super().config(*args, **kwargs)

        self.cmd("modprobe tcp_cubic")
        self.cmd("sysctl -w net.ipv4.tcp_congestion_control=cubic")
        self.cmd("sysctl -w net.ipv4.tcp_ecn=1")


class DelayHost(ExperimentHost):
    def __init__(self, *args, delay, **kwargs):
        super().__init__(*args, **kwargs)

        self.delay = delay

    def config(self, *args, **kwargs):
        super().config(*args, **kwargs)

        self.cmd("modprobe sch_netem")
        for intf in self.intfNames():
            self.cmd(
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

        assert self.aqm in [
            "DualPI2",
            "FIFO",
            "FIFO (ECN)",
            "CoDel",
            "FQ",
            "FQ-CoDel",
        ], f"Unexpected AQM: {self.aqm}"

        self.cmd("modprobe sch_htb")
        self.cmd("tc qdisc add dev router-rx root handle 1: htb default 3")
        self.cmd(
            f"tc class add dev router-rx parent 1: classid 1:3 htb rate {self.rate}mbit"
        )

        def add_aqm(aqm_string):
            self.cmd("tc qdisc add dev router-rx parent 1:3 handle 3: " + aqm_string)

        if self.aqm == "FIFO":
            add_aqm(f"bfifo limit {self.btl_limit}")
        elif self.aqm == "FIFO (ECN)":
            self.cmd("modprobe sch_fq")
            add_aqm(
                f"fq limit {self.btl_pkt_limit} flow_limit {self.btl_pkt_limit} orphan_mask 0 ce_threshold {self.ecn_threshold}ms",
            )
        elif self.aqm == "CoDel":
            self.cmd("modprobe sch_codel")
            add_aqm(
                f"codel limit {self.btl_pkt_limit} target {self.ecn_threshold}ms interval 100ms ecn"
            )
        elif self.aqm == "FQ":
            self.cmd("modprobe sch_fq")
            add_aqm(
                f"fq limit {self.btl_pkt_limit} flow_limit {self.btl_pkt_limit} ce_threshold {self.ecn_threshold}ms"
            )
        elif self.aqm == "FQ-CoDel":
            self.cmd("modprobe sch_fq_codel")
            add_aqm(
                f"fq_codel limit {self.btl_pkt_limit} target {self.ecn_threshold}ms interval 100ms ecn"
            )
        elif self.aqm == "DualPI2":
            self.cmd("modprobe sch_dualpi2")
            add_aqm(f"dualpi2 limit {self.btl_pkt_limit} target {self.ecn_threshold}ms")
