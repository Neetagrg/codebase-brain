# AGENTS.md - ArduHumanoid SITL Complete System Documentation

**Last Updated:** 2026-05-01  
**Purpose:** Complete technical context for developers and AI agents working on this MAVLink-controlled bipedal humanoid robot simulation.

---

## 🎯 60-Second Context

**What:** 8-DOF bipedal humanoid robot running on ArduPilot Rover SITL + Gazebo Harmonic, controlled via MAVLink commands.

**Status:** 
- ✅ Robot model loads and stands in Gazebo
- ✅ ArduPilot SITL connects via JSON protocol
- ✅ IMU feedback working (EKF3 attitude estimation)
- ✅ Joint position control via Gazebo topics
- ✅ Balance controller maintains standing pose
- ⚠️ Gait controller exists but walking not stable
- ❌ ZMP preview controller incomplete (missing hip_roll joints)
- ❌ Lua scripting integration not implemented
- ❌ MAVLink waypoint navigation not implemented

**Critical Path:** Python gait controllers → Gazebo joint topics → ArduPilotPlugin → ArduPilot SITL (sensor fusion only, no control loop yet)

---

## 📊 Complete Signal Chain: MAVLink Command → Joint Movement

### Current Architecture (Python-Controlled)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. GAZEBO HARMONIC (Physics Simulation)                        │
│    - DART physics engine (4ms timestep)                         │
│    - 8-DOF humanoid model (ArduBiped_Proto)                     │
│    - Joint position controllers (PID: P=8, I=0.01, D=10)        │
│    - IMU sensor on torso (1000 Hz)                              │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ├─ IMU data (JSON) ──────────────────────┐
                 │                                         │
                 ├─ Joint commands (Gazebo topics) ◄──────┤
                 │   /l_hip_pitch/cmd                     │
                 │   /r_hip_pitch/cmd                     │
                 │   /l_knee/cmd                          │
                 │   /r_knee/cmd                          │
                 │   /l_ankle/cmd (fixed joint)           │
                 │   /r_ankle/cmd (fixed joint)           │
                 │                                         │
┌────────────────▼─────────────────────────────────────────────────┐
│ 2. ARDUPILOT PLUGIN (ArduPilotPlugin in model.sdf)             │
│    - Receives IMU data from Gazebo                              │
│    - Sends to ArduPilot via JSON (127.0.0.1:9002)               │
│    - Receives servo PWM from ArduPilot (channels 0-3)           │
│    - Converts PWM → joint angles via multiplier/offset          │
│    - Publishes to Gazebo joint topics                           │
│                                                                  │
│    PWM Conversion Formula:                                       │
│    angle = (pwm - 1500) / 500 * multiplier + offset            │
│                                                                  │
│    Channel Mapping:                                              │
│    CH0 → l_hip_pitch  (mult=1.571, offset=-0.5)                │
│    CH1 → r_hip_pitch  (mult=1.571, offset=-0.5)                │
│    CH2 → l_knee       (mult=2.618, offset=-0.5)                │
│    CH3 → r_knee       (mult=2.618, offset=-0.5)                │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 │ JSON Protocol (IMU → ArduPilot)
                 │ JSON Protocol (Servo PWM ← ArduPilot)
                 │
┌────────────────▼─────────────────────────────────────────────────┐
│ 3. ARDUPILOT ROVER SITL (Flight Controller)                    │
│    - EKF3 sensor fusion (AHRS_EKF_TYPE=10)                      │
│    - Attitude estimation from IMU                                │
│    - Servo output channels (SRV_Channels)                        │
│    - MAVLink telemetry (UDP:14551)                               │
│    - Lua scripting capability (SCR_ENABLE=1, not used yet)      │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 │ MAVLink (UDP:14551)
                 │ ATTITUDE messages (pitch, roll, yaw)
                 │
┌────────────────▼─────────────────────────────────────────────────┐
│ 4. PYTHON GAIT CONTROLLER (gait_controller.py)                 │
│    - Reads ATTITUDE messages via pymavlink                       │
│    - Implements balance PID (Kp=0.08, Ki=0.001, Kd=0.01)        │
│    - Generates gait phases (6-phase walking cycle)               │
│    - Sends joint commands directly to Gazebo topics              │
│    - BYPASSES ArduPilot servo output entirely                    │
└──────────────────────────────────────────────────────────────────┘
```

### Intended Architecture (Not Yet Implemented)

```
MAVLink Command (GUIDED mode, waypoint)
    ↓
ArduPilot Rover SITL
    ↓
Lua Script (humanoid.lua) - ZMP + IK gait generation
    ↓
SRV_Channels (servo PWM output)
    ↓
ArduPilotPlugin (PWM → angle conversion)
    ↓
Gazebo Joint Position Controllers
    ↓
DART Physics → Robot Walks
```

---

## 📁 Complete File Inventory

### `/models/biped_robot/`

#### `model.config`
- **Purpose:** Gazebo model metadata
- **Breaking Changes:** Changing `<sdf version>` requires SDF syntax updates
- **Dependencies:** Referenced by Gazebo when loading model

#### `model.sdf`
- **Purpose:** Robot definition (DEPRECATED - use worlds/ardupilot_humanoid.sdf instead)
- **Key Details:**
  - 8 DOF: 4 per leg (hip_pitch, knee, knee_shin, ankle=fixed)
  - Total mass: 3.9 kg
  - Leg geometry: L1=L2=0.20m (thigh/shin)
  - ArduPilotPlugin configured for 4 channels only
  - **GOTCHA:** This file has lower P_gain (5.0) than world file (8.0)
- **Breaking Changes:** 
  - Changing joint limits breaks IK solver assumptions
  - Changing masses affects CoM and balance
  - Plugin channel mapping must match ArduPilot params

### `/worlds/`

#### `ardupilot_humanoid.sdf`
- **Purpose:** PRIMARY world file - use this, not model.sdf
- **Key Details:**
  - Physics: 4ms timestep, DART engine
  - Robot spawned at (0, 0, 0.57) with 0.12 rad pitch
  - Enhanced foot collision (18cm x 10cm, mu=1.0)
  - Joint controllers: P=8, I=0.01, D=10
  - Initial pose: hip=-0.09, knee=0.35
- **Breaking Changes:**
  - Initial pose must match gait controller standing pose
  - Physics timestep affects stability (too large = explosions)
  - Friction coefficients critical for foot contact
- **GOTCHA:** Duplicate friction tags in joint dynamics (line 193, 201, etc.)

#### `ardupilot_humanoid.sdf.bak`
- **Purpose:** Backup of previous world configuration
- **Safe to delete:** Yes, but keep for rollback reference

### `/params/`

#### `biped.param`
- **Purpose:** ArduPilot servo parameters (UNUSED - overridden by mav.parm)
- **Key Details:** Basic servo config (P=5.0, D=0.1, trim=1500)
- **Breaking Changes:** None - file not loaded in current workflow

#### `mav.parm`
- **Purpose:** Complete ArduPilot parameter set (1404 lines)
- **Key Details:**
  - AHRS_EKF_TYPE=10 (EKF3 enabled)
  - Rover-specific attitude control params
  - Servo output configuration
- **Breaking Changes:**
  - Changing EKF params affects attitude estimation
  - AHRS_ORIENTATION must match Gazebo coordinate transform
- **GOTCHA:** Large file, use line ranges when reading

### `/scripts/`

#### `balance_controller.py`
- **Purpose:** Simple standing balance controller
- **Algorithm:** PID on pitch (Kp=2.0, Ki=0.01, Kd=0.5)
- **Control:** Hip pitch (primary) + ankle pitch (secondary, 0.5x)
- **Standing Pose:** hip=-0.09, knee=0.35, ankle=0.0
- **Breaking Changes:**
  - Gains tuned for current mass distribution
  - Standing pose must match world file initial_position
- **GOTCHA:** Stronger gains than gait controller

#### `gait_controller.py`
- **Purpose:** 6-phase walking gait with balance
- **Algorithm:**
  - Balance PID (Kp=0.08, Ki=0.001, Kd=0.01) - weaker than balance_controller
  - 6 gait phases: STAND → SHIFT_R → STEP_L → STAND → SHIFT_L → STEP_R
  - Phase duration: 3.0s each
  - Step parameters: HIP_STEP=0.05, KNEE_LIFT=0.55
- **Startup Sequence:**
  1. Pre-hold pose 40x before MAVLink (prevents fall during connection)
  2. Connect to MAVLink
  3. Kill startup.sh
  4. Hold pose 20x
  5. Calibrate standing pitch (20 samples)
  6. Stabilize 3s with balance
  7. Execute gait phases
- **Breaking Changes:**
  - Phase timing affects stability
  - Balance gains must be tuned with gait parameters
- **GOTCHA:** Resets balance integral between stabilize and gait phases

#### `zmp_gait_controller.py`
- **Purpose:** Advanced ZMP preview control walking (INCOMPLETE)
- **Algorithm:**
  - LIPM (Linear Inverted Pendulum Model)
  - Preview horizon: 20 steps
  - Step length: 0.12m, duration: 0.6s
  - Double support: 0.1s
- **Dependencies:**
  - preview_control.py (LIPM controller)
  - foot.py (swing trajectory)
  - inverse_kinematics.py (leg IK)
- **Breaking Changes:** CRITICAL - requires hip_roll joints not in current model
- **GOTCHA:** Hardcoded path `/home/neetamis/...` (line 6) - will break on other systems

#### `inverse_kinematics.py`
- **Purpose:** 2-link leg IK solver
- **Algorithm:**
  - Geometric IK for planar 2R manipulator
  - L1=L2=0.20m (thigh/shin lengths)
  - Ankle compensation: ankle = -(hip_pitch + knee*0.3)
- **Joint Limits:**
  - hip_pitch: [-1.57, 0.52] rad (-90° to +30°)
  - knee: [0.0, 2.618] rad (0° to +150°)
  - ankle: [-0.5, 0.5] rad
  - hip_roll: [-0.4, 0.4] rad
- **Breaking Changes:**
  - Leg lengths must match SDF model
  - Joint limits must match SDF
- **GOTCHA:** Assumes hip joint at CoM height, foot at ground

#### `preview_control.py`
- **Purpose:** LIPM preview controller implementation
- **Algorithm:**
  - Discrete-time LQR with preview
  - Solves discrete algebraic Riccati equation
  - Computes preview gains for N-step horizon
- **Parameters:**
  - dt=0.02s, com_height=0.35m, preview_horizon=20
  - Qe=1.0 (tracking weight), R=1e-6 (control weight)
- **Breaking Changes:**
  - CoM height must match robot geometry
  - Preview horizon affects computational cost
- **GOTCHA:** Requires scipy for solve_discrete_are

#### `foot.py`
- **Purpose:** Swing foot trajectory generation
- **Algorithm:**
  - Sinusoidal height profile: z = h*sin(π*phase)
  - Linear x progression
  - Constant y (lateral position)
- **Parameters:**
  - max_height=0.04m (swing clearance)
  - duration=0.6s
- **Breaking Changes:** Height must clear ground obstacles

#### `hold_pose.py`
- **Purpose:** Simple pose holder (UNUSED)
- **Pose:** hip=-0.05, knee=0.1, ankle=0.05
- **GOTCHA:** Different pose than gait_controller standing pose

#### `startup.sh`
- **Purpose:** Hold standing pose until gait controller starts
- **Pose:** hip=-0.09, knee=0.35, ankle=0.0 (matches gait_controller)
- **Usage:** Run in background, killed by gait_controller after MAVLink connection
- **Breaking Changes:** Pose must match gait controller exactly

#### `startup_hold.py`
- **Purpose:** Python version of startup pose holder
- **Pose:** All joints to 0.0 (DIFFERENT from startup.sh)
- **GOTCHA:** Inconsistent with other startup scripts

#### `startup_lock.py`
- **Purpose:** Lock joints immediately after Gazebo starts
- **Pose:** hip=-0.10, knee=0.30, ankle=0.10
- **Usage:** Run once, exits after 30 iterations (1.5s)
- **GOTCHA:** Yet another different standing pose

#### `startup_pose.sh`
- **Purpose:** Bash version of startup lock
- **Pose:** hip=-0.2, knee=0.4
- **GOTCHA:** More aggressive pose than others

#### `launch.sh`
- **Purpose:** Instructions for manual 3-terminal launch
- **GOTCHA:** References ArduCopter instead of Rover (outdated)

#### `start_all.sh`
- **Purpose:** Kill all processes and show manual launch instructions
- **GOTCHA:** Also references ArduCopter (outdated)

#### `calculate_com.py`
- **Purpose:** Calculate center of mass from URDF
- **GOTCHA:** References `humanoid_proto.urdf` which doesn't exist (SDF model only)

#### `validate_inertia.py`
- **Purpose:** Advanced CoM validator with joint transforms
- **Features:**
  - Builds kinematic tree
  - Computes world-frame CoM
  - Validates inertia triangle inequality
  - Checks ODE stability floor (1e-4 kg·m²)
- **GOTCHA:** Also references non-existent URDF file

#### `check_config.py`
- **Purpose:** Verify Gazebo joint topics have subscribers
- **Topics Checked:**
  - /l_hip_pitch/cmd
  - /r_hip_pitch/cmd
  - /l_knee/cmd
  - /r_knee/cmd
  - /l_ankle/cmd
  - /r_ankle/cmd
- **Usage:** Diagnostic tool to verify Gazebo plugin loaded correctly

#### `print_tree.py`
- **Purpose:** Print URDF kinematic tree
- **GOTCHA:** References non-existent URDF file

### `/terrain/`

#### `S36E149.DAT`
- **Purpose:** Terrain elevation data (likely unused)
- **Safe to delete:** Probably, but keep for future terrain features

---

## 🔧 Non-Obvious Patterns & Gotchas

### 1. **Multiple Standing Poses**
**Problem:** 5 different standing poses across scripts:
- `gait_controller.py`: hip=-0.09, knee=0.35
- `startup.sh`: hip=-0.09, knee=0.35 ✅ (matches gait)
- `startup_lock.py`: hip=-0.10, knee=0.30
- `startup_pose.sh`: hip=-0.2, knee=0.4
- `hold_pose.py`: hip=-0.05, knee=0.1

**Solution:** Use `gait_controller.py` pose as canonical. Others are experimental.

### 2. **ArduPilot Plugin PWM Conversion**
**Formula:** `angle = (pwm - 1500) / 500 * multiplier + offset`

**Example (l_hip_pitch):**
- PWM range: [1000, 2000]
- multiplier: 1.571
- offset: -0.5
- PWM 1000 → angle = -1.571 - 0.5 = -2.071 rad (clamped to -1.571)
- PWM 1500 → angle = 0.0 - 0.5 = -0.5 rad
- PWM 2000 → angle = 1.571 - 0.5 = 1.071 rad (clamped to 0.523)

**GOTCHA:** Offset shifts neutral point, not just range!

### 3. **Python Controllers Bypass ArduPilot**
**Current:** Python → Gazebo topics directly
**Intended:** Python → MAVLink → ArduPilot → Gazebo

**Why:** Faster development, but defeats purpose of ArduPilot integration.

### 4. **Ankle Joints Are Fixed**
**SDF:** `<joint name="l_ankle" type="fixed">`
**Controllers:** Still send commands to `/l_ankle/cmd`

**Impact:** Ankle commands ignored, but IK solver includes ankle compensation.

### 5. **Duplicate Friction Tags**
**Location:** `worlds/ardupilot_humanoid.sdf` lines 193, 201, 209, 220, 228, 236
**Code:** `<friction>1.5</friction><friction>0.5</friction>`

**Impact:** Gazebo uses last value (0.5). First value ignored.

### 6. **Initial Pitch Lean**
**World file:** `<pose>0 0 0.57 0.12 0 0</pose>` (0.12 rad = 6.9° forward pitch)

**Purpose:** Compensates for CoM position, prevents backward fall on spawn.

**GOTCHA:** If you change mass distribution, must retune this value.

### 7. **Balance Integral Windup**
**Problem:** `gait_controller.py` resets integral between stabilize and gait phases (lines 97-98)

**Why:** Prevents carry-over of accumulated error from standing to walking.

**GOTCHA:** If you remove this, robot will lurch on first step.

### 8. **ZMP Controller Missing Joints**
**Problem:** `zmp_gait_controller.py` requires hip_roll joints
**Reality:** Current model only has hip_pitch

**Impact:** ZMP controller cannot run on current model.

**Fix Required:** Add hip_roll joints to SDF model, or remove hip_roll from ZMP controller.

### 9. **Hardcoded Paths**
**Location:** `zmp_gait_controller.py` line 6
**Code:** `sys.path.insert(0, '/home/neetamis/humanoid-ardupilot-sitl/scripts')`

**Impact:** Breaks on any other system.

**Fix:** Use relative imports or `os.path.dirname(__file__)`.

### 10. **Coordinate Frame Transforms**
**ArduPilotPlugin:**
- `modelXYZToAirplaneXForwardZDown`: 0 0 0 180 0 0
- `gazeboXYZToNED`: 0 0 0 180 0 90

**Purpose:** Convert between Gazebo (X-forward, Z-up) and ArduPilot (X-forward, Z-down, NED frame).

**GOTCHA:** If you change these, IMU data will be wrong and robot will fall.

---

## ⚠️ Known Failure Modes

### 1. **Robot Falls Immediately on Spawn**
**Cause:** Initial pose doesn't match standing pose, or startup.sh not running
**Fix:** 
- Ensure world file initial_position matches gait controller standing pose
- Run `startup.sh` in background before starting gait controller
- Check initial pitch lean (0.12 rad) is correct for CoM

### 2. **Robot Explodes (Joints Fly Apart)**
**Cause:** Physics timestep too large, or joint limits violated
**Fix:**
- Keep max_step_size ≤ 0.004s
- Check joint commands within limits
- Increase joint damping if oscillating

### 3. **Gait Controller Connects But Robot Doesn't Move**
**Cause:** Gazebo topics not subscribed (plugin not loaded)
**Fix:**
- Run `check_config.py` to verify topics
- Restart Gazebo if topics missing
- Check ArduPilotPlugin loaded in world file

### 4. **Balance Controller Oscillates**
**Cause:** PID gains too high, or derivative kick
**Fix:**
- Reduce Kp (currently 2.0 in balance_controller, 0.08 in gait_controller)
- Add derivative filtering
- Increase damping in joint dynamics

### 5. **Walking Gait Unstable**
**Cause:** Multiple factors
- Phase timing too fast (3.0s is very slow)
- Step length too large (0.05 rad hip displacement)
- Balance gains too weak (Kp=0.08)
- No ZMP stability margin

**Fix:**
- Implement proper ZMP preview control
- Add hip_roll joints for lateral balance
- Tune gait parameters empirically
- Increase balance PID gains during swing phase

### 6. **MAVLink Connection Timeout**
**Cause:** ArduPilot not outputting to UDP:14551
**Fix:**
- In MAVProxy: `output add 127.0.0.1:14551`
- Or use `--out=udp:127.0.0.1:14551` in sim_vehicle.py

### 7. **ZMP Controller Import Error**
**Cause:** Hardcoded path doesn't exist
**Fix:** Change line 6 to relative import or correct path

### 8. **Foot Slipping**
**Cause:** Friction coefficient too low
**Fix:** Increase `<mu>` in foot collision (currently 1.0, try 1.5-2.0)

### 9. **Knee Hyperextension**
**Cause:** IK solver allows knee < 0
**Fix:** Already clamped in inverse_kinematics.py (line 17), but check commands

### 10. **ArduPilot EKF Not Converging**
**Cause:** IMU data quality or coordinate transform wrong
**Fix:**
- Check `AHRS_EKF_TYPE=10` (EKF3)
- Verify coordinate transforms in ArduPilotPlugin
- Check IMU sensor update_rate (1000 Hz)

---

## 📈 Current Status & Next Steps

### ✅ What Works
1. Gazebo simulation loads and runs stably
2. Robot model physics (mass, inertia, collisions)
3. ArduPilot SITL connects via JSON protocol
4. IMU data flows: Gazebo → ArduPilot → MAVLink
5. EKF3 attitude estimation (pitch, roll, yaw)
6. Balance controller maintains standing pose
7. Gait controller executes 6-phase walking cycle (but unstable)
8. Joint position control via Gazebo topics
9. Startup scripts prevent fall during initialization

### ⚠️ What's Incomplete
1. Walking gait not stable (falls after 1-2 steps)
2. ZMP preview controller missing hip_roll joints
3. No lateral (roll) balance control
4. Lua scripting not integrated
5. ArduPilot servo output not used (Python bypasses it)
6. No MAVLink command interface (GUIDED mode, waypoints)

### ❌ What Doesn't Work
1. Autonomous walking for >3 steps
2. MAVLink waypoint navigation
3. ZMP controller (requires model changes)
4. Lua gait generation
5. ArduPilot-controlled locomotion

### 🎯 Next Steps (Priority Order)

1. **Add Hip Roll Joints**
   - Modify `worlds/ardupilot_humanoid.sdf`
   - Add l_hip_roll, r_hip_roll revolute joints
   - Update ArduPilotPlugin channel mapping (CH4, CH5)
   - Update IK solver to include roll

2. **Stabilize Walking Gait**
   - Implement ZMP stability margin check
   - Add lateral balance (hip roll control)
   - Tune gait timing (reduce from 3.0s to 0.6-1.0s)
   - Increase balance PID gains during swing phase

3. **Integrate Lua Scripting**
   - Port gait_controller.py logic to Lua
   - Use SRV_Channels for servo output
   - Test ArduPilot → Gazebo control loop
   - Remove Python bypass

4. **Implement MAVLink Control**
   - Add GUIDED mode handler in Lua
   - Convert velocity commands to gait parameters
   - Implement waypoint following
   - Add AUTO mode support

5. **Optimize Performance**
   - Profile control loop timing
   - Reduce Gazebo topic latency
   - Tune PID gains for faster response
   - Add feedforward terms

---

## 🔍 Quick Reference

### Standing Pose (Canonical)
```python
HIP_STAND  = -0.09  # rad
KNEE_STAND =  0.35  # rad
ANKLE_STAND = 0.0   # rad (fixed joint)
```

### Joint Limits (SDF)
```
l_hip_pitch:  [-1.571, 0.523] rad  (-90° to +30°)
l_knee:       [0.0, 2.618] rad     (0° to +150°)
l_knee_shin:  [0.0, 2.618] rad     (0° to +150°)
l_ankle:      fixed
```

### Robot Geometry
```
Total Mass:    3.9 kg
Torso:         2.5 kg
Thigh (each):  0.5 kg
Shin (each):   0.3 kg
Foot (each):   0.15 kg
Leg Length:    L1=L2=0.20m
Foot Width:    0.16m (hip separation)
CoM Height:    ~0.38m above ground
```

### Network Ports
```
Gazebo → ArduPilot:  JSON on 127.0.0.1:9002
ArduPilot → Python:  MAVLink on UDP:14551
Gazebo Topics:       /l_hip_pitch/cmd, etc.
```

### Key Parameters
```
Physics dt:        0.004s (250 Hz)
Control dt:        0.02s (50 Hz)
IMU rate:          1000 Hz
Joint PID:         P=8, I=0.01, D=10
Balance PID:       P=0.08, Ki=0.001, Kd=0.01 (gait)
                   P=2.0, Ki=0.01, Kd=0.5 (balance)
```

---

## 🚨 Critical Warnings

1. **DO NOT** change joint limits without updating IK solver
2. **DO NOT** change mass distribution without retuning initial pitch lean
3. **DO NOT** increase physics timestep above 0.004s (robot will explode)
4. **DO NOT** run multiple controllers simultaneously (they will fight)
5. **DO NOT** modify ArduPilotPlugin coordinate transforms (IMU will break)
6. **ALWAYS** run startup.sh before gait_controller.py
7. **ALWAYS** verify Gazebo topics subscribed before starting controller
8. **REMEMBER** Python controllers bypass ArduPilot (not final architecture)

---

## 📚 External Dependencies

- **Gazebo Harmonic** (gz-sim8)
- **ArduPilot** (Rover SITL)
- **ardupilot_gazebo** plugin
- **Python 3** with pymavlink, numpy, scipy
- **MAVProxy** (optional, for manual control)

---

**End of AGENTS.md** - You now have complete context. Good luck! 🚀