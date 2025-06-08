SCRIPT_PATH="$(realpath $0)"
SCRIPT_FOLDER="$(dirname $SCRIPT_PATH)"
BASE_FOLDER="$SCRIPT_FOLDER/../.."

mn -c

for cca in "cubic" "bbr2"
do
    for aqm in "FIFO" "FIFO (ECN)" "CoDel" "FQ" "FQ-CoDel" "DualPI2"
    do
        for n_bdp in "0.5" "1" "2" "4" "8"
        do
            for i in $(seq 0 9)
            do
                python "$BASE_FOLDER/experiment/run.py" \
                    -f "$BASE_FOLDER/data/raw/reproduce/$(uname -r)/$cca/$aqm/N$n_bdp/$i" \
                    --classic-cca "$cca" \
                    --aqm "$aqm" \
                    --n-bdp "$n_bdp"
            done
        done
    done
done
