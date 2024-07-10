#!/bin/bash

# Path to your Python script
PYTHON_SCRIPT="ials_simple.py"

# Arguments to pass to the Python script
ARGS="--data Data/ml-1m --epochs 12 --embedding_dim 192 --regularization 0.007 --unobserved_weight 0.3 --stddev 0.1"

# Number of times to execute the script
NUM_EXECUTIONS=10

# Loop to execute the script
for i in $(seq 1 $NUM_EXECUTIONS)
do
  echo "Execution $i"
  python $PYTHON_SCRIPT $ARGS
done

ARGS="--data Data/pinterest-20 --epochs 12 --embedding_dim 192 --regularization 0.007 --unobserved_weight 0.3 --stddev 0.1"

for i in $(seq 1 $NUM_EXECUTIONS)
do
  echo "Execution $i"
  python $PYTHON_SCRIPT $ARGS
done

ARGS="--data Data/last-fm --epochs 12 --embedding_dim 192 --regularization 0.007 --unobserved_weight 0.3 --stddev 0.1 --grid_search True" 

python $PYTHON_SCRIPT $ARGS