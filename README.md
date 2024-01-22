
# Monetary Incentive Delay Task (MID)

This repository contains a Python implementation of the Monetary Incentive Delay Task (MID). The MID is a cognitive task that measures motivation and reward sensitivity. It is often used in research on decision-making, and reinforcement learning.

## Usage

To run the task, simply clone this repository and install the required dependencies:
* StreamInfo: https://pypi.org/project/pylsl/
* Psychopy: https://www.psychopy.org/
```
pip install pylsl psychopy
```
This will install the two required packages. Then, run the following command or run the code from your IDE:
```
python mid.py
```
You will be prompted to enter the Subject ID. Once you have entered it, the task will begin.

## Output data

The task will save the results to a file called 'results/{subject_id}.txt'. 
To date, this file will contain the following columns:

* cond: The condition (learn or reverse)
* trial_n: The trial number
* trial_setup: The reward setup for the trial
* latency_ms: The time it took the subject to respond
* selection: The box that the subject selected
* hit: Whether the subject selected the correct box
* result: The subject's total earnings after the trial
* streak: The subject's current streak of correct selections

## EEG markers

The task can also be used to record EEG data. To do this, you will need to connect an EEG device to your computer and use a recorder before running the task.

To date, the task will stream the following EEG markers:

* experiment_start
* fixation_shown
* key_pressed
* feedback_shown
* trial_start
* trial_end

You can use these markers to align your EEG data with the task events.
 
## Notes
Stimuli presentation and timing:
https://www.psychopy.org/coder/codeStimuli.html