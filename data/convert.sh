SCRIPT_PATH="$(realpath $0)"
SCRIPT_FOLDER="$(dirname $SCRIPT_PATH)"
BASE_FOLDER="$SCRIPT_FOLDER/.."

python "$BASE_FOLDER/data/converter.py" \
    -f "$BASE_FOLDER/data/raw/reproduce/" \
    -c kernel classic_cca aqm bdp i \
    -s bdp \
    -o "$BASE_FOLDER/data/reproduce.csv"

python "$BASE_FOLDER/data/converter.py" \
    -f "$BASE_FOLDER/data/raw/extend/" \
    -c bdp omit kernel classic_cca aqm rtt rate i \
    -s bdp omit rtt rate \
    -o "$BASE_FOLDER/data/extend.csv"

cp -r "$BASE_FOLDER/data/raw/trace" "$BASE_FOLDER/data"
