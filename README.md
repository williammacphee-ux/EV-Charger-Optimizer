# EV-Charger-Optimizer
P-median facility-location model that places public EV chargers to minimize resident travel distance. Python, PuLP, real Census data.

EV Charger Placement Optimizer

An operations-research model that chooses where to place public EV charging stations in Cambridge, MA so that residents travel the shortest possible distance to charge. Built in Python with integer programming, on real U.S. Census and City of Cambridge data, and solved to provable optimality.

Course project (Introduction to Python for Business Data Analysis) — William MacPhee & Tyler Hobons.

Overview

Cambridge is expanding its public EV charging network and has to decide where the stations go. This matters most for residents without off-street parking — mostly renters — who depend on public chargers: they park on the street, plug in overnight, and walk home, so how far they travel to a charger determines whether public charging is usable for them. Because the City funds only a few stations per phase, which sites come first is a real, staged decision.

This project models that decision as a p-median facility-location problem and solves it exactly, so the result is the provable optimum rather than a heuristic guess.

Study area: Cambridge, MA
Candidate sites: 32 census tracts
Stations selected: 8
Objective: minimize population-weighted renter travel distance to the nearest station
Approach

The model is a mixed-integer linear program solved with the CBC solver via PuLP.

Decision variables

x[j] — 1 if a station is built in tract j
y[i][j] — 1 if residents of tract i are assigned to the station in tract j
t[i][j] >= 0 — distance residents of i actually travel to j

Objective

Minimize sum p[i] * t[i][j] — total distance travelled, weighted by how many people travel it

Constraints

Every tract's residents charge somewhere: sum_j y[i][j] = 1
You can only travel to a built station: t[i][j] <= d[i][j] * x[j]
If assigned i->j, the full distance counts: t[i][j] >= d[i][j] * y[i][j]
You can only be assigned to a built station: y[i][j] <= x[j]
Build exactly m stations: sum_j x[j] = m

The population weight makes the solution equitable — a tract with more renters pulls stations toward it, so the model minimizes distance per person, not per tract.

Data

All data is public and was verified rather than trusted blindly:

Demand (p[i]): renter-occupied households per tract, U.S. Census ACS 5-Year 2024, Table B25003. Renters are the group the City itself names as most dependent on public charging. Range: 255–2,161 per tract.
Locations: official tract centroids from the U.S. Census 2024 Gazetteer Files; distances are great-circle (haversine) miles between centroids.
Identifying Cambridge's 32 tracts: the Census returns all 357 Middlesex County tracts, so the 32 Cambridge tracts were identified from the City's official 2020 census-tract map, then verified by confirming the renter counts summed to the known citywide total — proving the correct tracts were selected rather than a slice of a neighboring city.

AI assistance: Claude and Gemini were used to help clean and organize the raw Census download into the processed files in this repo. The modeling, formulation, and analysis are the authors' own.

Results
Optimal placement. Stations are built in tracts 3521.01, 3523, 3525, 3532, 3538, 3540, 3549.01, and 3549.02 — spread across the city rather than clustered, which is the model balancing dense demand against keeping outlying areas close.
Provably optimal across 10.5M+ possible combinations of 8 sites from 32 candidates — the CBC solver reports Optimal on every run, so no better placement exists under the stated objective.
Average travel: 0.252 miles per resident.
Beats simpler strategies: 4.0% less travel than a population-based rule (build in the 8 highest-population tracts) and 3.1% less than a greedy distance-reducing heuristic.

The margins are modest — a genuine finding, not a disappointment. When demand is fairly spread out and candidate sites are dense, even simple heuristics land close to optimal, so the exact optimum improves on them only modestly. The value of the full model is twofold: once you care about distance travelled rather than just population served, the problem genuinely requires optimization, and the model guarantees the best answer and quantifies exactly how much travel the simpler rules leave on the table.

Sensitivity: how many stations are worth building?

Re-solving for each number of stations shows clear diminishing returns — useful for the City's phased-funding decision:

Stations	Avg. distance (mi)
1	1.23
2	0.66
6	0.33
8	0.25

Each added station helps less than the last, which tells the City where funding stops buying much improvement.

The bug I caught and fixed

The first version returned an impossible answer: zero total travel. Because the distance from a tract to itself is zero, the original formulation let a tract "charge at home" for zero cost without a station ever being built there — the solver was gaming the math. The fix was one constraint — y[i][j] <= x[j], meaning residents can only be assigned to a tract that actually has a station — which closed the loophole and produced valid results. Reasoning from an impossible output back to the flawed constraint is the difference between running a solver and understanding one.

Repository contents
ev_model_V2.py                # the optimization model + benchmarks
cambridge_tract_demand.csv    # renter / owner / total households per tract
cambridge_tract_centroids.csv # tract centroids (lat/lon) + renter counts
README.md
How to run
bash
pip install pulp
python ev_model_V2.py

CBC ships with PuLP, so no separate solver install is needed. The script prints the chosen stations, the full assignment, the benchmark comparison, and writes v2_results.json.

What this project demonstrates
Translating a real municipal siting decision into a formal optimization model
Integer/linear programming and exact, provably optimal solution methods (p-median / facility location)
Working with real public data — and verifying it rather than trusting it blindly
Debugging a subtle formulation flaw and validating the corrected result
Benchmarking the optimum against practical heuristics and quantifying the gap
