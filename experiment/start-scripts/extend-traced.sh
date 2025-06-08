SCRIPT_PATH="$(realpath $0)"
SCRIPT_FOLDER="$(dirname $SCRIPT_PATH)"
BASE_FOLDER="$SCRIPT_FOLDER/../.."

n_bdp=8
omit=10

mn -c

for cca in "cubic" "bbr2"
do
    for aqm in "CoDel" "DualPI2"
    do
        for rate in "4" "8" "16" "32" "64" "128" "256"
        do
            for delay in "4" "8" "16" "32" "64" "128"
            do
                python "$BASE_FOLDER/experiment/run.py" \
                    -f "$BASE_FOLDER/data/raw/extend/N$n_bdp/O$omit/$(uname -r)/$cca/$aqm/D$delay/R$rate/31" \
                    --classic-cca "$cca" \
                    --aqm "$aqm" \
                    --rate "$rate" \
                    --delay "$delay" \
                    --n-bdp "$n_bdp" \
                    --omit "$omit" \
                    --trace "$BASE_FOLDER/experiment/bpftrace-scripts/trace-classic-ecn.bt"
            done
        done
    done
done
