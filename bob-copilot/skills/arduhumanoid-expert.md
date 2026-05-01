# ArduHumanoid SITL Domain Expert

**Skill Type:** Domain Knowledge  
**Activation:** Automatic when working in humanoid-ardupilot-sitl project  
**Purpose:** Complete technical mastery of MAVLink-controlled bipedal humanoid robot simulation

---

## System Architecture (5 Interconnected Systems)

### 1. Gazebo Harmonic (Physics Simulation)
- **Engine:** DART physics, 4ms timestep (250 Hz)
- **Model:** 8-DOF bipedal humanoid (ArduBiped_Proto)
- **Mass:** 3.9 kg total (torso 2.5kg, thigh 0.5kg each, shin 0.3kg each, foot 0.15kg each)
- **Leg Geometry:** L1=L2=0.20m (thigh/shin), foot width 0.16m (hip separation)
- **CoM Height:** ~0.38m above ground
- **Joint Controllers:** PID (P=8, I=0.01, D=10)
- **IMU Sensor:** 1000 Hz on torso
- **Spawn Position:** (0, 0, 0.57) with 0.12 rad forward pitch (6.9°)
- **Foot Collision:** 18cm x 10cm, friction mu=1.0

### 2. ArduPilotPlugin (SDF Plugin)
- **Location:** Embedded in [`worlds/ardupilot_humanoid.sdf`](worlds/ardupilot_humanoid.sdf)
- **JSON Protocol:** 127.0.0.1:9002
- **Data Flow:**
  - **IN:** IMU data from Gazebo → ArduPilot
  - **OUT:** Servo PWM from ArduPilot → Joint angles
- **PWM Conversion Formula:** `angle = (pwm - 1500) / 500 * multiplier + offset`
- **Channel Mapping (4 channels only):**
  - CH0 → l_hip_pitch (mult=1.571, offset=-0.5)
  - CH1 → r_hip_pitch (mult=1.571, offset=-0.5)
  - CH2 → l_knee (mult=2.618, offset=-0.5)
  - CH3 → r_knee (mult=2.618, offset=-0.5)
- **Coordinate Transforms:**
  - `modelXYZToAirplaneXForwardZDown`: 0 0 0 180 0 0
  - `gazeboXYZToNED`: 0 0 0 180 0 90
  - **Purpose:** Gazebo (X-forward, Z-up) ↔ ArduPilot (X-forward, Z-down, NED)

### 3. ArduPilot Rover SITL (Flight Controller)
- **Mode:** Rover (NOT Copter - launch scripts are outdated)
- **EKF:** EKF3 enabled (AHRS_EKF_TYPE=10)
- **Attitude Estimation:** Pitch, roll, yaw from IMU fusion
- **Servo Output:** SRV_Channels (currently unused by Python controllers)
- **MAVLink:** UDP:14551 telemetry
- **Lua Scripting:** SCR_ENABLE=1 (capability exists, not implemented)
- **Parameters:** [`mav.parm`](mav.parm) (1404 lines, use line ranges when reading)

### 4. Python Gait Controllers (Current Implementation)
- **Connection:** pymavlink to UDP:14551
- **Control Path:** Python → Gazebo topics DIRECTLY (bypasses ArduPilot servo output)
- **Gazebo Topics:**
  - `/l_hip_pitch/cmd`
  - `/r_hip_pitch/cmd`
  - `/l_knee/cmd`
  - `/r_knee/cmd`
  - `/l_ankle/cmd` (fixed joint, commands ignored)
  - `/r_ankle/cmd` (fixed joint, commands ignored)

### 5. MAVLink Protocol (Intended, Not Implemented)
- **Goal:** MAVLink commands → ArduPilot Lua → SRV_Channels → ArduPilotPlugin → Gazebo
- **Missing:** GUIDED mode handler, waypoint navigation, Lua gait generation

---

## Joint Configuration & Kinematics

### Joint Limits (SDF)
```
l_hip_pitch:  [-1.571, 0.523] rad  (-90° to +30°)
r_hip_pitch:  [-1.571, 0.523] rad  (-90° to +30°)
l_knee:       [0.0, 2.618] rad     (0° to +150°)
r_knee:       [0.0, 2.618] rad     (0° to +150°)
l_knee_shin:  [0.0, 2.618] rad     (0° to +150°)
r_knee_shin:  [0.0, 2.618] rad     (0° to +150°)
l_ankle:      FIXED (type="fixed")
r_ankle:      FIXED (type="fixed")
```

### Canonical Standing Pose
```python
HIP_STAND  = -0.09  # rad
KNEE_STAND =  0.35  # rad
ANKLE_STAND = 0.0   # rad (fixed joint)
```
**CRITICAL:** This pose MUST match [`worlds/ardupilot_humanoid.sdf`](worlds/ardupilot_humanoid.sdf) initial_position

### Inverse Kinematics ([`scripts/inverse_kinematics.py`](scripts/inverse_kinematics.py))
- **Algorithm:** Geometric IK for planar 2R manipulator
- **Leg Lengths:** L1=L2=0.20m (must match SDF)
- **Ankle Compensation:** `ankle = -(hip_pitch + knee*0.3)`
- **Assumptions:** Hip joint at CoM height, foot at ground
- **Hip Roll:** [-0.4, 0.4] rad (NOT in current model - ZMP controller blocker)

---

## Controller Implementations

### Balance Controller ([`scripts/balance_controller.py`](scripts/balance_controller.py))
- **Purpose:** Simple standing balance only
- **Algorithm:** PID on pitch
- **Gains:** Kp=2.0, Ki=0.01, Kd=0.5 (STRONGER than gait controller)
- **Control Strategy:**
  - Primary: Hip pitch adjustment
  - Secondary: Ankle pitch (0.5x, but ankle is fixed so no effect)
- **Standing Pose:** hip=-0.09, knee=0.35, ankle=0.0

### Gait Controller ([`scripts/gait_controller.py`](scripts/gait_controller.py))
- **Purpose:** 6-phase walking gait with balance
- **Balance PID:** Kp=0.08, Ki=0.001, Kd=0.01 (WEAKER than balance_controller)
- **Gait Phases:** STAND → SHIFT_R → STEP_L → STAND → SHIFT_L → STEP_R
- **Phase Duration:** 3.0s each (very slow, intentional for stability)
- **Step Parameters:**
  - HIP_STEP=0.05 rad
  - KNEE_LIFT=0.55 rad
- **Startup Sequence (CRITICAL):**
  1. Pre-hold pose 40x before MAVLink (prevents fall during connection)
  2. Connect to MAVLink
  3. Kill [`startup.sh`](scripts/startup.sh)
  4. Hold pose 20x
  5. Calibrate standing pitch (20 samples)
  6. Stabilize 3s with balance
  7. Execute gait phases
- **Integral Reset:** Lines 97-98 reset integral between stabilize and gait (prevents lurch on first step)

### ZMP Preview Controller ([`scripts/zmp_gait_controller.py`](scripts/zmp_gait_controller.py))
- **Status:** INCOMPLETE - requires hip_roll joints NOT in current model
- **Algorithm:** LIPM (Linear Inverted Pendulum Model)
- **Preview Horizon:** 20 steps
- **Step Parameters:** length=0.12m, duration=0.6s, double support=0.1s
- **Dependencies:**
  - [`scripts/preview_control.py`](scripts/preview_control.py) - Discrete LQR with preview
  - [`scripts/foot.py`](scripts/foot.py) - Swing trajectory (sinusoidal, max_height=0.04m)
  - [`scripts/inverse_kinematics.py`](scripts/inverse_kinematics.py) - Leg IK
- **BLOCKER:** Hardcoded path line 6: `/home/neetamis/humanoid-ardupilot-sitl/scripts`

---

## Critical Gotchas & Non-Obvious Patterns

### 1. Multiple Standing Poses (INCONSISTENCY ALERT)
- **Canonical:** [`gait_controller.py`](scripts/gait_controller.py) hip=-0.09, knee=0.35 ✅
- **Matches:** [`startup.sh`](scripts/startup.sh) hip=-0.09, knee=0.35 ✅
- **Different:** [`startup_lock.py`](scripts/startup_lock.py) hip=-0.10, knee=0.30
- **Different:** [`startup_pose.sh`](scripts/startup_pose.sh) hip=-0.2, knee=0.4
- **Different:** [`hold_pose.py`](scripts/hold_pose.py) hip=-0.05, knee=0.1
- **Different:** [`startup_hold.py`](scripts/startup_hold.py) all joints=0.0
- **Rule:** ALWAYS use gait_controller.py pose as canonical

### 2. PWM Conversion Math (OFFSET SHIFTS NEUTRAL POINT)
**Formula:** `angle = (pwm - 1500) / 500 * multiplier + offset`

**Example (l_hip_pitch):**
- PWM 1000 → angle = (1000-1500)/500 * 1.571 + (-0.5) = -1.571 - 0.5 = -2.071 rad (clamped to -1.571)
- PWM 1500 → angle = (1500-1500)/500 * 1.571 + (-0.5) = 0.0 - 0.5 = **-0.5 rad** (NOT 0!)
- PWM 2000 → angle = (2000-1500)/500 * 1.571 + (-0.5) = 1.571 - 0.5 = 1.071 rad (clamped to 0.523)

**GOTCHA:** Offset=-0.5 means neutral PWM (1500) produces -0.5 rad, NOT 0 rad!

### 3. Python Controllers Bypass ArduPilot
- **Current:** Python → Gazebo topics directly
- **Intended:** Python → MAVLink → ArduPilot Lua → SRV_Channels → ArduPilotPlugin → Gazebo
- **Why Bypass:** Faster development iteration
- **Problem:** Defeats purpose of ArduPilot integration

### 4. Ankle Joints Are Fixed (But Controllers Don't Know)
- **SDF:** `<joint name="l_ankle" type="fixed">`
- **Controllers:** Still send commands to `/l_ankle/cmd`
- **Impact:** Commands ignored, but IK solver includes ankle compensation
- **Reason:** Future-proofing for when ankles become actuated

### 5. Duplicate Friction Tags (Parser Bug)
- **Location:** [`worlds/ardupilot_humanoid.sdf`](worlds/ardupilot_humanoid.sdf) lines 193, 201, 209, 220, 228, 236
- **Code:** `<friction>1.5</friction><friction>0.5</friction>`
- **Behavior:** Gazebo uses LAST value (0.5), first value ignored
- **Fix:** Remove duplicate tags

### 6. Initial Pitch Lean (CoM Compensation)
- **World file:** `<pose>0 0 0.57 0.12 0 0</pose>` (0.12 rad = 6.9° forward)
- **Purpose:** Compensates for CoM position, prevents backward fall on spawn
- **CRITICAL:** If mass distribution changes, MUST retune this value

### 7. Balance Integral Windup Prevention
- **Location:** [`gait_controller.py`](scripts/gait_controller.py) lines 97-98
- **Action:** Resets integral between stabilize and gait phases
- **Why:** Prevents carry-over of accumulated error from standing to walking
- **GOTCHA:** Removing this causes robot to lurch on first step

### 8. ZMP Controller Missing Joints
- **Problem:** [`zmp_gait_controller.py`](scripts/zmp_gait_controller.py) requires hip_roll joints
- **Reality:** Current model only has hip_pitch
- **Impact:** ZMP controller CANNOT run on current model
- **Fix Options:**
  1. Add hip_roll joints to SDF (preferred)
  2. Remove hip_roll from ZMP controller (degrades lateral stability)

### 9. Hardcoded Paths (Portability Killer)
- **Location:** [`zmp_gait_controller.py`](scripts/zmp_gait_controller.py) line 6
- **Code:** `sys.path.insert(0, '/home/neetamis/humanoid-ardupilot-sitl/scripts')`
- **Impact:** Breaks on any other system
- **Fix:** Use `sys.path.insert(0, os.path.dirname(__file__))`

### 10. Coordinate Frame Transforms (DO NOT TOUCH)
- **ArduPilotPlugin transforms:**
  - `modelXYZToAirplaneXForwardZDown`: 0 0 0 180 0 0
  - `gazeboXYZToNED`: 0 0 0 180 0 90
- **Purpose:** Gazebo (X-forward, Z-up) ↔ ArduPilot (X-forward, Z-down, NED)
- **CRITICAL:** Changing these breaks IMU data → robot falls immediately

---

## Known Failure Modes & Fixes

### 1. Robot Falls Immediately on Spawn
**Symptoms:** Robot collapses within 1 second of Gazebo start  
**Causes:**
- Initial pose doesn't match standing pose
- [`startup.sh`](scripts/startup.sh) not running
- Initial pitch lean (0.12 rad) wrong for CoM

**Fixes:**
1. Verify [`worlds/ardupilot_humanoid.sdf`](worlds/ardupilot_humanoid.sdf) initial_position = hip=-0.09, knee=0.35
2. Run `bash scripts/startup.sh &` before starting gait controller
3. Check spawn pose pitch = 0.12 rad

### 2. Robot Explodes (Joints Fly Apart)
**Symptoms:** Joints separate, robot fragments scatter  
**Causes:**
- Physics timestep too large
- Joint limits violated
- Insufficient damping

**Fixes:**
1. Keep max_step_size ≤ 0.004s in [`worlds/ardupilot_humanoid.sdf`](worlds/ardupilot_humanoid.sdf)
2. Clamp joint commands to limits before publishing
3. Increase joint damping in SDF

### 3. Gait Controller Connects But Robot Doesn't Move
**Symptoms:** MAVLink connected, no joint movement  
**Causes:**
- Gazebo topics not subscribed (plugin not loaded)
- ArduPilotPlugin failed to initialize

**Fixes:**
1. Run `python scripts/check_config.py` to verify topics
2. Check Gazebo console for plugin load errors
3. Restart Gazebo if topics missing

### 4. Balance Controller Oscillates
**Symptoms:** Robot rocks back and forth, increasing amplitude  
**Causes:**
- PID gains too high
- Derivative kick
- Insufficient damping

**Fixes:**
1. Reduce Kp (currently 2.0 in [`balance_controller.py`](scripts/balance_controller.py), 0.08 in [`gait_controller.py`](scripts/gait_controller.py))
2. Add derivative filtering (low-pass filter on error derivative)
3. Increase joint damping in SDF

### 5. Walking Gait Unstable (Falls After 1-2 Steps)
**Symptoms:** Robot takes 1-2 steps then falls  
**Causes:**
- Phase timing too fast (3.0s is intentionally slow)
- Step length too large (0.05 rad hip displacement)
- Balance gains too weak (Kp=0.08)
- No ZMP stability margin
- No lateral (roll) balance control

**Fixes:**
1. Implement proper ZMP preview control
2. Add hip_roll joints for lateral balance
3. Tune gait parameters empirically
4. Increase balance PID gains during swing phase
5. Add ZMP stability margin check

### 6. MAVLink Connection Timeout
**Symptoms:** Python controller can't connect to UDP:14551  
**Causes:**
- ArduPilot not outputting to UDP:14551
- Firewall blocking UDP

**Fixes:**
1. In MAVProxy: `output add 127.0.0.1:14551`
2. Or use `--out=udp:127.0.0.1:14551` in sim_vehicle.py
3. Check firewall rules

### 7. ZMP Controller Import Error
**Symptoms:** `ModuleNotFoundError` when running [`zmp_gait_controller.py`](scripts/zmp_gait_controller.py)  
**Cause:** Hardcoded path `/home/neetamis/...` doesn't exist  
**Fix:** Change line 6 to `sys.path.insert(0, os.path.dirname(__file__))`

### 8. Foot Slipping
**Symptoms:** Feet slide during stance phase  
**Cause:** Friction coefficient too low  
**Fix:** Increase `<mu>` in foot collision (currently 1.0, try 1.5-2.0)

### 9. Knee Hyperextension
**Symptoms:** Knee bends backward (negative angle)  
**Cause:** IK solver allows knee < 0  
**Fix:** Already clamped in [`inverse_kinematics.py`](scripts/inverse_kinematics.py) line 17, but verify commands

### 10. ArduPilot EKF Not Converging
**Symptoms:** ATTITUDE messages show NaN or unstable values  
**Causes:**
- IMU data quality poor
- Coordinate transform wrong
- EKF parameters misconfigured

**Fixes:**
1. Verify `AHRS_EKF_TYPE=10` in [`mav.parm`](mav.parm)
2. Check coordinate transforms in ArduPilotPlugin
3. Verify IMU update_rate=1000 Hz in SDF

---

## Current Project Status

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
1. **Add Hip Roll Joints** - Modify SDF, update plugin channels, update IK solver
2. **Stabilize Walking Gait** - ZMP stability margin, lateral balance, tune timing
3. **Integrate Lua Scripting** - Port Python logic to Lua, use SRV_Channels
4. **Implement MAVLink Control** - GUIDED mode, waypoint following, AUTO mode
5. **Optimize Performance** - Profile timing, reduce latency, tune PID

---

## Quick Reference Tables

### Network Ports
| Connection | Protocol | Address | Purpose |
|------------|----------|---------|---------|
| Gazebo → ArduPilot | JSON | 127.0.0.1:9002 | IMU data, servo PWM |
| ArduPilot → Python | MAVLink | UDP:14551 | Telemetry, attitude |
| Gazebo Topics | gz-transport | local | Joint commands |

### Key Parameters
| Parameter | Value | Location |
|-----------|-------|----------|
| Physics dt | 0.004s (250 Hz) | [`worlds/ardupilot_humanoid.sdf`](worlds/ardupilot_humanoid.sdf) |
| Control dt | 0.02s (50 Hz) | Python controllers |
| IMU rate | 1000 Hz | SDF sensor config |
| Joint PID | P=8, I=0.01, D=10 | SDF joint controllers |
| Balance PID (gait) | P=0.08, Ki=0.001, Kd=0.01 | [`gait_controller.py`](scripts/gait_controller.py) |
| Balance PID (balance) | P=2.0, Ki=0.01, Kd=0.5 | [`balance_controller.py`](scripts/balance_controller.py) |

### File Priority (What to Use)
| Purpose | Use This | NOT This |
|---------|----------|----------|
| World file | [`worlds/ardupilot_humanoid.sdf`](worlds/ardupilot_humanoid.sdf) | [`models/biped_robot/model.sdf`](models/biped_robot/model.sdf) |
| Standing pose | [`gait_controller.py`](scripts/gait_controller.py) | Other startup scripts |
| ArduPilot params | [`mav.parm`](mav.parm) | [`params/biped.param`](params/biped.param) |
| Startup script | [`startup.sh`](scripts/startup.sh) | Other startup_*.py/sh |

---

## Critical Warnings (DO NOT VIOLATE)

1. **DO NOT** change joint limits without updating [`inverse_kinematics.py`](scripts/inverse_kinematics.py)
2. **DO NOT** change mass distribution without retuning initial pitch lean (0.12 rad)
3. **DO NOT** increase physics timestep above 0.004s (robot will explode)
4. **DO NOT** run multiple controllers simultaneously (they will fight)
5. **DO NOT** modify ArduPilotPlugin coordinate transforms (IMU will break)
6. **ALWAYS** run [`startup.sh`](scripts/startup.sh) before [`gait_controller.py`](scripts/gait_controller.py)
7. **ALWAYS** verify Gazebo topics subscribed before starting controller
8. **REMEMBER** Python controllers bypass ArduPilot (not final architecture)

---

## Expert Decision-Making Framework

When answering questions about this codebase, apply this framework:

### 1. Identify System Layer
- Is this about Gazebo physics, ArduPilot, Python controllers, or integration?
- Which files are involved?

### 2. Check for Gotchas
- Does this involve one of the 10 critical gotchas?
- Are there inconsistencies (e.g., multiple standing poses)?

### 3. Verify Current Status
- Is this feature working, incomplete, or broken?
- What's the current vs. intended architecture?

### 4. Consider Failure Modes
- Could this change trigger a known failure mode?
- What are the breaking changes?

### 5. Provide Complete Context
- Reference specific files with line numbers
- Explain WHY, not just WHAT
- Warn about related systems that might break

---

**Skill Activation Confirmed** - You are now a senior robotics engineer on the ArduHumanoid SITL project with complete system knowledge. Answer any question about this codebase with confidence and precision.