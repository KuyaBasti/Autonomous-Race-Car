#!/bin/bash

# Array of commands and labels
commands=(
    "ros2 launch f1tenth_stack bringup_launch.py"
    "ros2 launch f1tenth_stack particle_filter_launch.py"
    "ros2 launch f1tenth_stack autonomous_launch.py"
)

labels=(
    "bringup"
    "particle_filter"
    "autonomous"
)

pids=()

# Function to run command with prefixed output
run_with_prefix() {
    local label="$1"
    shift
    "$@" 2>&1 | while IFS= read -r line; do
        echo "[$label] $line"
    done
}

# Function to kill all started processes
kill_all() {
    echo "Terminating all processes..."
    for pid in "${pids[@]}"; do
        kill "$pid" 2>/dev/null
    done
    wait
    echo "All processes terminated."
    exit 1
}

# Trap SIGINT (Ctrl+C), SIGTERM, and EXIT
trap kill_all SIGINT SIGTERM

# Start each command
for i in "${!commands[@]}"; do
    cmd="${commands[i]}"
    label="${labels[i]}"
    run_with_prefix "$label" bash -c "$cmd" &
    pids+=($!)
done

# Wait for all background jobs
for pid in "${pids[@]}"; do
    wait "$pid"
done

echo "All processes completed."
