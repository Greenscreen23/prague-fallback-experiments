# Reproducing and Solving a Fallback Issue in TCP Prague

This repo contains the experiment code, plotting code and experiment data of the paper Reproducing and Solving a Fallback Issue in TCP Prague. 

## Reproducing the Experiments

You can reproduce the experiments by running the [prague Linux kernel](https://github.com/L4STeam/linux/tree/15b3b6c85e5f996618a6fb8a9b50a8f9e1886a06). To run a single instance launch the `run.py` file in the experiment folder. All command line flags are documented in `args.py` and the topology is documented in `topo.py`.

To reproduce a specific experimental setup, use the scripts in the `start-scripts` subfolder:
- For chapter 3 use `reproduce.sh`.
- For chapter 4 use `extend.sh`.
- For chapter 5 first either apply `bpftrace-scripts/noinline.diff` to the linux kernel, compile it, and run it, or follow the instructions in the three bpftrace files in the `bpftrace-scripts` folder to change the function being traced. Then use `trace.sh`.
- For chapter 6 first run the [updated prague Linux kernel](https://github.com/L4STeam/linux/tree/48b3db6b4a7fd57e2d31db3bb46a3bc6af7bf3ad) and then run `extend.sh`. To run the additional traced run follow the setup instructions for chapter 5 and then run `extend-traced.sh`.

## Using Our Experiment Data

You can retrieve our raw experiment data from the Github release of this repo. The `data` folder contains a compressed version of our data. To use our plotting notebooks, you don't need to download the raw experiment data. Our raw data was compressed by running the `convert.sh` script.

## Plotting

All plots in the paper were created using the notebooks in the `plotting` folder.
- For Figure 1 we used `explain.ipynb`
- For Figure 3 we used `reproduce.ipynb`
- For Figure 4 and 5 we used `extend.ipynb`

All plots created are in the `images` subfolder. You can also find additional plots in that folder which were discussed in the paper. For example `plotting/images/extend/patched/classic_ecn.pdf` visualizes the bpftrace output of the additional experiment run described in chapter 6.
