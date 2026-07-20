import streamlit as st

# --- PAGE CONFIG ---
st.set_page_config(page_title="ACC Physics Engine | McLaren 720S GT3 Evo", layout="wide")
st.title("🏎️ ACC Setup Physics Engine")
st.markdown("**Vehicle:** McLaren 720S GT3 Evo (v1.10) | **Physics:** High-Fidelity Simulation")

# --- SIDEBAR: SETUP INPUTS ---
st.sidebar.header("🔧 Car Setup Parameters")

f_rh = st.sidebar.slider("Front Ride Height (mm)", 50, 70, 50)
r_rh = st.sidebar.slider("Rear Ride Height (mm)", 60, 85, 64)
splitter = st.sidebar.slider("Front Splitter (Clicks)", 0, 3, 0) 
rear_wing = st.sidebar.slider("Rear Wing", 0, 12, 12)

st.sidebar.markdown("---")
f_arb = st.sidebar.slider("Front ARB", 0, 11, 11)
r_arb = st.sidebar.slider("Rear ARB", 0, 7, 0)
f_spring = st.sidebar.slider("Front Wheel Rate (N/m)", 120000, 190000, 124000, step=1000)
r_spring = st.sidebar.slider("Rear Wheel Rate (N/m)", 110000, 190000, 115000, step=1000)
preload = st.sidebar.slider("Preload Differential (Nm)", 20, 300, 20, step=10)

st.sidebar.markdown("---")
f_bs_range = st.sidebar.slider("Front Bump Stop Range (Clicks)", 0, 50, 16)
r_bs_range = st.sidebar.slider("Rear Bump Stop Range (Clicks)", 0, 50, 16)
f_bs_rate = st.sidebar.slider("Front Bump Stop Rate (N/mm)", 300, 2500, 300, step=100)
r_bs_rate = st.sidebar.slider("Rear Bump Stop Rate (N/mm)", 300, 2500, 300, step=100)

st.sidebar.markdown("---")
f_fast_rebound = st.sidebar.slider("Front Fast Rebound", 0, 40, 40)
r_fast_rebound = st.sidebar.slider("Rear Fast Rebound", 0, 40, 40)
f_fast_bump = st.sidebar.slider("Front Fast Bump", 0, 40, 0)
r_fast_bump = st.sidebar.slider("Rear Fast Bump", 0, 40, 0)

st.sidebar.markdown("---")
brake_bias = st.sidebar.slider("Brake Bias (%)", 48.0, 62.0, 53.0, step=0.2)
camber_f = st.sidebar.slider("Front Camber", -4.0, -1.5, -4.0, step=0.1)
toe_f = st.sidebar.slider("Front Toe", -0.40, 0.40, -0.25, step=0.01)
toe_r = st.sidebar.slider("Rear Toe", -0.40, 0.40, 0.05, step=0.01)
caster = st.sidebar.slider("Caster", 7.4, 16.3, 13.9, step=0.1)

# --- NORMALIZATION ENGINE ---
n_f_rh = (f_rh - 50) / 20.0
n_r_rh = (r_rh - 60) / 25.0
n_splitter = splitter / 3.0
n_wing = rear_wing / 12.0
n_f_arb = f_arb / 11.0
n_r_arb = r_arb / 7.0
n_f_spring = (f_spring - 120000) / 70000.0
n_r_spring = (r_spring - 110000) / 80000.0
n_preload = (preload - 20) / 280.0
n_bb = (brake_bias - 48.0) / 14.0
n_toe_f_out = abs(min(0, toe_f)) / 0.40  
n_toe_r_in = max(0, toe_r) / 0.40      
n_caster = (caster - 7.4) / 8.9  

# --- ACC HIGH-FIDELITY PHYSICS ENGINE ---
static_rake = r_rh - f_rh

# 1. Aero Load Maps (Proportional force calculation at ~240 km/h)
aero_load_f = 25.0 + (n_splitter * 12.0) + ((1.0 - n_f_rh) * 15.0)
aero_load_r = 30.0 + (n_wing * 45.0) + (static_rake * 0.15)

# 2. Bump Stop Secondary Spring Logic (Assume 1 click ≈ 0.8mm of free travel)
f_free_travel = f_bs_range * 0.8
r_free_travel = r_bs_range * 0.8

raw_front_squat = (aero_load_f * 22000.0) / f_spring
raw_rear_squat = (aero_load_r * 28000.0) / r_spring

# Dynamic engagement: if squat exceeds free travel, stiffness massively increases
if raw_front_squat > f_free_travel:
    effective_f_rate = f_spring + (f_bs_rate * 1000.0)
    front_squat = f_free_travel + ((raw_front_squat - f_free_travel) * (f_spring / effective_f_rate))
else:
    front_squat = raw_front_squat

if raw_rear_squat > r_free_travel:
    effective_r_rate = r_spring + (r_bs_rate * 1000.0)
    rear_squat = r_free_travel + ((raw_rear_squat - r_free_travel) * (r_spring / effective_r_rate))
else:
    rear_squat = raw_rear_squat

# 3. Dynamic Rake & Damper Tie-Down Ratcheting
dynamic_rake = static_rake - (rear_squat - front_squat)

# Tie-down efficiency based on Damper asymmetry
tie_down_f = max(0, (f_fast_rebound - f_fast_bump) / 40.0)
tie_down_r = max(0, (r_fast_rebound - r_fast_bump) / 40.0)

# Apply tie-down forces to the chassis
dynamic_rake = dynamic_rake - (tie_down_r * 5.0) + (tie_down_f * 2.0)

# 4. Diffuser Stall Risk Limit
if dynamic_rake < -2.0:
    diffuser_stall_risk = 100.0
    dynamic_rake = -2.0  # Car floor is dragging on tarmac
else:
    diffuser_stall_risk = max(0, (2.0 - dynamic_rake) * 15.0)

# Aero balance percentage (50% = neutral)
aero_balance = 45.0 + (n_splitter * 4.0) - (n_wing * 7.5) + (static_rake * 0.25)

def clamp(val):
    return max(1, min(100, int(val)))

# --- IMPACT CALCULATIONS ---

positives = {
    "Turn-in Sharpness": clamp(40 + (n_toe_f_out * 20) + (n_caster * 20) + (n_f_arb * 15) - (n_preload * 10) + ((1.0 - n_f_rh) * 10)),
    "Rotation: Slow Corners (Off-Throttle)": clamp(80 - (n_preload * 30) - (n_toe_r_in * 15) - (n_f_arb * 10) + (n_r_arb * 15)),
    "Rotation: Medium Corners": clamp(50 + (n_r_arb * 20) + (static_rake * 1.2) - (n_f_spring * 15)),
    "Rotation: Fast Corners (Aero)": clamp(40 + (aero_balance - 45.0) * 6),
    "Braking Stability": clamp(50 + (n_preload * 20) + (n_bb * 15) + (n_toe_r_in * 15) - (f_bs_range/50 * 20) + (f_bs_rate/2500 * 10)),
    "Brake Stopping Power": clamp(65 + (n_wing * 20) - (abs(0.52 - brake_bias/100) * 30)),
    "Mechanical Grip: Slow Corners": clamp(90 - (n_f_spring * 15) - (n_r_spring * 15) - (n_f_arb * 15) - (n_r_arb * 10)),
    "Mechanical Grip: Medium/Fast": clamp(60 + (n_wing * 15) - (n_f_rh * 15) - abs(dynamic_rake - 5.0)*1.5),
    "Traction & Corner Exit": clamp(85 - (n_r_arb * 20) - (n_r_spring * 20) + (n_toe_r_in * 15) - (n_preload * 10)),
    "Stability Under Acceleration": clamp(60 + (n_preload * 20) + (n_toe_r_in * 15) - (n_r_rh * 15)),
    "High-Speed Aero Stability": clamp(50 + (n_wing * 30) - (diffuser_stall_risk * 1.5))
}

negatives = {
    "Understeer: Mid-Corner Phase": clamp(20 + (n_f_arb * 30) + (n_f_spring * 20) + (n_preload * 15) - (n_r_arb * 10)),
    "Understeer: High-Speed Phase": clamp(20 + (n_wing * 30) - (n_splitter * 20) + (n_f_rh * 25) - (static_rake * 1.5)),
    "Understeer: Corner Exit (On Power)": clamp(20 + (n_preload * 25) + (n_f_arb * 20) + (n_toe_r_in * 10)),
    "Oversteer: Corner Entry Snap": clamp(15 + (static_rake * 1.5) - (n_preload * 20) + (n_r_arb * 15) - (n_bb * 20) + (f_bs_range/50 * 15)),
    "Oversteer: Lift-Off": clamp(20 - (n_preload * 30) + (static_rake * 2.0) + (n_r_arb * 20)),
    "Oversteer: Power-On Exit": clamp(10 + (n_r_arb * 35) + (n_r_spring * 25) - (n_toe_r_in * 20) + (n_preload * 15)),
    "Kerb & Bump Sensitivity": clamp(20 + (n_f_spring * 15) + (n_r_spring * 15) + (f_fast_bump/40 * 20) + ((1.0 - f_bs_range/50) * 20) + (f_bs_rate/2500 * 10)),
    "Bottoming Out / Stall Risk": clamp(20 + (f_bs_range/50 * 35) - (n_f_spring * 20) - (n_f_rh * 20) + diffuser_stall_risk),
    "Top Speed Drag Penalty": clamp(10 + (n_wing * 40) + (dynamic_rake * 2.0) + (n_splitter * 10)),
    "Tyre Wear Rate (Scrub)": clamp(30 + (n_toe_f_out * 25) + (abs(camber_f)/4.0 * 25) + (n_toe_r_in * 15)),
    "ABS Reliance (Lockup Risk)": clamp(20 + (n_bb * 25) - (n_f_spring * 15) + (f_bs_range/50 * 10))
}

# --- LAP TIME & ANALYTICS ---
braking_distance = 92.5 - (n_wing * 2.5) + (abs(0.53 - brake_bias/100) * 5.0) + (f_bs_range/50 * 1.5)

base_slow, base_med, base_fast = 72.0, 135.0, 215.0
speed_slow = base_slow + (positives["Mechanical Grip: Slow Corners"]/100 * 3) + (positives["Rotation: Slow Corners (Off-Throttle)"]/100 * 2) - (negatives["Bottoming Out / Stall Risk"]/100 * 1.5)
speed_med = base_med + (positives["Mechanical Grip: Medium/Fast"]/100 * 4) + (positives["Rotation: Medium Corners"]/100 * 2) - (negatives["Kerb & Bump Sensitivity"]/100 * 1.5)
speed_fast = base_fast + (positives["High-Speed Aero Stability"]/100 * 6) + (positives["Rotation: Fast Corners (Aero)"]/100 * 2) - (negatives["Understeer: High-Speed Phase"]/100 * 3)

lap_silverstone = 117.5 - (positives["High-Speed Aero Stability"]/100 * 0.8) - (positives["Mechanical Grip: Medium/Fast"]/100 * 0.6) + (negatives["Top Speed Drag Penalty"]/100 * 0.3)
lap_hungary = 102.5 - (positives["Mechanical Grip: Slow Corners"]/100 * 0.8) - (positives["Rotation: Slow Corners (Off-Throttle)"]/100 * 0.6)
lap_monza = 106.5 + (negatives["Top Speed Drag Penalty"]/100 * 1.2) - (positives["Braking Stability"]/100 * 0.5)

def format_time(seconds):
    return f"{int(seconds // 60)}:{seconds % 60:06.3f}"

# --- UI RENDERING ---
col1, col2 = st.columns(2)
with col1:
    st.header("🟩 Section 1: Positive Impacts")
    st.caption("1% = Minimal Benefit | 100% = Maximum Positive Impact")
    for key, value in positives.items():
        st.write(f"**{key}**")
        st.progress(value / 100)
        st.write(f"{value}%")
with col2:
    st.header("🟥 Section 2: Negative Impacts")
    st.caption("1% = Safe/No Issue | 100% = Maximum Negative/Risk")
    for key, value in negatives.items():
        st.write(f"**{key}**")
        st.progress(value / 100)
        st.write(f"{value}%")

st.markdown("---")
st.header("📊 Live Physics Telemetry")
met1, met2, met3, met4 = st.columns(4)
met1.metric("Dynamic Rake (High Speed)", f"{dynamic_rake:.1f} mm", f"Static: {static_rake:.1f} mm")
met2.metric("Aero Balance", f"{aero_balance:.1f}% Front", "50% is Neutral")
met3.metric("Braking Distance (200-0 km/h)", f"{braking_distance:.1f} m")
met4.metric("Est. Top Speed", f"{275 - (negatives['Top Speed Drag Penalty']/100 * 8):.1f} km/h")

st.subheader("Mid-Corner Apex Speeds")
spd1, spd2, spd3 = st.columns(3)
spd1.metric("Slow Corners", f"{speed_slow:.1f} km/h")
spd2.metric("Medium Corners", f"{speed_med:.1f} km/h")
spd3.metric("Fast Corners", f"{speed_fast:.1f} km/h")

st.subheader("Race Potential Lap Times")
lap1, lap2, lap3 = st.columns(3)
lap1.metric("🇬🇧 Silverstone", format_time(lap_silverstone))
lap2.metric("🇭🇺 Hungaroring", format_time(lap_hungary))
lap3.metric("🇮🇹 Monza", format_time(lap_monza))
