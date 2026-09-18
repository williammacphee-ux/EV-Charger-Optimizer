# ============================================================================
#  EV CHARGER PLACEMENT — V2 (Dr. D's formulation): minimize distance travelled
#  ---------------------------------------------------------------------------
#  Regions = 32 Cambridge census tracts. Each tract is BOTH a demand point and a
#  candidate station location (its centroid). We choose m tracts to build public
#  stations in, so that the total distance residents travel to charge is minimized.
#
#  This is the p-median / set-covering family (as Dr. D noted). Unlike the simple
#  "coverage" version, greedy does NOT solve this optimally — it genuinely needs
#  the solver.
#
#  Decision variables (exactly as specified):
#    x_j  in {0,1}      : 1 if a station is built in region j
#    y_ij in {0,1}      : 1 if people in region i travel to region j to charge
#    t_ij >= 0          : distance travelled by people of region i to region j
#
#  Minimize   sum_i sum_j  p_i * t_ij
#  s.t.       sum_j y_ij = 1                 for each i   (everyone charges somewhere)
#             t_ij <= d_ij * x_j             (can only travel to a built station)
#             t_ij >= d_ij * y_ij            (if i->j, travel is at least the distance)
#             sum_j x_j = m                  (build exactly m stations)
#
#  DATA (all real):
#    p_i  = renter-occupied households per tract (ACS B25003 5-yr 2024) [proxy for
#           residents dependent on public charging]
#    d_ij = straight-line miles between tract centroids (Census 2024 Gazetteer)
# ============================================================================

import pulp, math, json

# --- REAL tract data: (lat, lon, renter_pop) ---
tracts = {
    "3521.01":(42.371642,-71.07397,1564),"3521.02":(42.3685228,-71.0758378,785),
    "3522":(42.3719651,-71.085125,835),"3523":(42.3662197,-71.0835011,2161),
    "3524":(42.3650343,-71.0934341,594),"3525":(42.368235,-71.0978873,957),
    "3526":(42.3694072,-71.0912216,883),"3527":(42.3734746,-71.0936021,835),
    "3528":(42.3717557,-71.0963101,535),"3529":(42.3724814,-71.1033526,623),
    "3530":(42.3677877,-71.1032789,1168),"3531.01":(42.3625359,-71.0990808,1719),
    "3531.02":(42.3601076,-71.0909495,509),"3532":(42.3584986,-71.1057832,1399),
    "3533":(42.3585142,-71.1110542,784),"3536":(42.3805404,-71.1154594,1027),
    "3537":(42.3745268,-71.1122878,1010),"3538":(42.3708052,-71.1096338,1433),
    "3539":(42.3662691,-71.1162109,1127),"3540":(42.380987,-71.1226248,1352),
    "3541":(42.3748851,-71.1256481,465),"3542":(42.3734076,-71.135224,255),
    "3543":(42.3830878,-71.1471164,920),"3544":(42.3833722,-71.1372911,294),
    "3545":(42.3847449,-71.12504,344),"3546.01":(42.390845,-71.1491066,760),
    "3546.02":(42.3876828,-71.1359698,1275),"3547":(42.3895812,-71.1226285,656),
    "3548":(42.3926658,-71.1279416,546),"3549.01":(42.3964207,-71.1489645,1778),
    "3549.02":(42.3946771,-71.1357395,1365),"3550":(42.3985275,-71.1342815,748),
}
R = list(tracts.keys())
p = {i: tracts[i][2] for i in R}

def hav(a,b,c,d):
    Rm=3958.8;p1,p2=math.radians(a),math.radians(c)
    dp=math.radians(c-a);dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*Rm*math.asin(math.sqrt(x))

d = {(i,j): hav(tracts[i][0],tracts[i][1],tracts[j][0],tracts[j][1]) for i in R for j in R}

M = 8   # number of stations to build

# ---------------- V2 MODEL ----------------
prob = pulp.LpProblem("EV_V2_min_distance", pulp.LpMinimize)
x = {j: pulp.LpVariable(f"x_{j}", cat="Binary") for j in R}
y = {(i,j): pulp.LpVariable(f"y_{i}_{j}", cat="Binary") for i in R for j in R}
t = {(i,j): pulp.LpVariable(f"t_{i}_{j}", lowBound=0) for i in R for j in R}

# objective: minimize total distance-weighted travel
prob += pulp.lpSum(p[i]*t[(i,j)] for i in R for j in R)
for i in R:
    prob += pulp.lpSum(y[(i,j)] for j in R) == 1           # each region charges somewhere
    for j in R:
        prob += t[(i,j)] <= d[(i,j)]*x[j]                  # only travel to a built station
        prob += t[(i,j)] >= d[(i,j)]*y[(i,j)]              # travel is at least the distance
        prob += y[(i,j)] <= x[j]                           # can only be served by a BUILT station
prob += pulp.lpSum(x[j] for j in R) == M                  # build exactly M stations

prob.solve(pulp.PULP_CBC_CMD(msg=False))

built = [j for j in R if x[j].value() > 0.5]
total_travel = sum(p[i]*t[(i,j)].value() for i in R for j in R)
total_pop = sum(p.values())
avg_dist = total_travel/total_pop

print("="*64)
print(f"  V2 — MINIMIZE DISTANCE TRAVELLED   (status: {pulp.LpStatus[prob.status]})")
print(f"  Build {M} stations among {len(R)} Cambridge tracts")
print("="*64)
print("  Stations built in tracts:", ", ".join(sorted(built)))
print(f"\n  Total distance-weighted travel: {total_travel:,.0f} person-miles")
print(f"  Average distance per resident:  {avg_dist:.3f} miles")

# who travels where
print("\n  Assignment (tract -> station, distance):")
for i in sorted(R):
    for j in R:
        if y[(i,j)].value() and y[(i,j)].value() > 0.5:
            tag = "  (station here)" if i==j else ""
            print(f"    {i:>8} -> {j:<8}  {d[(i,j)]:.2f} mi{tag}")
            break

# ---------------- COMPARE TO V1 (Dr. D's "simple" allocation) ----------------
# V1: build in the m tracts with largest population (no optimization).
v1 = sorted(R, key=lambda j: -p[j])[:M]
def avg_dist_for(stations):
    tot = 0.0
    for i in R:
        nearest = min(d[(i,j)] for j in stations)
        tot += p[i]*nearest
    return tot, tot/total_pop
v1_travel, v1_avg = avg_dist_for(v1)

# Greedy for the distance objective (add the station that most reduces travel).
greedy = []
while len(greedy) < M:
    best,bestval = None, None
    for c in R:
        if c in greedy: continue
        _, a = avg_dist_for(greedy+[c])
        if bestval is None or a < bestval:
            best,bestval = c,a
    greedy.append(best)
g_travel, g_avg = avg_dist_for(greedy)

print("\n" + "-"*64)
print("  COMPARISON (average distance per resident, lower = better):")
print(f"    V1  largest-population (no optimization): {v1_avg:.3f} mi")
print(f"    Greedy (distance-reducing, heuristic):    {g_avg:.3f} mi")
print(f"    V2  OPTIMAL (this model):                 {avg_dist:.3f} mi")
print(f"\n    V2 improvement vs V1: {(v1_avg-avg_dist)/v1_avg*100:.1f}% less travel")
print(f"    V2 improvement vs greedy: {(g_avg-avg_dist)/g_avg*100:.1f}% less travel")
print("="*64)

json.dump({"built":built,"avg_dist":avg_dist,"total_travel":total_travel,
           "v1_avg":v1_avg,"greedy_avg":g_avg,"v1":v1,"greedy":greedy,
           "total_pop":total_pop,"M":M},
          open("v2_results.json","w"), indent=2)
