# lua-trace

**Purpose:** Trace the complete signal flow from an ArduPilot servo channel to its physical joint, showing every file and transformation.

**Usage:** `/lua-trace <channel_number>`

**Example:** `/lua-trace 0`

---

## What This Command Does

Given an ArduPilot servo channel number (0-7), this command traces the complete signal path from Lua script generation through ArduPilot servo output, ArduPilotPlugin PWM conversion, Gazebo joint controller, and finally to physical joint movement. Shows every file touched, every transformation applied, and every configuration point.

---

## Signal Flow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. LUA SCRIPT (Future - Not Yet Implemented)                   │
│    File: scripts/humanoid.lua (DOES NOT EXIST YET)             │
│    - Reads MAVLink commands (GUIDED mode, waypoints)            │
│    - Implements ZMP preview control + IK                         │
│    - Generates joint angles                                      │
│    - Converts angles → PWM (reverse of plugin formula)           │
│    - Outputs to SRV_Channels                                     │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ SRV_Channel API
                 │ SRV_Channels:set_output_pwm(channel, pwm)
                 │
┌────────────────▼────────────────────────────────────────────────┐
│ 2. ARDUPILOT ROVER SITL                                         │
│    File: mav.parm (ArduPilot parameters)                        │
│    - Receives servo commands from Lua                            │
│    - Applies servo parameters (min/max/trim/function)            │
│    - Outputs PWM values (1000-2000 µs)                           │
│    - Sends via JSON protocol to ArduPilotPlugin                  │
│                                                                  │
│    Key Parameters:                                               │
│    - SERVO<N>_FUNCTION: Channel assignment                       │
│    - SERVO<N>_MIN: 1000 (minimum PWM)                            │
│    - SERVO<N>_MAX: 2000 (maximum PWM)                            │
│    - SERVO<N>_TRIM: 1500 (neutral PWM)                           │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ JSON Protocol (127.0.0.1:9002)
                 │ {"servo<N>": pwm_value}
                 │
┌────────────────▼────────────────────────────────────────────────┐
│ 3. ARDUPILOT PLUGIN (Gazebo Plugin)                            │
│    File: worlds/ardupilot_humanoid.sdf                          │
│    Plugin: ArduPilotPlugin                                       │
│    - Receives PWM from ArduPilot via JSON                        │
│    - Looks up channel mapping in <control channel="N">           │
│    - Applies PWM → angle conversion formula                      │
│    - Publishes angle to Gazebo topic                             │
│                                                                  │
│    PWM → Angle Formula:                                          │
│    angle = (pwm - 1500) / 500 * multiplier + offset             │
│                                                                  │
│    Example (Channel 0 → l_hip_pitch):                            │
│    - multiplier: 1.571                                           │
│    - offset: -0.5                                                │
│    - PWM 1000 → angle = -1.571 - 0.5 = -2.071 (clamped)         │
│    - PWM 1500 → angle = 0.0 - 0.5 = -0.5                         │
│    - PWM 2000 → angle = 1.571 - 0.5 = 1.071 (clamped)           │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ Gazebo Topic (gz.transport)
                 │ Topic: /<joint_name>/cmd
                 │ Message: gz.msgs.Double (angle in radians)
                 │
┌────────────────▼────────────────────────────────────────────────┐
│ 4. GAZEBO JOINT POSITION CONTROLLER                            │
│    File: worlds/ardupilot_humanoid.sdf                          │
│    Plugin: gz-sim-joint-position-controller-system              │
│    - Subscribes to /<joint_name>/cmd topic                       │
│    - Receives target angle (radians)                             │
│    - Applies PID control (P=8, I=0.01, D=10)                     │
│    - Clamps to joint limits                                      │
│    - Sends torque command to physics engine                      │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ Physics Engine Command
                 │ Joint torque (N·m)
                 │
┌────────────────▼────────────────────────────────────────────────┐
│ 5. GAZEBO DART PHYSICS ENGINE                                  │
│    File: worlds/ardupilot_humanoid.sdf (physics settings)       │
│    - Receives torque command                                     │
│    - Simulates joint dynamics (mass, inertia, friction)          │
│    - Updates joint angle                                         │
│    - Timestep: 0.004s (250 Hz)                                   │
│    - Renders visual model                                        │
└──────────────────────────────────────────────────────────────────┘
```

---

## Channel-to-Joint Mapping (Current Configuration)

### Channel 0 → `l_hip_pitch` (Left Hip Pitch)

**Files Touched:**
1. `scripts/humanoid.lua` (FUTURE - not implemented)
2. `mav.parm` (lines with SERVO1_*)
3. `worlds/ardupilot_humanoid.sdf` (ArduPilotPlugin, line ~450)
4. `worlds/ardupilot_humanoid.sdf` (JointPositionController, line ~350)

**Transformations:**
```
Lua Script (FUTURE):
  joint_angle = -0.09 rad (standing pose)
  pwm = (angle - offset) / multiplier * 500 + 1500
  pwm = (-0.09 - (-0.5)) / 1.571 * 500 + 1500
  pwm = 0.41 / 1.571 * 500 + 1500
  pwm = 130.5 + 1500 = 1630.5 µs
  
ArduPilot:
  Applies SERVO1_MIN/MAX/TRIM (no change if within range)
  Outputs: pwm = 1630.5 µs
  
ArduPilotPlugin:
  angle = (1630.5 - 1500) / 500 * 1.571 + (-0.5)
  angle = 130.5 / 500 * 1.571 - 0.5
  angle = 0.261 * 1.571 - 0.5
  angle = 0.41 - 0.5 = -0.09 rad ✓
  
Gazebo Controller:
  Target: -0.09 rad
  PID: Generates torque to reach target
  Clamps: [-1.571, 0.523] rad
  
Physics Engine:
  Applies torque, updates joint angle
  Final: l_hip_pitch = -0.09 rad
```

**Configuration Details:**

`worlds/ardupilot_humanoid.sdf` (ArduPilotPlugin):
```xml
<control channel="0">
  <jointName>l_hip_pitch</jointName>
  <multiplier>1.571</multiplier>
  <offset>-0.5</offset>
  <servo_min>1000</servo_min>
  <servo_max>2000</servo_max>
  <type>POSITION</type>
</control>
```

`worlds/ardupilot_humanoid.sdf` (JointPositionController):
```xml
<plugin filename="gz-sim-joint-position-controller-system" 
        name="gz::sim::systems::JointPositionController">
  <joint_name>l_hip_pitch</joint_name>
  <topic>/l_hip_pitch/cmd</topic>
  <p_gain>8</p_gain>
  <i_gain>0.01</i_gain>
  <d_gain>10</d_gain>
  <initial_position>-0.09</initial_position>
</plugin>
```

`mav.parm` (ArduPilot parameters):
```
SERVO1_FUNCTION=0  (disabled, or set to specific function)
SERVO1_MIN=1000
SERVO1_MAX=2000
SERVO1_TRIM=1500
```

---

### Channel 1 → `r_hip_pitch` (Right Hip Pitch)

**Files Touched:**
1. `scripts/humanoid.lua` (FUTURE)
2. `mav.parm` (SERVO2_*)
3. `worlds/ardupilot_humanoid.sdf` (ArduPilotPlugin, line ~460)
4. `worlds/ardupilot_humanoid.sdf` (JointPositionController, line ~360)

**Configuration:**
```xml
<control channel="1">
  <jointName>r_hip_pitch</jointName>
  <multiplier>1.571</multiplier>
  <offset>-0.5</offset>
  <servo_min>1000</servo_min>
  <servo_max>2000</servo_max>
</control>
```

**Joint Limits:** [-1.571, 0.523] rad (-90° to +30°)

---

### Channel 2 → `l_knee` (Left Knee)

**Files Touched:**
1. `scripts/humanoid.lua` (FUTURE)
2. `mav.parm` (SERVO3_*)
3. `worlds/ardupilot_humanoid.sdf` (ArduPilotPlugin, line ~470)
4. `worlds/ardupilot_humanoid.sdf` (JointPositionController, line ~370)

**Configuration:**
```xml
<control channel="2">
  <jointName>l_knee</jointName>
  <multiplier>2.618</multiplier>
  <offset>-0.5</offset>
  <servo_min>1000</servo_min>
  <servo_max>2000</servo_max>
</control>
```

**Joint Limits:** [0.0, 2.618] rad (0° to +150°)

**Note:** Larger multiplier (2.618 vs 1.571) because knee has larger range of motion.

---

### Channel 3 → `r_knee` (Right Knee)

**Files Touched:**
1. `scripts/humanoid.lua` (FUTURE)
2. `mav.parm` (SERVO4_*)
3. `worlds/ardupilot_humanoid.sdf` (ArduPilotPlugin, line ~480)
4. `worlds/ardupilot_humanoid.sdf` (JointPositionController, line ~380)

**Configuration:**
```xml
<control channel="3">
  <jointName>r_knee</jointName>
  <multiplier>2.618</multiplier>
  <offset>-0.5</offset>
  <servo_min>1000</servo_min>
  <servo_max>2000</servo_max>
</control>
```

**Joint Limits:** [0.0, 2.618] rad (0° to +150°)

---

### Channels 4-7 → **NOT MAPPED**

**Status:** No joints assigned to these channels in current configuration.

**Future Use:**
- CH4 → `l_hip_roll` (requires adding joint to SDF)
- CH5 → `r_hip_roll` (requires adding joint to SDF)
- CH6 → `l_ankle` (currently fixed joint)
- CH7 → `r_ankle` (currently fixed joint)

**Files to Modify:**
1. `worlds/ardupilot_humanoid.sdf` - Add hip_roll joints
2. `worlds/ardupilot_humanoid.sdf` - Add ArduPilotPlugin channel mappings
3. `worlds/ardupilot_humanoid.sdf` - Add JointPositionController plugins
4. `scripts/inverse_kinematics.py` - Update IK solver for 3-DOF legs
5. `scripts/humanoid.lua` - Generate hip_roll commands

---

## PWM Conversion Deep Dive

### Formula Breakdown

**ArduPilotPlugin Formula:**
```
angle = (pwm - 1500) / 500 * multiplier + offset
```

**Components:**
- `pwm`: Input PWM value (1000-2000 µs)
- `1500`: Neutral PWM (center of range)
- `500`: Half of PWM range (1000-2000 has range of 1000, half is 500)
- `multiplier`: Scales PWM range to joint angle range
- `offset`: Shifts neutral point of joint

**Inverse Formula (Lua → PWM):**
```
pwm = (angle - offset) / multiplier * 500 + 1500
```

### Example: l_hip_pitch (CH0)

**Parameters:**
- multiplier: 1.571 rad (≈90°)
- offset: -0.5 rad (≈-28.6°)
- Joint limits: [-1.571, 0.523] rad (-90° to +30°)

**PWM → Angle Mapping:**
```
PWM 1000 → angle = (1000-1500)/500 * 1.571 + (-0.5) = -1.571 - 0.5 = -2.071 rad
           Clamped to: -1.571 rad (joint lower limit)
           
PWM 1250 → angle = (1250-1500)/500 * 1.571 + (-0.5) = -0.393 - 0.5 = -0.893 rad
           
PWM 1500 → angle = (1500-1500)/500 * 1.571 + (-0.5) = 0.0 - 0.5 = -0.5 rad
           (This is NOT neutral! Offset shifts it.)
           
PWM 1750 → angle = (1750-1500)/500 * 1.571 + (-0.5) = 0.393 - 0.5 = -0.107 rad
           
PWM 2000 → angle = (2000-1500)/500 * 1.571 + (-0.5) = 1.571 - 0.5 = 1.071 rad
           Clamped to: 0.523 rad (joint upper limit)
```

**Key Insight:** Offset shifts the neutral point! PWM 1500 → angle = offset, NOT 0.

### Example: l_knee (CH2)

**Parameters:**
- multiplier: 2.618 rad (≈150°)
- offset: -0.5 rad
- Joint limits: [0.0, 2.618] rad (0° to +150°)

**PWM → Angle Mapping:**
```
PWM 1000 → angle = (1000-1500)/500 * 2.618 + (-0.5) = -2.618 - 0.5 = -3.118 rad
           Clamped to: 0.0 rad (joint lower limit)
           
PWM 1500 → angle = (1500-1500)/500 * 2.618 + (-0.5) = 0.0 - 0.5 = -0.5 rad
           Clamped to: 0.0 rad (joint lower limit)
           
PWM 1595 → angle = (1595-1500)/500 * 2.618 + (-0.5) = 0.497 - 0.5 = -0.003 rad
           Clamped to: 0.0 rad (barely at limit)
           
PWM 1600 → angle = (1600-1500)/500 * 2.618 + (-0.5) = 0.524 - 0.5 = 0.024 rad
           (First PWM value that produces positive angle)
           
PWM 2000 → angle = (2000-1500)/500 * 2.618 + (-0.5) = 2.618 - 0.5 = 2.118 rad
```

**Key Insight:** Knee requires PWM > 1595 to produce positive angles due to offset.

---

## Lua Script Template (Future Implementation)

**File:** `scripts/humanoid.lua` (DOES NOT EXIST YET)

```lua
-- ArduPilot Lua script for humanoid gait control
-- This is a TEMPLATE for future implementation

-- Import required libraries
local mavlink = require("mavlink")
local socket = require("socket")

-- Robot parameters
local L1 = 0.20  -- Thigh length (m)
local L2 = 0.20  -- Shin length (m)
local COM_HEIGHT = 0.35  -- Center of mass height (m)

-- PWM conversion parameters (from ArduPilotPlugin config)
local CHANNEL_CONFIG = {
  [0] = {joint="l_hip_pitch", mult=1.571, offset=-0.5, min=1000, max=2000},
  [1] = {joint="r_hip_pitch", mult=1.571, offset=-0.5, min=1000, max=2000},
  [2] = {joint="l_knee", mult=2.618, offset=-0.5, min=1000, max=2000},
  [3] = {joint="r_knee", mult=2.618, offset=-0.5, min=1000, max=2000},
}

-- Convert joint angle to PWM
function angle_to_pwm(channel, angle)
  local cfg = CHANNEL_CONFIG[channel]
  local pwm = (angle - cfg.offset) / cfg.mult * 500 + 1500
  pwm = math.max(cfg.min, math.min(cfg.max, pwm))  -- Clamp
  return math.floor(pwm + 0.5)  -- Round to integer
end

-- Inverse kinematics (2-link planar)
function leg_ik(x, z)
  local d = math.sqrt(x*x + z*z)
  if d > L1 + L2 then
    return nil, nil  -- Unreachable
  end
  
  local cos_knee = (d*d - L1*L1 - L2*L2) / (2 * L1 * L2)
  local knee = math.acos(cos_knee)
  
  local alpha = math.atan2(z, x)
  local beta = math.acos((L1*L1 + d*d - L2*L2) / (2 * L1 * d))
  local hip_pitch = alpha - beta
  
  return hip_pitch, knee
end

-- Main control loop
function update()
  -- Read MAVLink commands (GUIDED mode, waypoints)
  -- Implement ZMP preview control
  -- Generate gait phases
  -- Compute IK for each leg
  -- Convert angles to PWM
  -- Output to SRV_Channels
  
  -- Example: Standing pose
  local hip_angle = -0.09
  local knee_angle = 0.35
  
  local pwm0 = angle_to_pwm(0, hip_angle)  -- l_hip_pitch
  local pwm1 = angle_to_pwm(1, hip_angle)  -- r_hip_pitch
  local pwm2 = angle_to_pwm(2, knee_angle) -- l_knee
  local pwm3 = angle_to_pwm(3, knee_angle) -- r_knee
  
  SRV_Channels:set_output_pwm(0, pwm0)
  SRV_Channels:set_output_pwm(1, pwm1)
  SRV_Channels:set_output_pwm(2, pwm2)
  SRV_Channels:set_output_pwm(3, pwm3)
  
  return update, 20  -- Run at 50 Hz (20ms period)
end

return update()
```

**To Enable Lua Scripting:**
1. Set `SCR_ENABLE=1` in `mav.parm`
2. Create `scripts/humanoid.lua` with gait logic
3. Restart ArduPilot SITL
4. Lua script will run automatically

---

## Current vs Intended Architecture

### Current (Python Bypass)
```
Python Controller → Gazebo Topics → Joint Controllers → Physics
```

**Files:**
- `scripts/gait_controller.py` - Generates joint angles
- `scripts/balance_controller.py` - PID balance control
- Direct publish to `/l_hip_pitch/cmd`, etc.

**Bypasses:**
- ArduPilot servo output
- ArduPilotPlugin PWM conversion
- Lua scripting

### Intended (Lua Control)
```
Lua Script → ArduPilot SRV_Channels → JSON → ArduPilotPlugin → Gazebo Topics → Joint Controllers → Physics
```

**Files:**
- `scripts/humanoid.lua` - Gait generation + IK
- `mav.parm` - Servo parameters
- `worlds/ardupilot_humanoid.sdf` - ArduPilotPlugin config

**Advantages:**
- MAVLink command interface (GUIDED mode, waypoints)
- Consistent with ArduPilot ecosystem
- Lua scripting flexibility
- Proper servo output testing

---

## Debugging Channel Mapping

### Step 1: Verify ArduPilotPlugin Configuration
```bash
grep -A 10 '<control channel="N">' worlds/ardupilot_humanoid.sdf
```

**Check:**
- Channel number matches
- Joint name correct
- Multiplier/offset reasonable
- Servo min/max = 1000/2000

### Step 2: Test PWM Conversion Manually
```python
# Python test script
channel = 0  # l_hip_pitch
pwm = 1500
multiplier = 1.571
offset = -0.5

angle = (pwm - 1500) / 500 * multiplier + offset
print(f"CH{channel} PWM {pwm} → angle {angle:.3f} rad ({angle*57.3:.1f}°)")
```

### Step 3: Verify Joint Controller Subscribes
```bash
cd scripts
python3 check_config.py
```

### Step 4: Monitor Gazebo Topics
```bash
# List all topics
gz topic -l | grep cmd

# Echo specific topic
gz topic -e -t /l_hip_pitch/cmd
```

### Step 5: Test End-to-End (Future)
```bash
# In MAVProxy (when Lua script running)
servo set 0 1500  # Set CH0 to neutral PWM
servo set 0 1750  # Set CH0 to +250 µs
```

---

## Quick Reference

### Channel Mapping
```
CH0 → l_hip_pitch (mult=1.571, offset=-0.5)
CH1 → r_hip_pitch (mult=1.571, offset=-0.5)
CH2 → l_knee      (mult=2.618, offset=-0.5)
CH3 → r_knee      (mult=2.618, offset=-0.5)
CH4-7 → NOT MAPPED
```

### PWM Ranges
```
Neutral: 1500 µs
Range:   1000-2000 µs (±500 µs from neutral)
```

### Files to Check
1. [`worlds/ardupilot_humanoid.sdf`](worlds/ardupilot_humanoid.sdf) - ArduPilotPlugin config (line ~450)
2. [`mav.parm`](mav.parm) - ArduPilot servo parameters
3. [`scripts/humanoid.lua`](scripts/humanoid.lua) - Lua script (FUTURE, does not exist)
4. [`scripts/inverse_kinematics.py`](scripts/inverse_kinematics.py) - IK solver reference

---

**End of lua-trace command**