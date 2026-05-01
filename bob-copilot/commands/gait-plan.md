# gait-plan

**Purpose:** Generate a step-by-step implementation plan for a named gait phase using ZMP constraints.

**Usage:** `/gait-plan <phase_name>`

**Examples:**
- `/gait-plan STAND` - Standing balance phase
- `/gait-plan SHIFT_R` - Weight shift to right leg
- `/gait-plan STEP_L` - Left leg swing phase
- `/gait-plan WALK` - Complete walking cycle

---

## What This Command Does

Given a gait phase name, this command generates a detailed implementation plan including:
1. ZMP stability constraints
2. Required joint trajectories
3. IK solver requirements
4. Balance controller tuning
5. Phase timing and transitions
6. Implementation steps with file modifications

---

## Gait Phase Library

### STAND - Standing Balance

**Description:** Maintain upright standing pose with active balance control.

**Duration:** Continuous (until transition)

**ZMP Constraints:**
- ZMP must stay within support polygon (both feet on ground)
- Support polygon: Rectangle defined by foot positions
- Foot separation: 0.16m (hip width)
- Foot size: 0.18m x 0.10m
- ZMP safety margin: 0.02m from edges

**Joint Targets:**
```python
HIP_STAND  = -0.09  # rad (-5.2°)
KNEE_STAND =  0.35  # rad (20.0°)
ANKLE_STAND = 0.0   # rad (fixed joint)
```

**Balance Control:**
- PID on pitch: Kp=2.0, Ki=0.01, Kd=0.5 (balance_controller.py)
- PID on pitch: Kp=0.08, Ki=0.001, Kd=0.01 (gait_controller.py)
- Primary actuator: Hip pitch
- Secondary actuator: Ankle pitch (0.5x, but fixed joint)

**CoM Position:**
- Height: 0.38m above ground
- X: 0.0m (centered between feet)
- Y: 0.0m (centered laterally)

**Implementation Steps:**

1. **Define Standing Pose** (`scripts/gait_controller.py`)
   ```python
   HIP_STAND = -0.09
   KNEE_STAND = 0.35
   ANKLE_STAND = 0.0
   ```

2. **Implement Balance PID** (`scripts/balance_controller.py`)
   ```python
   def balance_control(pitch, pitch_rate, dt):
       error = pitch - target_pitch
       integral += error * dt
       derivative = (error - prev_error) / dt
       
       hip_correction = Kp * error + Ki * integral + Kd * derivative
       return hip_correction
   ```

3. **Apply Joint Commands** (`scripts/gait_controller.py`)
   ```python
   l_hip_cmd = HIP_STAND + balance_correction
   r_hip_cmd = HIP_STAND + balance_correction
   l_knee_cmd = KNEE_STAND
   r_knee_cmd = KNEE_STAND
   ```

4. **Verify ZMP Stability**
   ```python
   # ZMP should be at (0, 0) for symmetric standing
   zmp_x = 0.0
   zmp_y = 0.0
   
   # Check within support polygon
   assert -0.08 < zmp_x < 0.08  # Within foot length
   assert -0.08 < zmp_y < 0.08  # Within foot width
   ```

**Files to Modify:**
- [`scripts/balance_controller.py`](scripts/balance_controller.py) - Balance PID implementation
- [`scripts/gait_controller.py`](scripts/gait_controller.py) - Standing pose constants
- [`worlds/ardupilot_humanoid.sdf`](worlds/ardupilot_humanoid.sdf) - Initial pose (already correct)

**Success Criteria:**
- Robot stands upright for >10 seconds
- Pitch oscillation < 0.05 rad (2.9°)
- No drift in position

---

### SHIFT_R - Weight Shift to Right Leg

**Description:** Shift CoM laterally to right leg to prepare for left leg swing.

**Duration:** 3.0s (current), target 0.3-0.5s

**ZMP Constraints:**
- ZMP must move from center to right foot
- ZMP trajectory: Linear from (0, 0) to (0, -0.08)
- ZMP must stay within right foot support polygon
- Right foot: Center at (0, -0.08), size 0.18m x 0.10m

**Joint Trajectories:**
```python
# Hip roll (REQUIRES NEW JOINTS - not in current model)
l_hip_roll: 0.0 → +0.15 rad (lean right)
r_hip_roll: 0.0 → -0.15 rad (lean right)

# Hip pitch (maintain standing)
l_hip_pitch: -0.09 → -0.09 rad
r_hip_pitch: -0.09 → -0.09 rad

# Knee (maintain standing)
l_knee: 0.35 → 0.35 rad
r_knee: 0.35 → 0.35 rad
```

**CoM Trajectory:**
- Start: (0.0, 0.0, 0.38) - centered
- End: (0.0, -0.08, 0.38) - over right foot
- Velocity: 0.08m / 0.5s = 0.16 m/s lateral

**ZMP Trajectory:**
```python
def zmp_shift_right(t, duration=0.5):
    """Linear ZMP shift from center to right foot"""
    phase = min(t / duration, 1.0)
    zmp_x = 0.0  # No forward/back shift
    zmp_y = -0.08 * phase  # Lateral shift to right
    return zmp_x, zmp_y
```

**Implementation Steps:**

1. **Add Hip Roll Joints** (`worlds/ardupilot_humanoid.sdf`)
   ```xml
   <joint name="l_hip_roll" type="revolute">
     <parent>torso</parent>
     <child>l_thigh</child>
     <axis>
       <xyz>1 0 0</xyz>  <!-- Roll axis -->
       <limit>
         <lower>-0.4</lower>
         <upper>0.4</upper>
       </limit>
     </axis>
   </joint>
   ```

2. **Update IK Solver** (`scripts/inverse_kinematics.py`)
   ```python
   def leg_ik_3dof(x, y, z):
       """3-DOF leg IK: hip_pitch, hip_roll, knee"""
       # Compute hip_roll from lateral displacement
       hip_roll = math.atan2(y, z)
       
       # Project to sagittal plane for 2D IK
       z_proj = z / math.cos(hip_roll)
       hip_pitch, knee = leg_ik_2dof(x, z_proj)
       
       return hip_pitch, hip_roll, knee
   ```

3. **Implement ZMP Controller** (`scripts/zmp_gait_controller.py`)
   ```python
   def shift_weight_right(t, duration=0.5):
       """Generate joint commands for right weight shift"""
       phase = min(t / duration, 1.0)
       
       # Compute target CoM position
       com_y = -0.08 * phase  # Move to right foot
       
       # Compute required hip roll
       hip_roll = math.atan2(com_y, COM_HEIGHT)
       
       # Apply to both legs (opposite directions)
       l_hip_roll = +hip_roll
       r_hip_roll = -hip_roll
       
       return l_hip_roll, r_hip_roll
   ```

4. **Add Balance Feedback** (`scripts/zmp_gait_controller.py`)
   ```python
   # Measure actual roll from IMU
   actual_roll = attitude.roll
   
   # PID correction
   roll_error = target_roll - actual_roll
   roll_correction = Kp_roll * roll_error
   
   # Apply correction
   l_hip_roll += roll_correction
   r_hip_roll -= roll_correction
   ```

**Files to Modify:**
- [`worlds/ardupilot_humanoid.sdf`](worlds/ardupilot_humanoid.sdf) - Add hip_roll joints
- [`scripts/inverse_kinematics.py`](scripts/inverse_kinematics.py) - 3-DOF IK solver
- [`scripts/zmp_gait_controller.py`](scripts/zmp_gait_controller.py) - Weight shift logic
- [`scripts/preview_control.py`](scripts/preview_control.py) - ZMP preview for lateral motion

**Success Criteria:**
- ZMP reaches right foot center within duration
- No loss of balance (pitch/roll < 0.1 rad)
- Smooth trajectory (no jerks)

---

### STEP_L - Left Leg Swing Phase

**Description:** Swing left leg forward while maintaining balance on right leg.

**Duration:** 0.6s (target), 3.0s (current)

**ZMP Constraints:**
- ZMP must stay within right foot support polygon
- Right foot: Center at (0, -0.08), size 0.18m x 0.10m
- ZMP safety margin: 0.02m from edges
- ZMP bounds: x ∈ [-0.07, 0.07], y ∈ [-0.13, -0.03]

**Joint Trajectories:**

**Support Leg (Right):**
```python
# Maintain standing pose with balance corrections
r_hip_pitch: -0.09 + balance_correction
r_hip_roll: -0.15 (maintain weight shift)
r_knee: 0.35
```

**Swing Leg (Left):**
```python
# Lift and swing forward
t ∈ [0, 0.6]  # Swing duration

# Hip pitch: Swing forward
l_hip_pitch(t) = -0.09 + 0.05 * sin(π * t / 0.6)
# Range: -0.09 → -0.04 → -0.09 rad

# Knee: Lift foot
l_knee(t) = 0.35 + 0.20 * sin(π * t / 0.6)
# Range: 0.35 → 0.55 → 0.35 rad
# Foot clearance: ~0.04m

# Hip roll: Maintain lateral position
l_hip_roll: +0.15 (constant)
```

**Foot Trajectory:**
```python
def swing_foot_trajectory(t, duration=0.6, step_length=0.12):
    """Generate swing foot trajectory"""
    phase = t / duration
    
    # Forward motion (linear)
    x = step_length * phase
    
    # Vertical motion (sinusoidal)
    z = 0.04 * math.sin(math.pi * phase)  # 4cm clearance
    
    # Lateral (constant)
    y = 0.08  # Left foot offset
    
    return x, y, z
```

**CoM Trajectory:**
```python
# CoM stays over right foot (support leg)
com_x = 0.0  # No forward shift yet
com_y = -0.08  # Over right foot
com_z = 0.38  # Constant height
```

**ZMP Stability Check:**
```python
def check_zmp_stability(com_pos, com_vel, com_accel):
    """Verify ZMP stays within support polygon"""
    g = 9.81  # Gravity
    
    # ZMP position (simplified LIPM)
    zmp_x = com_pos[0] - (com_pos[2] / g) * com_accel[0]
    zmp_y = com_pos[1] - (com_pos[2] / g) * com_accel[1]
    
    # Right foot support polygon
    x_min, x_max = -0.07, 0.07
    y_min, y_max = -0.13, -0.03
    
    # Check bounds with safety margin
    margin = 0.02
    assert x_min + margin < zmp_x < x_max - margin
    assert y_min + margin < zmp_y < y_max - margin
    
    return zmp_x, zmp_y
```

**Implementation Steps:**

1. **Implement Swing Trajectory** (`scripts/foot.py`)
   ```python
   class SwingFootTrajectory:
       def __init__(self, duration=0.6, step_length=0.12, max_height=0.04):
           self.duration = duration
           self.step_length = step_length
           self.max_height = max_height
       
       def get_position(self, t):
           phase = min(t / self.duration, 1.0)
           
           x = self.step_length * phase
           y = 0.08  # Left foot lateral offset
           z = self.max_height * math.sin(math.pi * phase)
           
           return x, y, z
   ```

2. **Compute IK for Swing Leg** (`scripts/inverse_kinematics.py`)
   ```python
   # Get foot position from trajectory
   foot_x, foot_y, foot_z = swing_trajectory.get_position(t)
   
   # Compute joint angles
   l_hip_pitch, l_hip_roll, l_knee = leg_ik_3dof(foot_x, foot_y, foot_z)
   ```

3. **Implement Balance Control** (`scripts/zmp_gait_controller.py`)
   ```python
   # Measure pitch from IMU
   pitch_error = attitude.pitch - target_pitch
   
   # PID correction on support leg
   r_hip_pitch += Kp * pitch_error + Kd * pitch_rate
   
   # Clamp to joint limits
   r_hip_pitch = np.clip(r_hip_pitch, -1.571, 0.523)
   ```

4. **Verify ZMP Stability** (`scripts/zmp_gait_controller.py`)
   ```python
   # Compute ZMP from CoM state
   zmp_x, zmp_y = compute_zmp(com_pos, com_vel, com_accel)
   
   # Check within support polygon
   if not is_zmp_stable(zmp_x, zmp_y, support_foot='right'):
       # Abort swing, return to double support
       abort_swing()
   ```

**Files to Modify:**
- [`scripts/foot.py`](scripts/foot.py) - Swing trajectory (already exists)
- [`scripts/inverse_kinematics.py`](scripts/inverse_kinematics.py) - 3-DOF IK
- [`scripts/zmp_gait_controller.py`](scripts/zmp_gait_controller.py) - Swing phase logic
- [`scripts/gait_controller.py`](scripts/gait_controller.py) - Phase timing

**Success Criteria:**
- Foot clears ground by ≥0.03m
- ZMP stays within support polygon
- No loss of balance (pitch/roll < 0.15 rad)
- Smooth landing (impact force < 2x body weight)

---

### WALK - Complete Walking Cycle

**Description:** Full walking gait with continuous forward motion.

**Phases:**
1. STAND (0.5s) - Initial standing
2. SHIFT_R (0.5s) - Weight shift to right
3. STEP_L (0.6s) - Left leg swing
4. SHIFT_L (0.5s) - Weight shift to left
5. STEP_R (0.6s) - Right leg swing
6. Repeat from phase 4

**Total Cycle Time:** 2.7s (target), 18.0s (current)

**Step Parameters:**
```python
STEP_LENGTH = 0.12  # m (12cm forward)
STEP_WIDTH = 0.16   # m (hip separation)
STEP_HEIGHT = 0.04  # m (foot clearance)
STEP_DURATION = 0.6 # s (swing time)
SHIFT_DURATION = 0.5 # s (weight shift time)
DOUBLE_SUPPORT = 0.1 # s (both feet on ground)
```

**ZMP Trajectory:**
```python
def zmp_walking_trajectory(t, cycle_time=2.7):
    """ZMP trajectory for walking cycle"""
    phase = (t % cycle_time) / cycle_time
    
    if phase < 0.185:  # STAND (0.5s)
        zmp_x, zmp_y = 0.0, 0.0
    
    elif phase < 0.370:  # SHIFT_R (0.5s)
        shift_phase = (phase - 0.185) / 0.185
        zmp_x = 0.0
        zmp_y = -0.08 * shift_phase
    
    elif phase < 0.593:  # STEP_L (0.6s)
        zmp_x = 0.0
        zmp_y = -0.08  # Over right foot
    
    elif phase < 0.778:  # SHIFT_L (0.5s)
        shift_phase = (phase - 0.593) / 0.185
        zmp_x = 0.0
        zmp_y = -0.08 + 0.16 * shift_phase
    
    else:  # STEP_R (0.6s)
        zmp_x = 0.0
        zmp_y = 0.08  # Over left foot
    
    return zmp_x, zmp_y
```

**CoM Trajectory (LIPM):**
```python
def com_trajectory_lipm(zmp_ref, com_height=0.38):
    """Compute CoM trajectory from ZMP reference using LIPM"""
    g = 9.81
    omega = math.sqrt(g / com_height)  # Natural frequency
    
    # Solve LIPM differential equation
    # com_ddot = omega^2 * (com - zmp)
    
    # Use preview control to track ZMP reference
    com_pos, com_vel = preview_controller.update(zmp_ref)
    
    return com_pos, com_vel
```

**Implementation Steps:**

1. **Implement Preview Controller** (`scripts/preview_control.py`)
   ```python
   class LIPMPreviewController:
       def __init__(self, dt=0.02, com_height=0.35, preview_horizon=20):
           self.dt = dt
           self.com_height = com_height
           self.preview_horizon = preview_horizon
           
           # Compute preview gains
           self.compute_gains()
       
       def compute_gains(self):
           """Solve discrete-time LQR with preview"""
           # State: [com_pos, com_vel, zmp_error_integral]
           # Control: com_accel
           
           # Discrete-time LIPM dynamics
           A, B, C = self.get_lipm_matrices()
           
           # Solve DARE for optimal gains
           P = solve_discrete_are(A, B, Q, R)
           K = np.linalg.inv(R + B.T @ P @ B) @ B.T @ P @ A
           
           # Compute preview gains
           self.K_x = K  # State feedback
           self.K_p = self.compute_preview_gains(P)  # Preview gains
       
       def update(self, zmp_ref_future):
           """Update controller with future ZMP reference"""
           # State feedback
           u = -self.K_x @ self.state
           
           # Preview feedforward
           for i, zmp_ref in enumerate(zmp_ref_future):
               u += self.K_p[i] * zmp_ref
           
           # Integrate to get CoM position
           self.state = self.A @ self.state + self.B @ u
           
           return self.state[0], self.state[1]  # com_pos, com_vel
   ```

2. **Implement Walking State Machine** (`scripts/zmp_gait_controller.py`)
   ```python
   class WalkingGait:
       def __init__(self):
           self.phase = 'STAND'
           self.phase_time = 0.0
           self.cycle_count = 0
       
       def update(self, dt):
           self.phase_time += dt
           
           if self.phase == 'STAND':
               if self.phase_time > 0.5:
                   self.transition_to('SHIFT_R')
           
           elif self.phase == 'SHIFT_R':
               if self.phase_time > 0.5:
                   self.transition_to('STEP_L')
           
           elif self.phase == 'STEP_L':
               if self.phase_time > 0.6:
                   self.transition_to('SHIFT_L')
           
           elif self.phase == 'SHIFT_L':
               if self.phase_time > 0.5:
                   self.transition_to('STEP_R')
           
           elif self.phase == 'STEP_R':
               if self.phase_time > 0.6:
                   self.transition_to('SHIFT_L')
                   self.cycle_count += 1
       
       def transition_to(self, new_phase):
           self.phase = new_phase
           self.phase_time = 0.0
   ```

3. **Generate Joint Commands** (`scripts/zmp_gait_controller.py`)
   ```python
   def generate_joint_commands(phase, phase_time):
       """Generate joint commands for current phase"""
       
       if phase == 'STAND':
           return stand_pose()
       
       elif phase == 'SHIFT_R':
           return shift_right(phase_time)
       
       elif phase == 'STEP_L':
           return step_left(phase_time)
       
       elif phase == 'SHIFT_L':
           return shift_left(phase_time)
       
       elif phase == 'STEP_R':
           return step_right(phase_time)
   ```

4. **Integrate with MAVLink** (`scripts/humanoid.lua` - FUTURE)
   ```lua
   -- Read velocity command from MAVLink
   local vx = vehicle:get_velocity_NED().x
   local vy = vehicle:get_velocity_NED().y
   
   -- Convert to step parameters
   local step_length = vx * STEP_DURATION
   local step_width = STEP_WIDTH + vy * STEP_DURATION
   
   -- Generate gait with modified parameters
   local joints = walking_gait:update(step_length, step_width)
   
   -- Output to servos
   for ch, angle in pairs(joints) do
       local pwm = angle_to_pwm(ch, angle)
       SRV_Channels:set_output_pwm(ch, pwm)
   end
   ```

**Files to Modify:**
- [`scripts/preview_control.py`](scripts/preview_control.py) - LIPM preview controller (exists)
- [`scripts/zmp_gait_controller.py`](scripts/zmp_gait_controller.py) - Walking state machine (incomplete)
- [`scripts/foot.py`](scripts/foot.py) - Swing trajectories (exists)
- [`scripts/inverse_kinematics.py`](scripts/inverse_kinematics.py) - 3-DOF IK (needs hip_roll)
- [`worlds/ardupilot_humanoid.sdf`](worlds/ardupilot_humanoid.sdf) - Add hip_roll joints
- [`scripts/humanoid.lua`](scripts/humanoid.lua) - MAVLink integration (FUTURE)

**Success Criteria:**
- Continuous walking for >10 steps
- Forward velocity: 0.12m / 2.7s = 0.044 m/s (4.4 cm/s)
- No falls (pitch/roll < 0.2 rad)
- ZMP stays within support polygon 95% of time
- Smooth gait (no jerks or stumbles)

---

## ZMP Stability Theory

### Linear Inverted Pendulum Model (LIPM)

**Assumptions:**
1. CoM moves in horizontal plane at constant height
2. All mass concentrated at CoM
3. Legs are massless
4. No angular momentum about CoM

**Dynamics:**
```
com_ddot = (g / h) * (com - zmp)

where:
  com = Center of Mass position (x, y)
  zmp = Zero Moment Point position (x, y)
  g = 9.81 m/s² (gravity)
  h = 0.38 m (CoM height)
  omega = sqrt(g/h) = 5.07 rad/s (natural frequency)
```

**ZMP Equation:**
```
zmp = com - (h / g) * com_ddot

For stable walking:
  zmp must stay within support polygon
```

**Support Polygon:**
- Single support: Foot contact area
- Double support: Convex hull of both feet
- Safety margin: 0.02m from edges

### Preview Control

**Concept:** Use future ZMP reference to compute optimal CoM trajectory.

**Preview Horizon:** N = 20 steps (0.4s at 50 Hz)

**Cost Function:**
```
J = Σ (Qe * e_k² + R * u_k²)

where:
  e_k = zmp_ref[k] - zmp[k]  (tracking error)
  u_k = com_accel[k]          (control input)
  Qe = 1.0                    (tracking weight)
  R = 1e-6                    (control weight)
```

**Optimal Control:**
```
u = -K_x * state + Σ K_p[i] * zmp_ref[k+i]

where:
  K_x = state feedback gains
  K_p = preview gains (computed from DARE solution)
```

---

## Implementation Checklist

### Phase 1: Add Hip Roll Joints (CRITICAL)
- [ ] Modify `worlds/ardupilot_humanoid.sdf` to add l_hip_roll, r_hip_roll
- [ ] Add JointPositionController plugins for hip_roll
- [ ] Add ArduPilotPlugin channel mappings (CH4, CH5)
- [ ] Update `inverse_kinematics.py` for 3-DOF IK
- [ ] Test hip_roll range of motion

### Phase 2: Implement Weight Shift
- [ ] Implement `shift_weight_right()` in `zmp_gait_controller.py`
- [ ] Implement `shift_weight_left()` in `zmp_gait_controller.py`
- [ ] Add roll balance PID controller
- [ ] Test weight shift without swing (verify ZMP)

### Phase 3: Implement Swing Phase
- [ ] Verify `foot.py` swing trajectory
- [ ] Implement swing phase in `zmp_gait_controller.py`
- [ ] Add ZMP stability check during swing
- [ ] Test single step (SHIFT_R → STEP_L → STAND)

### Phase 4: Complete Walking Cycle
- [ ] Implement walking state machine
- [ ] Add phase transitions
- [ ] Tune phase durations (reduce from 3.0s to 0.5-0.6s)
- [ ] Test continuous walking (>10 steps)

### Phase 5: Integrate Preview Control
- [ ] Verify `preview_control.py` implementation
- [ ] Generate ZMP reference trajectory
- [ ] Compute optimal CoM trajectory
- [ ] Replace simple balance PID with preview control

### Phase 6: MAVLink Integration (FUTURE)
- [ ] Create `scripts/humanoid.lua`
- [ ] Port gait logic to Lua
- [ ] Add GUIDED mode handler
- [ ] Implement velocity command → gait parameters
- [ ] Test waypoint navigation

---

## Tuning Parameters

### Balance PID Gains
```python
# Standing (balance_controller.py)
Kp_pitch = 2.0
Ki_pitch = 0.01
Kd_pitch = 0.5

# Walking (gait_controller.py)
Kp_pitch = 0.08  # Weaker for walking
Ki_pitch = 0.001
Kd_pitch = 0.01

# Roll (NEW - for hip_roll control)
Kp_roll = 1.0
Ki_roll = 0.005
Kd_roll = 0.2
```

### Gait Timing
```python
# Current (too slow)
STAND_DURATION = 3.0  # s
SHIFT_DURATION = 3.0  # s
STEP_DURATION = 3.0   # s

# Target (realistic)
STAND_DURATION = 0.5  # s
SHIFT_DURATION = 0.5  # s
STEP_DURATION = 0.6   # s
DOUBLE_SUPPORT = 0.1  # s
```

### Step Parameters
```python
STEP_LENGTH = 0.12    # m (12cm)
STEP_WIDTH = 0.16     # m (hip separation)
STEP_HEIGHT = 0.04    # m (foot clearance)
ZMP_MARGIN = 0.02     # m (safety margin)
```

### Preview Control
```python
DT = 0.02             # s (50 Hz control)
COM_HEIGHT = 0.38     # m
PREVIEW_HORIZON = 20  # steps (0.4s)
Qe = 1.0              # Tracking weight
R = 1e-6              # Control weight
```

---

## Quick Reference

### Files to Modify
1. [`worlds/ardupilot_humanoid.sdf`](worlds/ardupilot_humanoid.sdf) - Add hip_roll joints
2. [`scripts/inverse_kinematics.py`](scripts/inverse_kinematics.py) - 3-DOF IK solver
3. [`scripts/zmp_gait_controller.py`](scripts/zmp_gait_controller.py) - Gait phases
4. [`scripts/preview_control.py`](scripts/preview_control.py) - LIPM controller
5. [`scripts/foot.py`](scripts/foot.py) - Swing trajectories
6. [`scripts/gait_controller.py`](scripts/gait_controller.py) - Phase timing

### Key Equations
```python
# LIPM dynamics
com_ddot = (g / h) * (com - zmp)

# ZMP position
zmp = com - (h / g) * com_ddot

# Preview control
u = -K_x @ state + Σ K_p[i] * zmp_ref[k+i]

# 3-DOF leg IK
hip_roll = atan2(y, z)
z_proj = z / cos(hip_roll)
hip_pitch, knee = leg_ik_2dof(x, z_proj)
```

### Success Metrics
- Standing: >10s without fall
- Weight shift: ZMP reaches target within 0.5s
- Swing: Foot clearance ≥0.03m, ZMP stable
- Walking: >10 continuous steps, velocity ~0.04 m/s

---

**End of gait-plan command**