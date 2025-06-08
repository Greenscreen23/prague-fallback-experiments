SCRIPT_PATH="$(realpath $0)"
SCRIPT_FOLDER="$(dirname $SCRIPT_PATH)"
BASE_FOLDER="$SCRIPT_FOLDER/../.."

mn -c

for script in "$BASE_FOLDER"/experiment/bpftrace-scripts/*.bt
do
    python "$BASE_FOLDER/experiment/run.py" \
        -f "$BASE_FOLDER/data/raw/trace/$(basename $script)" \
        --trace "$script" \
        --n-bdp 8
done
