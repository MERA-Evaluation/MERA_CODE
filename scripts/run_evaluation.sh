#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

################################################################################
# run_evaluation.sh
#
# A flexible wrapper around lm_eval that splits a comma-separated task list,
# iterates over each, and handles failures without stopping the entire run.
# At the end, packages results for submission and cleans up temporary files.
#
# Usage: ./run_evaluation.sh [options]
#        ./run_evaluation.sh --help    # to show documentation below
################################################################################

# Print usage/help information
usage() {
  cat <<EOF

Usage: $0 [OPTIONS]

Tasks (required):
  -t, --tasks TASK1,TASK2,…   Comma-separated list of tasks to evaluate
                              (default: all MERA Code tasks)

Model / runtime options:
  -m, --model ENGINE          lm_eval engine (hf | vllm | local-chat-completions)
  -a, --model_args ARGS       comma-separated key=val pairs for model init
  -g, --gen_kwargs JSON       comma-separated key=val pairs for generation kwargs
  -d, --device DEVICE         cuda | cpu
  -b, --batch_size SIZE       integer or "auto"
  -v, --verbosity LEVEL       DEBUG | INFO | WARNING | ERROR
      --compute_metrics       disable --predict_only (compute metrics instead of bypass)
      --no_logs               disable --log_samples (skip logging inputs/outputs)
      --use_cache PATH        enable --use_cache PATH (cache intermediate results)
      --trust_remote_code     pass --trust_remote_code into models or datasets init
      --no_chat_template      disables chat_template usage for model evaluation
  -o, --output_path DIR       directory for logs & results (default: "./results")
  -h, --help                  show this help message and exit

Examples:
  # All tasks, hf, one GPU:
  bash scripts/run_evaluation.sh \
    --model_args "pretrained=Qwen/Qwen2.5-0.5B-Instruct,dtype=bfloat16" \
    --output_path ./mera_code_results/Qwen2.5-0.5B-Instruct

  # Custom tasks, vllm, two GPUs:
  CUDA_VISIBLE_DEVICES="0,1" bash scripts/run_evaluation.sh \
    --tasks rucodeeval,realcode \
    --model vllm
    --model_args "pretrained=Qwen/Qwen2.5-0.5B-Instruct,tensor_parallel_size=2" \
    --output_path ./mera_code_results/Qwen2.5-0.5B-Instruct

  # All tasks, API, save cache:
  OPENAI_API_KEY="..." bash scripts/run_evaluation.sh \
    --model openai-chat-completions
    --device cpu
    --model_args "model=gpt-4o,num_concurrent=8,timeout=90000" \
    --output_path ./mera_code_results/gpt-4o
    --use_cache ./models_cache/gpt-4o
  
  # All tasks, vllm serve:
  bash scripts/run_evaluation.sh \
    --model local-chat-completions
    --device cpu
    --model_args "model=Qwen/Qwen2.5-0.5B-Instruct,num_concurrent=8,timeout=200,base_url=http://localhost:8888/v1/chat/completions" \
    --output_path ./mera_code_results/Qwen2.5-0.5B-Instruct
  
  # All tasks, pre-trained (base, no chat template) model:
  bash scripts/run_evaluation.sh \
    --model_args "pretrained=bigcode/starcoder2-7b,dtype=auto" \
    --output_path ./mera_code_results/starcoder2-7b
    --no_chat_template

EOF
  exit 1
}

################################################################################
# Default tasks (space-separated list)
################################################################################
DEFAULT_TASK_LIST=(
  rucodeeval
  codelintereval
  rucodereviewer
  ruhumaneval
  strucom
  unittests
  codecorrectness
  realcode
  realcodejava
  javatestgen
  yabloco
)

################################################################################
# Configurable parameters with defaults
################################################################################
TASKS=""                     # comma-separated input tasks
MODEL="hf"                   # lm_eval engine
MODEL_ARGS=""                # model initialization parameters
GEN_KWARGS=""                # generation kwargs JSON string
DEVICE="cuda"                # default device
BATCH_SIZE=1                 # default batch size
VERBOSITY="ERROR"            # default verbosity level
PREDICT_ONLY=true            # include --predict_only by default
LOG_SAMPLES=true             # include --log_samples by default
USE_CACHE_PATH=""            # path for --use_cache (optional)
OUTPUT_PATH="./results"      # output/ log directory (required)
TRUST_REMOTE_CODE=false      # include --trust_remote_code by default
CHAT_TEMPLATE=true           # include --apply_chat_template and --fewshot_as_multiturn by default

################################################################################
# Parse command-line arguments
################################################################################
while [[ $# -gt 0 ]]; do
  case "$1" in
    -t|--tasks)              TASKS="$2"; shift 2;;
    -m|--model)              MODEL="$2"; shift 2;;
    -a|--model_args)         MODEL_ARGS="$2"; shift 2;;
    -g|--gen_kwargs)         GEN_KWARGS="$2"; shift 2;;
    -d|--device)             DEVICE="$2"; shift 2;;
    -b|--batch_size)         BATCH_SIZE="$2"; shift 2;;
    -v|--verbosity)          VERBOSITY="$2"; shift 2;;
    --compute_metrics)       PREDICT_ONLY=false; shift;;
    --no_log_samples)        LOG_SAMPLES=false; shift;;
    --trust_remote_code)     TRUST_REMOTE_CODE=true; shift;;
    --no_chat_template)      CHAT_TEMPLATE=false; shift;;
    --use_cache)             USE_CACHE_PATH="$2"; shift 2;;
    -o|--output_path)        OUTPUT_PATH="$2"; shift 2;;
    -h|--help)               usage;;
    *) echo "Unknown option: $1" >&2; usage;;
  esac
done

################################################################################
# Build TASK_LIST: split comma-separated or use default
################################################################################
if [[ -n "$TASKS" ]]; then
  IFS=',' read -r -a TASK_LIST <<< "$TASKS"
else
  TASK_LIST=("${DEFAULT_TASK_LIST[@]}")
fi

################################################################################
# Immutable evaluation settings (do not change)
################################################################################
SEED=1234                     # fixed random seed for reproducibility
INCLUDE_PATH="./code_tasks"   # path to custom task definitions

################################################################################
# Prepare environment for HuggingFace & CUDA
################################################################################
mkdir -p "$OUTPUT_PATH"
export HF_DATASETS_CACHE="${OUTPUT_PATH}/ds_cache"
export HF_DATASETS_IN_MEMORY_MAX_SIZE=23400000
export TOKENIZERS_PARALLELISM=false
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export PYTHONPATH="$PWD"

################################################################################
# Build the common lm_eval flags array
################################################################################
COMMON_FLAGS=(
  --model         "$MODEL"
  --model_args    "$MODEL_ARGS"
  --device        "$DEVICE"
  --batch_size    "$BATCH_SIZE"
)

$PREDICT_ONLY       && COMMON_FLAGS+=(--predict_only)
$LOG_SAMPLES        && COMMON_FLAGS+=(--log_samples)
$TRUST_REMOTE_CODE  && COMMON_FLAGS+=(--trust_remote_code)
$CHAT_TEMPLATE      && COMMON_FLAGS+=(--apply_chat_template --fewshot_as_multiturn)

COMMON_FLAGS+=(
  --seed          "$SEED"
  --verbosity     "$VERBOSITY"
  --include_path  "$INCLUDE_PATH"
  --output_path   "$OUTPUT_PATH"
)

[[ -n "$GEN_KWARGS"     ]] && COMMON_FLAGS+=(--gen_kwargs "$GEN_KWARGS")
[[ -n "$USE_CACHE_PATH" ]] && COMMON_FLAGS+=(--use_cache  "$USE_CACHE_PATH")

################################################################################
# Stage 1: Run evaluations over each task, logging failures
################################################################################
echo "→ Evaluating ${#TASK_LIST[@]} task(s): ${TASK_LIST[*]}"
echo "  engine:              $MODEL"
echo "  model_args:          $MODEL_ARGS"
echo "  gen_kwargs:          $GEN_KWARGS"
echo "  device:              $DEVICE"
echo "  batch_size:          $BATCH_SIZE"
echo "  predict_only:        $PREDICT_ONLY"
echo "  log_samples:         $LOG_SAMPLES"
echo "  verbosity:           $VERBOSITY"
echo "  include_path:        $INCLUDE_PATH"
echo "  output_path:         $OUTPUT_PATH"
echo "  trust_remote_code:   $TRUST_REMOTE_CODE"
echo "  chat_template:       $CHAT_TEMPLATE
[[ -n "$USE_CACHE_PATH" ]] && echo "  use_cache:           $USE_CACHE_PATH"
echo

FAIL_LOG="$OUTPUT_PATH/failures.log"
: > "$FAIL_LOG"  # clear previous failures

for task in "${TASK_LIST[@]}"; do
  echo "→ Task: $task"
  if ! lm_eval --tasks "$task" "${COMMON_FLAGS[@]}"; then
    code=$?
    ts=$(date +'%Y-%m-%d %H:%M:%S')
    echo "[$ts] Task '$task' failed (exit $code)" >> "$FAIL_LOG"
    echo "  ❌ logged failure"
  else
    echo "  ✅ success"
  fi
done

################################################################################
# Stage 2: Package outputs into submission format
################################################################################
echo -e "\nPackaging outputs into submission format..."
HF_DATASETS_CACHE="${OUTPUT_PATH}/ds_cache" \
HF_DATASETS_IN_MEMORY_MAX_SIZE=23400000 \
python scripts/log_to_submission.py \
  --outputs_dir "${OUTPUT_PATH}" \
  --dst_dir "${OUTPUT_PATH}_submission" \
  --model_args  "${MODEL_ARGS}"

################################################################################
# Stage 3: Cleanup temporary files and directories
################################################################################
echo "Cleaning up caches and temp folders..."
rm -rf "${OUTPUT_PATH}/ds_cache" \
       extracted_codes reports working_dir workspace/data workspace/java_testgen_workdir

echo "Done. All stages complete."
