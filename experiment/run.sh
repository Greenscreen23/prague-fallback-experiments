#!/bin/sh

for aqm in "FIFO" "FIFO (ECN)" "CoDel" "FQ" "FQ-CoDel" "DualPI2"
do
    for n_ddp in "0.5" "1" "2" "4" "8"
    do
        python experiment.py -f "Results/Patched/$aqm-N$n_ddp" --aqm "$aqm" --n-ddp "$n_ddp" -i 10
    done
done
