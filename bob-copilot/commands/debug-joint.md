# debug-joint

**Purpose:** Diagnose why a specific joint isn't responding to commands.

**Usage:** `/debug-joint <joint_name>`

**Example:** `/debug-joint l_hip_pitch`

---

## What This Command Does

Given a joint name (e.g., `l_hip_pitch`, `r_knee`, `l_ankle`), this command traces the complete signal path from Python controller to physical joint movement, checking every configuration point where the joint could fail.

---

## Diagnostic Checklist

### 1. **SDF Joint Definition** (`worlds/ardupilot_humanoid.sdf`)

**Check:**
- Joint exists in `<model name="ArduBiped_Proto">`
- Joint type: `revolute` (movable) or `fixed` (immovable)
- Joint limits: `<lower>` and `<upper>` bounds
- Joint axis: `<xyz>` direction vector
- Joint dynamics: `<damping>` and `<friction>` values
- Initial position: `<initial_position>` value

**Common Issues:**
- **Fixed joint:** If `type="fixed"`, joint cannot move (e.g., ankle joints)
- **Inverted limits:** `<lower>` > `<upper>` causes Gazebo errors
- **Zero damping:** Can cause oscillations or instability
- **Duplicate friction tags:** Lines 193, 201, 209, 220, 228, 236 have duplicates (Gazebo uses last value)

**Search Pattern:**
```xml
<joint name="<joint_name>" type="revolute">
  <pose>...</pose>
  <parent>...</parent>
  <child>...</child>
  <axis>
    <xyz>...</xyz>
    <limit>
      <lower>-1.571</lower>
      <upper>0.523</upper>
    </limit>
    <dynamics>
      <damping>0.1</damping>
      <friction>0.5</friction>
    </dynamics>
  </axis>
</joint>
```

---

### 2. **Gazebo Joint Controller** (`worlds/ardupilot_humanoid.sdf`)

**Check:**
- Plugin exists: `<plugin filename="gz-sim-joint-position-controller-system">`
- Joint name matches: `<joint_name>` tag
- Topic name: `<topic>` (should be `/<joint_name>/cmd`)
- PID gains: `<p_gain>8</p_gain>`, `<i_gain>0.01</i_gain>`, `<d_gain>10</d_gain>`
- Initial target: `<initial_position>` (should match standing pose)

**Common Issues:**
- **Topic mismatch:** Topic name doesn't match what Python publishes to
- **Low P gain:** P < 5 causes sluggish response (model.sdf has P=5, world file has P=8)
- **Missing plugin:** Controller not loaded, joint won't respond
- **Wrong initial position:** Robot falls immediately on spawn

**Search Pattern:**
```xml
<plugin filename="gz-sim-joint-position-controller-system" name="gz::sim::systems::JointPositionController">
  <joint_name>l_hip_pitch</joint_name>
  <topic>/l_hip_pitch/cmd</topic>
  <p_gain>8</p_gain>
  <i_gain>0.01</i_gain>
  <d_gain>10</d_gain>
  <initial_position>-0.09</initial_position>
</plugin>
```

---

### 3. **ArduPilotPlugin Channel Mapping** (`worlds/ardupilot_humanoid.sdf`)

**Check:**
- Plugin exists: `<plugin filename="ArduPilotPlugin" name="ardupilot_plugin">`
- Channel mapping: `<control channel="N">` block
- Joint name matches: `<jointName>` tag
- Multiplier: `<multiplier>` (converts PWM range to angle range)
- Offset: `<offset>` (shifts neutral point)
- PWM limits: `<servo_min>1000</servo_min>`, `<servo_max>2000</servo_max>`

**PWM Conversion Formula:**
```
angle = (pwm - 1500) / 500 * multiplier + offset
```

**Channel Mapping (Current):**
- CH0 → `l_hip_pitch` (mult=1.571, offset=-0.5)
- CH1 → `r_hip_pitch` (mult=1.571, offset=-0.5)
- CH2 → `l_knee` (mult=2.618, offset=-0.5)
- CH3 → `r_knee` (mult=2.618, offset=-0.5)
- CH4-CH7 → **NOT MAPPED** (hip_roll joints don't exist yet)

**Common Issues:**
- **Joint not mapped:** Only 4 channels configured (hip_pitch, knee only)
- **Wrong multiplier:** Doesn't match joint limits (hip: 1.571 rad = 90°, knee: 2.618 rad = 150°)
- **Offset confusion:** Offset shifts neutral point, not just range (PWM 1500 → angle = offset)
- **Ankle joints:** Fixed joints, commands ignored even if mapped

**Search Pattern:**
```xml
<control channel="0">
  <jointName>l_hip_pitch</jointName>
  <multiplier>1.571</multiplier>
  <offset>-0.5</offset>
  <servo_min>1000</servo_min>
  <servo_max>2000</servo_max>
</control>
```

---

### 4. **Python Controller Commands** (`scripts/gait_controller.py`, `scripts/balance_controller.py`)

**Check:**
- Topic publisher exists: `gz.transport.Node().advertise()`
- Topic name matches: `/<joint_name>/cmd`
- Message type: `gz.msgs.Double`
- Command within limits: Check against SDF joint limits
- Controller running: Process active and connected to MAVLink

**Common Issues:**
- **Topic name typo:** Python publishes to wrong topic
- **No subscriber:** Gazebo plugin not loaded (run `check_config.py`)
- **Command out of bounds:** Joint limits violated, Gazebo clamps or explodes
- **Controller not running:** `startup.sh` or `gait_controller.py` not started
- **Multiple controllers:** Two scripts fighting for control (e.g., `balance_controller.py` + `gait_controller.py`)

**Standing Pose (Canonical):**
```python
HIP_STAND  = -0.09  # rad
KNEE_STAND =  0.35  # rad
ANKLE_STAND = 0.0   # rad (fixed joint, ignored)
```

**Search Pattern in Python:**
```python
topic = f"/{joint_name}/cmd"
pub = node.advertise(topic, gz.msgs.Double)
msg = gz.msgs.Double()
msg.data = angle  # Must be within joint limits
pub.publish(msg)
```

---

### 5. **Joint Limits Consistency** (`inverse_kinematics.py` vs SDF)

**Check:**
- IK solver limits match SDF limits
- Ankle compensation formula: `ankle = -(hip_pitch + knee*0.3)`
- Leg lengths: L1=L2=0.20m (thigh/shin)

**IK Solver Limits:**
```python
hip_pitch: [-1.57, 0.52] rad  (-90° to +30°)
knee:      [0.0, 2.618] rad   (0° to +150°)
ankle:     [-0.5, 0.5] rad
hip_roll:  [-0.4, 0.4] rad    (NOT IN CURRENT MODEL)
```

**Common Issues:**
- **Limit mismatch:** IK solver allows angles SDF rejects
- **Knee hyperextension:** IK solver clamped at line 17, but check commands
- **Hip roll commands:** ZMP controller sends hip_roll, but joints don't exist

---

### 6. **Gazebo Topic Verification** (`scripts/check_config.py`)

**Run:**
```bash
cd scripts
python3 check_config.py
```

**Expected Output:**
```
Checking /l_hip_pitch/cmd... ✓ (1 subscriber)
Checking /r_hip_pitch/cmd... ✓ (1 subscriber)
Checking /l_knee/cmd... ✓ (1 subscriber)
Checking /r_knee/cmd... ✓ (1 subscriber)
Checking /l_ankle/cmd... ✓ (1 subscriber)
Checking /r_ankle/cmd... ✓ (1 subscriber)
```

**Common Issues:**
- **0 subscribers:** ArduPilotPlugin not loaded, restart Gazebo
- **Script fails:** Gazebo not running or wrong version

---

### 7. **ArduPilot Parameter Check** (`mav.parm`)

**Check (if using ArduPilot servo output):**
- Servo function: `SERVON_FUNCTION` (N = channel number)
- Servo min/max: `SERVON_MIN`, `SERVON_MAX`
- Servo trim: `SERVON_TRIM=1500`

**Current Status:**
- **Python bypasses ArduPilot:** Controllers publish directly to Gazebo topics
- **ArduPilot servo output unused:** Intended architecture not implemented yet
- **Lua scripting not integrated:** No Lua scripts generating servo commands

**Note:** This check only matters for future Lua-based control.

---

## Diagnostic Workflow

### Step 1: Identify Joint Type
```bash
# Search SDF for joint definition
grep -A 20 'joint name="<joint_name>"' worlds/ardupilot_humanoid.sdf
```

**If `type="fixed"`:** Joint cannot move. Ankle joints are fixed by design.

---

### Step 2: Verify Gazebo Controller
```bash
# Search for joint controller plugin
grep -A 10 '<joint_name><joint_name></joint_name>' worlds/ardupilot_humanoid.sdf
```

**Check:**
- Plugin exists
- Topic name matches `/<joint_name>/cmd`
- PID gains reasonable (P=8, I=0.01, D=10)

---

### Step 3: Check Topic Subscribers
```bash
cd scripts
python3 check_config.py
```

**If 0 subscribers:** Restart Gazebo, plugin not loaded.

---

### Step 4: Verify Python Commands
```bash
# Search Python scripts for joint commands
grep -r "<joint_name>" scripts/*.py
```

**Check:**
- Topic name matches Gazebo controller
- Commands within joint limits
- Controller process running

---

### Step 5: Test Manual Command
```bash
# Publish test command to Gazebo topic
gz topic -t /<joint_name>/cmd -m gz.msgs.Double -p "data: 0.0"
```

**If joint moves:** Python controller issue (topic name, limits, or not running).
**If joint doesn't move:** Gazebo controller issue (plugin not loaded, wrong topic, or fixed joint).

---

### Step 6: Check ArduPilotPlugin Mapping
```bash
# Search for channel mapping
grep -A 10 '<jointName><joint_name></jointName>' worlds/ardupilot_humanoid.sdf
```

**Note:** Only matters if using ArduPilot servo output (not current architecture).

---

## Common Joint-Specific Issues

### `l_ankle` / `r_ankle`
- **Type:** `fixed` joint (cannot move)
- **Commands ignored:** Python sends commands, but Gazebo ignores them
- **IK solver:** Still computes ankle compensation, but has no effect
- **Fix:** None needed, this is by design

### `l_hip_pitch` / `r_hip_pitch`
- **Most common issue:** Initial position mismatch (world file: -0.09, some scripts: -0.05, -0.10, -0.2)
- **PWM mapping:** CH0/CH1, multiplier=1.571, offset=-0.5
- **Limits:** [-1.571, 0.523] rad (-90° to +30°)

### `l_knee` / `r_knee`
- **Most common issue:** Hyperextension (knee < 0)
- **PWM mapping:** CH2/CH3, multiplier=2.618, offset=-0.5
- **Limits:** [0.0, 2.618] rad (0° to +150°)
- **IK clamping:** Line 17 in `inverse_kinematics.py`

### `l_hip_roll` / `r_hip_roll`
- **Status:** **DOES NOT EXIST** in current model
- **ZMP controller:** Requires these joints, will fail
- **Fix required:** Add to SDF model (see AGENTS.md Next Steps #1)

---

## Quick Reference

### Joint Limits (SDF)
```
l_hip_pitch:  [-1.571, 0.523] rad  (-90° to +30°)
l_knee:       [0.0, 2.618] rad     (0° to +150°)
l_knee_shin:  [0.0, 2.618] rad     (0° to +150°)
l_ankle:      fixed (no limits)
```

### Standing Pose (Canonical)
```python
HIP_STAND  = -0.09  # rad
KNEE_STAND =  0.35  # rad
ANKLE_STAND = 0.0   # rad
```

### Gazebo Topics
```
/l_hip_pitch/cmd
/r_hip_pitch/cmd
/l_knee/cmd
/r_knee/cmd
/l_ankle/cmd  (fixed joint, ignored)
/r_ankle/cmd  (fixed joint, ignored)
```

### ArduPilot Channel Mapping
```
CH0 → l_hip_pitch
CH1 → r_hip_pitch
CH2 → l_knee
CH3 → r_knee
CH4-CH7 → NOT MAPPED
```

---

## Files to Check

1. [`worlds/ardupilot_humanoid.sdf`](worlds/ardupilot_humanoid.sdf) - Joint definitions, controllers, ArduPilotPlugin
2. [`scripts/gait_controller.py`](scripts/gait_controller.py) - Gait commands, balance PID
3. [`scripts/balance_controller.py`](scripts/balance_controller.py) - Standing balance commands
4. [`scripts/inverse_kinematics.py`](scripts/inverse_kinematics.py) - IK solver, joint limits
5. [`scripts/check_config.py`](scripts/check_config.py) - Topic subscriber verification
6. [`mav.parm`](mav.parm) - ArduPilot parameters (if using servo output)

---

**End of debug-joint command**