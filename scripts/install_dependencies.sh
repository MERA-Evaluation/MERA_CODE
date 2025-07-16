#!/usr/bin/env bash

################################################################################
# Prerequisites
################################################################################

### Should be launched from MERA_CODE directory

### Make sure to use in after activating the virtual environment

### How to create conda environment
# conda create -n mera_code python=3.11.9 -y
# conda activate mera_code

### How to create python venv environment
# python3.11 -m venv mera_code
# source mera_code/bin/activate


################################################################################
# Install dependencies
################################################################################

#!/usr/bin/env bash
set -e

# Default mode
MODE="remote_scoring"

# Print usage and exit
usage() {
  echo "Usage: $0 [--remote_scoring|--local_scoring]"
  exit 1
}

# Parse arguments
if [ $# -gt 1 ]; then
  usage
elif [ $# -eq 1 ]; then
  case "$1" in
    --remote_scoring)
      MODE="remote_scoring"
      ;;
    --local_scoring)
      MODE="local_scoring"
      ;;
    *)
      usage
      ;;
  esac
fi

echo "Installing dependencies for mode: $MODE"

cd lm-evaluation-harness

echo "Installing lm-eval..."
pip install -e .

# go back to MERA_CODE directory
cd ..

# If local_scoring, install the extras
if [ "$MODE" = "local_scoring" ]; then

  echo "Installing code_bleu for UnitTests..."
  git clone https://github.com/Pstva/code_bleu.git
  cd code_bleu
  pip install -e .
  cd ..

  echo "Installing metrics for YABLoCo..."
  mkdir workspace
  cd workspace
  git clone -b mera_code https://github.com/yabloco-codegen/yabloco-benchmark
  cd ..

fi

echo "Done."
