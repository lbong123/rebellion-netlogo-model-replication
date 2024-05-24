# Rebellion-netlogo-model-replication

The following code is written and designed using Python classes. The user is only intended to
interact and perfrom simulations through the public methods listed in the RebellionManager.

The output of each simulation is additionally stored within a test.csv file

## Instructions to replicate the parameter sweeping and extension experiments
No scripts were created in the process to generate our results, experimentation was frequent and distributed across the team and thus the testing occurred by interacting through the manager and manually updating various variables using different seeds. Here is an example of how one can replicate these results.

### Parameter sweeping
All parameters were initialised to their respective values in the setup method. You can refer to the variables used from each table in the report.

Random seeds of 1000, 2000 and 3000 were then used
to aggregate our statistics across the 3 runs. This was across 100 simulations ticks.

### Scale shifting of perceived hardship
The standard parameters from Netlogo were used and the seed was set to 12 across 500 simulation ticks.

The shift_perceived_hardship boolean was set to true

### Aggregate greivance
The standard parameters from Netlogo were used and the seed was set to 12 across 500 simulation ticks.

The aggregate_greivance boolean was set to true

### Standard
The standard parameters from Netlogo were used and the seed was set to 12 across 500 simulation ticks.