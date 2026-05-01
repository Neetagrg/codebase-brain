# sdf-check

**Purpose:** Validate SDF joint definitions for naming consistency, friction tags, and plugin linkage.

**Usage:** `/sdf-check [--fix]`

**Options:**
- No args: Run validation checks and report issues
- `--fix`: Automatically fix common issues (duplicate friction tags, etc.)

---

## What This Command Does

Performs comprehensive validation of [`worlds/ardupilot_humanoid.sdf`](worlds/ardupilot_humanoid.sdf) to catch common configuration errors that cause joint control failures, physics instability, or plugin mismatches. Reports all issues with line numbers and suggested fixes.

---

## Validation Checks

### 1. Joint Naming Consistency

**Check:** All joint names referenced in plugins match actual joint definitions.

**Files Checked:**
- Joint definitions: `<joint name="...">`
- JointPositionController plugins: `<joint_name>...</joint_name>`
- ArduPilotPlugin mappings: `<jointName>...</jointName>`

**Common Issues:**
- Typo in plugin joint name (e.g., `l_hip_pich` vs `l_hip_pitch`)
- Plugin references non-existent joint
- Joint defined but no controller plugin

**Example Error:**
```
❌ Line 350: JointPositionController references 'l_hip_pich' but joint is named 'l_hip_pitch'
❌ Line 125: Joint 'l_knee_shin' defined but no JointPositionController plugin found
```

**Validation Logic:**
```python
# Extract all joint names
joints = re.findall(r'<joint name="([^"]+)"', sdf_content)

# Extract all JointPositionController references
controller_joints = re.findall(r'<joint_name>([^<]+)</joint_name>', sdf_content)

# Extract all ArduPilotPlugin references
plugin_joints = re.findall(r'<jointName>([^<]+)</jointName>', sdf_content)

# Check for mismatches
for cj in controller_joints:
    if cj not in joints:
        print(f"❌ JointPositionController references '{cj}' but joint not defined")

for pj in plugin_joints:
    if pj not in joints:
        print(f"❌ ArduPilotPlugin references '{pj}' but joint not defined")
```

---

### 2. Duplicate Friction Tags

**Check:** Joint dynamics should not have duplicate `<friction>` tags.

**Known Issues (AGENTS.md):**
- Lines 193, 201, 209, 220, 228, 236 have duplicate friction tags
- Gazebo uses last value, first value ignored

**Example:**
```xml
<!-- WRONG: Duplicate friction tags -->
<dynamics>
  <damping>0.1</damping>
  <friction>1.5</friction>
  <friction>0.5</friction>  <!-- This value is used, 1.5 ignored -->
</dynamics>

<!-- CORRECT: Single friction tag -->
<dynamics>
  <damping>0.1</damping>
  <friction>0.5</friction>
</dynamics>
```

**Validation Logic:**
```python
# Find all <dynamics> blocks
dynamics_blocks = re.finditer(r'<dynamics>(.*?)</dynamics>', sdf_content, re.DOTALL)

for block in dynamics_blocks:
    friction_tags = re.findall(r'<friction>([^<]+)</friction>', block.group(1))
    if len(friction_tags) > 1:
        line_num = sdf_content[:block.start()].count('\n') + 1
        print(f"❌ Line {line_num}: Duplicate friction tags: {friction_tags}")
        print(f"   Gazebo will use last value: {friction_tags[-1]}")
```

**Auto-Fix (--fix flag):**
```python
# Remove duplicate friction tags, keep last value
sdf_content = re.sub(
    r'(<friction>[^<]+</friction>)\s*<friction>([^<]+)</friction>',
    r'<friction>\2</friction>',
    sdf_content
)
```

---

### 3. Joint Limits Validation

**Check:** Joint limits are physically reasonable and match IK solver assumptions.

**Rules:**
- `<lower>` must be < `<upper>`
- Limits should match `inverse_kinematics.py` assumptions
- Fixed joints should not have limits (or limits are ignored)

**Expected Limits (from AGENTS.md):**
```
l_hip_pitch:  [-1.571, 0.523] rad  (-90° to +30°)
l_knee:       [0.0, 2.618] rad     (0° to +150°)
l_knee_shin:  [0.0, 2.618] rad     (0° to +150°)
l_ankle:      fixed (no limits)
```

**Validation Logic:**
```python
# Extract joint limits
joint_limits = {}
for match in re.finditer(r'<joint name="([^"]+)".*?<lower>([^<]+)</lower>.*?<upper>([^<]+)</upper>', 
                          sdf_content, re.DOTALL):
    name, lower, upper = match.groups()
    lower, upper = float(lower), float(upper)
    joint_limits[name] = (lower, upper)
    
    if lower >= upper:
        print(f"❌ Joint '{name}': lower ({lower}) >= upper ({upper})")

# Check against IK solver expectations
IK_LIMITS = {
    'l_hip_pitch': (-1.57, 0.52),
    'r_hip_pitch': (-1.57, 0.52),
    'l_knee': (0.0, 2.618),
    'r_knee': (0.0, 2.618),
}

for joint, (lower, upper) in joint_limits.items():
    if joint in IK_LIMITS:
        ik_lower, ik_upper = IK_LIMITS[joint]
        if abs(lower - ik_lower) > 0.01 or abs(upper - ik_upper) > 0.01:
            print(f"⚠️  Joint '{joint}': SDF limits ({lower:.3f}, {upper:.3f}) "
                  f"don't match IK solver ({ik_lower:.3f}, {ik_upper:.3f})")
```

---

### 4. ArduPilotPlugin Channel Mapping

**Check:** Channel mappings are complete and consistent.

**Rules:**
- Each channel should map to exactly one joint
- Joint names must exist in model
- Multiplier should match joint range
- Offset should be reasonable
- No duplicate channel numbers

**Expected Mapping:**
```
CH0 → l_hip_pitch (mult=1.571, offset=-0.5)
CH1 → r_hip_pitch (mult=1.571, offset=-0.5)
CH2 → l_knee      (mult=2.618, offset=-0.5)
CH3 → r_knee      (mult=2.618, offset=-0.5)
```

**Validation Logic:**
```python
# Extract channel mappings
channels = {}
for match in re.finditer(r'<control channel="(\d+)">(.*?)</control>', sdf_content, re.DOTALL):
    ch_num = int(match.group(1))
    ch_block = match.group(2)
    
    joint = re.search(r'<jointName>([^<]+)</jointName>', ch_block).group(1)
    mult = float(re.search(r'<multiplier>([^<]+)</multiplier>', ch_block).group(1))
    offset = float(re.search(r'<offset>([^<]+)</offset>', ch_block).group(1))
    
    if ch_num in channels:
        print(f"❌ Channel {ch_num} mapped to multiple joints: "
              f"{channels[ch_num]['joint']} and {joint}")
    
    channels[ch_num] = {'joint': joint, 'mult': mult, 'offset': offset}

# Check multipliers match joint ranges
for ch_num, cfg in channels.items():
    joint = cfg['joint']
    mult = cfg['mult']
    
    if joint in joint_limits:
        lower, upper = joint_limits[joint]
        expected_mult = max(abs(lower), abs(upper))
        
        if abs(mult - expected_mult) > 0.1:
            print(f"⚠️  Channel {ch_num} ({joint}): multiplier {mult:.3f} "
                  f"doesn't match joint range (expected ~{expected_mult:.3f})")
```

---

### 5. JointPositionController Configuration

**Check:** Each movable joint has a position controller with reasonable PID gains.

**Rules:**
- Every revolute joint should have a controller
- Fixed joints should not have controllers (or controller is ignored)
- Topic name should match `/<joint_name>/cmd`
- PID gains should be reasonable (P=5-10, I=0.01, D=5-15)
- Initial position should match standing pose

**Expected Configuration:**
```xml
<plugin filename="gz-sim-joint-position-controller-system">
  <joint_name>l_hip_pitch</joint_name>
  <topic>/l_hip_pitch/cmd</topic>
  <p_gain>8</p_gain>
  <i_gain>0.01</i_gain>
  <d_gain>10</d_gain>
  <initial_position>-0.09</initial_position>
</plugin>
```

**Validation Logic:**
```python
# Extract all revolute joints
revolute_joints = []
for match in re.finditer(r'<joint name="([^"]+)" type="revolute"', sdf_content):
    revolute_joints.append(match.group(1))

# Extract all JointPositionController configs
controllers = {}
for match in re.finditer(r'<plugin filename="gz-sim-joint-position-controller-system".*?>(.*?)</plugin>', 
                          sdf_content, re.DOTALL):
    block = match.group(1)
    joint = re.search(r'<joint_name>([^<]+)</joint_name>', block).group(1)
    topic = re.search(r'<topic>([^<]+)</topic>', block).group(1)
    p_gain = float(re.search(r'<p_gain>([^<]+)</p_gain>', block).group(1))
    i_gain = float(re.search(r'<i_gain>([^<]+)</i_gain>', block).group(1))
    d_gain = float(re.search(r'<d_gain>([^<]+)</d_gain>', block).group(1))
    
    controllers[joint] = {'topic': topic, 'p': p_gain, 'i': i_gain, 'd': d_gain}
    
    # Check topic name
    expected_topic = f"/{joint}/cmd"
    if topic != expected_topic:
        print(f"❌ Joint '{joint}': topic '{topic}' should be '{expected_topic}'")
    
    # Check PID gains
    if p_gain < 1 or p_gain > 20:
        print(f"⚠️  Joint '{joint}': P gain {p_gain} outside typical range (5-10)")
    if d_gain < 1 or d_gain > 20:
        print(f"⚠️  Joint '{joint}': D gain {d_gain} outside typical range (5-15)")

# Check all revolute joints have controllers
for joint in revolute_joints:
    if joint not in controllers:
        print(f"❌ Revolute joint '{joint}' has no JointPositionController")
```

---

### 6. Initial Pose Consistency

**Check:** Initial joint positions in SDF match canonical standing pose.

**Canonical Standing Pose (from AGENTS.md):**
```python
HIP_STAND  = -0.09  # rad
KNEE_STAND =  0.35  # rad
ANKLE_STAND = 0.0   # rad (fixed joint)
```

**Validation Logic:**
```python
STANDING_POSE = {
    'l_hip_pitch': -0.09,
    'r_hip_pitch': -0.09,
    'l_knee': 0.35,
    'r_knee': 0.35,
    'l_ankle': 0.0,
    'r_ankle': 0.0,
}

# Check initial_position in JointPositionController
for match in re.finditer(r'<plugin filename="gz-sim-joint-position-controller-system".*?>(.*?)</plugin>', 
                          sdf_content, re.DOTALL):
    block = match.group(1)
    joint = re.search(r'<joint_name>([^<]+)</joint_name>', block).group(1)
    
    init_pos_match = re.search(r'<initial_position>([^<]+)</initial_position>', block)
    if init_pos_match:
        init_pos = float(init_pos_match.group(1))
        
        if joint in STANDING_POSE:
            expected = STANDING_POSE[joint]
            if abs(init_pos - expected) > 0.01:
                print(f"⚠️  Joint '{joint}': initial_position {init_pos:.3f} "
                      f"doesn't match standing pose {expected:.3f}")

# Check initial_position in joint definition
for match in re.finditer(r'<joint name="([^"]+)".*?<initial_position>([^<]+)</initial_position>', 
                          sdf_content, re.DOTALL):
    joint, init_pos = match.groups()
    init_pos = float(init_pos)
    
    if joint in STANDING_POSE:
        expected = STANDING_POSE[joint]
        if abs(init_pos - expected) > 0.01:
            print(f"⚠️  Joint '{joint}': joint initial_position {init_pos:.3f} "
                  f"doesn't match standing pose {expected:.3f}")
```

---

### 7. Physics Configuration

**Check:** Physics settings are stable and reasonable.

**Rules:**
- `max_step_size` ≤ 0.004s (CRITICAL - larger causes explosions)
- `real_time_factor` = 1.0 (real-time simulation)
- Physics engine = DART (required for humanoid stability)

**Expected Configuration:**
```xml
<physics name="1ms" type="dart">
  <max_step_size>0.004</max_step_size>
  <real_time_factor>1</real_time_factor>
</physics>
```

**Validation Logic:**
```python
# Extract physics settings
physics_match = re.search(r'<physics name="[^"]*" type="([^"]+)">(.*?)</physics>', 
                          sdf_content, re.DOTALL)
if physics_match:
    engine = physics_match.group(1)
    block = physics_match.group(2)
    
    if engine != "dart":
        print(f"❌ Physics engine '{engine}' should be 'dart' for humanoid stability")
    
    step_size = float(re.search(r'<max_step_size>([^<]+)</max_step_size>', block).group(1))
    if step_size > 0.004:
        print(f"❌ CRITICAL: max_step_size {step_size}s > 0.004s (robot will explode!)")
    
    rtf = float(re.search(r'<real_time_factor>([^<]+)</real_time_factor>', block).group(1))
    if rtf != 1.0:
        print(f"⚠️  real_time_factor {rtf} != 1.0 (simulation not real-time)")
```

---

### 8. Model Pose and Initial Pitch

**Check:** Robot spawn pose has correct initial pitch lean.

**Expected Pose (from AGENTS.md):**
```xml
<pose>0 0 0.57 0.12 0 0</pose>
<!-- x y z roll pitch yaw -->
<!-- 0.12 rad = 6.9° forward pitch -->
```

**Purpose:** Compensates for CoM position, prevents backward fall on spawn.

**Validation Logic:**
```python
# Extract model pose
pose_match = re.search(r'<model name="ArduBiped_Proto">.*?<pose>([^<]+)</pose>', 
                       sdf_content, re.DOTALL)
if pose_match:
    pose = [float(x) for x in pose_match.group(1).split()]
    x, y, z, roll, pitch, yaw = pose
    
    if abs(z - 0.57) > 0.05:
        print(f"⚠️  Model z-position {z:.3f} != 0.57 (may affect standing height)")
    
    if abs(pitch - 0.12) > 0.02:
        print(f"⚠️  Model pitch {pitch:.3f} != 0.12 rad (may cause fall on spawn)")
        print(f"   Expected: 0.12 rad (6.9°) forward lean to compensate for CoM")
```

---

### 9. Foot Collision Configuration

**Check:** Foot collision geometry and friction are adequate for stability.

**Expected Configuration:**
```xml
<collision name="l_foot_collision">
  <geometry>
    <box>
      <size>0.18 0.10 0.02</size>  <!-- 18cm x 10cm foot -->
    </box>
  </geometry>
  <surface>
    <friction>
      <ode>
        <mu>1.0</mu>  <!-- Friction coefficient -->
        <mu2>1.0</mu2>
      </ode>
    </friction>
  </surface>
</collision>
```

**Validation Logic:**
```python
# Extract foot collision configs
for foot in ['l_foot', 'r_foot']:
    collision_match = re.search(
        rf'<collision name="{foot}_collision">(.*?)</collision>', 
        sdf_content, re.DOTALL
    )
    if collision_match:
        block = collision_match.group(1)
        
        # Check friction
        mu_match = re.search(r'<mu>([^<]+)</mu>', block)
        if mu_match:
            mu = float(mu_match.group(1))
            if mu < 0.8:
                print(f"⚠️  {foot}: friction mu={mu} < 0.8 (may cause slipping)")
        else:
            print(f"❌ {foot}: no friction coefficient defined")
        
        # Check size
        size_match = re.search(r'<size>([^<]+)</size>', block)
        if size_match:
            size = [float(x) for x in size_match.group(1).split()]
            if size[0] < 0.15 or size[1] < 0.08:
                print(f"⚠️  {foot}: collision size {size} may be too small for stability")
```

---

### 10. Coordinate Frame Transforms

**Check:** ArduPilotPlugin coordinate transforms are correct.

**Expected Configuration:**
```xml
<modelXYZToAirplaneXForwardZDown>0 0 0 180 0 0</modelXYZToAirplaneXForwardZDown>
<gazeboXYZToNED>0 0 0 180 0 90</gazeboXYZToNED>
```

**Purpose:** Convert between Gazebo (X-forward, Z-up) and ArduPilot (X-forward, Z-down, NED frame).

**Validation Logic:**
```python
# Extract coordinate transforms
plugin_match = re.search(r'<plugin filename="ArduPilotPlugin".*?>(.*?)</plugin>', 
                         sdf_content, re.DOTALL)
if plugin_match:
    block = plugin_match.group(1)
    
    model_xyz = re.search(r'<modelXYZToAirplaneXForwardZDown>([^<]+)</modelXYZToAirplaneXForwardZDown>', block)
    gazebo_xyz = re.search(r'<gazeboXYZToNED>([^<]+)</gazeboXYZToNED>', block)
    
    if model_xyz:
        transform = model_xyz.group(1).strip()
        if transform != "0 0 0 180 0 0":
            print(f"⚠️  modelXYZToAirplaneXForwardZDown '{transform}' != '0 0 0 180 0 0'")
            print(f"   Changing this will break IMU data!")
    
    if gazebo_xyz:
        transform = gazebo_xyz.group(1).strip()
        if transform != "0 0 0 180 0 90":
            print(f"⚠️  gazeboXYZToNED '{transform}' != '0 0 0 180 0 90'")
            print(f"   Changing this will break IMU data!")
```

---

## Validation Report Format

### Summary
```
SDF Validation Report for worlds/ardupilot_humanoid.sdf
Generated: 2026-05-01 17:00:00

✅ Passed: 8 checks
⚠️  Warnings: 3 issues
❌ Errors: 2 critical issues

Total Issues: 5
```

### Detailed Results
```
1. Joint Naming Consistency ✅
   - All 8 joints defined
   - All controller references valid
   - All plugin references valid

2. Duplicate Friction Tags ❌
   - Line 193: l_hip_pitch has duplicate friction (1.5, 0.5)
   - Line 201: r_hip_pitch has duplicate friction (1.5, 0.5)
   - Line 209: l_knee has duplicate friction (1.5, 0.5)
   - Line 220: r_knee has duplicate friction (1.5, 0.5)
   - Line 228: l_ankle has duplicate friction (1.5, 0.5)
   - Line 236: r_ankle has duplicate friction (1.5, 0.5)
   Fix: Run with --fix flag to remove duplicates

3. Joint Limits Validation ✅
   - All limits physically reasonable
   - All limits match IK solver

4. ArduPilotPlugin Channel Mapping ⚠️
   - CH0-3 mapped correctly
   - CH4-7 not mapped (hip_roll joints don't exist yet)

5. JointPositionController Configuration ✅
   - All 6 revolute joints have controllers
   - All topics named correctly
   - PID gains reasonable

6. Initial Pose Consistency ⚠️
   - l_hip_pitch: -0.09 ✅
   - r_hip_pitch: -0.09 ✅
   - l_knee: 0.35 ✅
   - r_knee: 0.35 ✅

7. Physics Configuration ✅
   - Engine: dart ✅
   - max_step_size: 0.004s ✅
   - real_time_factor: 1.0 ✅

8. Model Pose and Initial Pitch ✅
   - Position: (0, 0, 0.57) ✅
   - Pitch: 0.12 rad (6.9°) ✅

9. Foot Collision Configuration ⚠️
   - l_foot friction: 1.0 ✅
   - r_foot friction: 1.0 ✅
   - Foot size: 0.18 x 0.10 m ✅

10. Coordinate Frame Transforms ✅
    - modelXYZToAirplaneXForwardZDown: 0 0 0 180 0 0 ✅
    - gazeboXYZToNED: 0 0 0 180 0 90 ✅
```

---

## Auto-Fix Capabilities (--fix flag)

### 1. Remove Duplicate Friction Tags
```python
# Keep last friction value, remove duplicates
sdf_content = re.sub(
    r'(<friction>[^<]+</friction>)\s*<friction>([^<]+)</friction>',
    r'<friction>\2</friction>',
    sdf_content
)
```

### 2. Normalize Topic Names
```python
# Ensure topic names match /<joint_name>/cmd pattern
for match in re.finditer(r'<joint_name>([^<]+)</joint_name>\s*<topic>([^<]+)</topic>', sdf_content):
    joint = match.group(1)
    topic = match.group(2)
    expected_topic = f"/{joint}/cmd"
    
    if topic != expected_topic:
        sdf_content = sdf_content.replace(
            f"<topic>{topic}</topic>",
            f"<topic>{expected_topic}</topic>"
        )
```

### 3. Align Initial Positions
```python
# Update initial positions to match standing pose
STANDING_POSE = {
    'l_hip_pitch': -0.09,
    'r_hip_pitch': -0.09,
    'l_knee': 0.35,
    'r_knee': 0.35,
}

for joint, target_pos in STANDING_POSE.items():
    # Update in JointPositionController
    sdf_content = re.sub(
        rf'(<joint_name>{joint}</joint_name>.*?<initial_position>)[^<]+(</initial_position>)',
        rf'\g<1>{target_pos}\g<2>',
        sdf_content,
        flags=re.DOTALL
    )
```

---

## Quick Reference

### Critical Checks (Must Pass)
1. ❌ Physics timestep ≤ 0.004s (robot explodes if larger)
2. ❌ Joint limits: lower < upper
3. ❌ All revolute joints have controllers
4. ❌ Coordinate transforms correct (IMU breaks if wrong)

### Warning Checks (Should Fix)
1. ⚠️  Duplicate friction tags (Gazebo ignores first value)
2. ⚠️  Initial pose matches standing pose
3. ⚠️  PID gains reasonable (P=5-10, D=5-15)
4. ⚠️  Foot friction ≥ 0.8 (prevents slipping)

### Info Checks (Nice to Have)
1. ℹ️  Channel mapping complete (CH4-7 not mapped yet)
2. ℹ️  Joint limits match IK solver
3. ℹ️  Model pitch = 0.12 rad (CoM compensation)

---

## Files Validated

1. [`worlds/ardupilot_humanoid.sdf`](worlds/ardupilot_humanoid.sdf) - Primary world file
2. Cross-referenced with:
   - [`scripts/inverse_kinematics.py`](scripts/inverse_kinematics.py) - Joint limits
   - [`scripts/gait_controller.py`](scripts/gait_controller.py) - Standing pose
   - [`AGENTS.md`](AGENTS.md) - System documentation

---

**End of sdf-check command**