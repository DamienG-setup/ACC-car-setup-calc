import streamlit as st
import math

# --- PAGE CONFIG ---
st.set_page_config(page_title="ACC Setup Impact Calculator | McLaren 720S GT3 Evo", layout="wide")
st.title("🏎️ ACC Setup Impact Calculator")
st.markdown("**Vehicle:** McLaren 720S GT3 Evo (v1.10) | **Baseline:** Extreme Tie-Down Setup")

# --- SIDEBAR: SETUP INPUTS (Pre-loaded with your exact baseline) ---
st.sidebar.header("🔧 Car Setup Parameters")

f_rh = st.sidebar.slider("Front Ride Height (mm)", 50, 70, 50)
r_rh = st.sidebar.slider("Rear Ride Height (mm)", 64, 80, 64)
splitter = st.sidebar.slider("Front Splitter", 0, 3, 0) # Adjusted based on your request
rear_wing = st.sidebar.slider("Rear Wing", 0, 12, 12)

st.sidebar.markdown("---")
f_arb = st.sidebar.slider("Front ARB", 0, 11, 11)
r_arb = st.sidebar.slider("Rear ARB", 0, 7, 0)
f_spring = st.sidebar.slider("Front Wheel Rate (N/m)", 124000, 182000, 124000, step=1000)
r_spring = st.sidebar.slider("Rear Wheel Rate (N/m)", 115000, 170000, 115000, step=1000)
preload = st.sidebar.slider("Preload Differential (Nm)", 20, 300, 20, step=10)

st.sidebar.markdown("---")
f_bs_range = st.sidebar.slider("Front Bump Stop Range (mm)", 0, 50, 16)
r_bs_range = st.sidebar.slider("Rear Bump Stop Range (mm)", 0, 50, 16)
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
caster = st.sidebar.slider("Caster", 7.4, 13.9, 13.9, step=0.1)

# --- PHYSICS CALCULATIONS ENGINE ---
# Normalize inputs to a 0.0 - 1.0 scale for mathematical weighting
n_f_rh = (f_rh - 50) / 20
n_r_rh = (r_rh - 64) / 16
n_splitter = splitter / 3
n_wing = rear_wing / 12
n_f_arb = f_arb / 11
n_r_arb = r_arb / 7
n_f_spring = (f_spring - 124000) / 58000
n_r_spring = (r_spring - 115000) / 55000
n_preload = (preload - 20) / 280
n_bb = (brake_bias - 48.0) / 14.0
n_toe_f_out = abs(min(0, toe_f)) / 0.40  # Negative toe is toe-out
n_toe_r_in = max(0, toe_r) / 0.40      # Positive toe is toe-in

# Helper function to clamp percentages between 1 and 100
def clamp(val):
    return max(1, min(100, int(val)))

# 1. POSITIVE IMPACTS MATH (1% = Negative/Poor, 100% = Maximum Positive Benefit)
positives = {}
positives["Turn-in Sharpness"] = clamp(50 + (n_toe_f_out * 20) + (caster/13.9 * 15) + (n_f_arb * 15) - (n_preload * 10))
positives["Rotation: Slow Corners (Off-Throttle)"] = clamp(80 - (n_preload * 30) - (n_toe_r_in * 10) - (n_f_arb * 10))
positives["Rotation: Medium Corners"] = clamp(50 + (n_r_arb * 20) + (n_r_rh * 15) - (n_f_spring * 10))
positives["Rotation: Fast Corners (Aero)"] = clamp(40 + (n_r_rh * 25) + (n_splitter * 25) - (n_wing * 10))
positives["Braking Stability"] = clamp(40 + (n_preload * 20) + (n_bb * 15) + (n_toe_r_in * 10) + (f_bs_range/50 * 10))
positives["Brake Stopping Power"] = clamp(70 + (n_wing * 15) - (abs(0.5 - n_bb) * 20)) # Optimal BB = better stopping
positives["Mechanical Grip: Slow Corners"] = clamp(90 - (n_f_spring * 15) - (n_r_spring * 15) - (n_f_arb * 10))
positives["Mechanical Grip: Medium/Fast"] = clamp(60 + (n_wing * 20) - (n_f_rh * 10) + (f_bs_rate/2500 * 10))
positives["Traction & Corner Exit"] = clamp(80 - (n_r_arb * 20) - (n_r_spring * 15) + (n_toe_r_in * 10))
positives["Stability Under Acceleration"] = clamp(60 + (n_preload * 15) + (n_toe_r_in * 15) - (n_r_rh * 10))
positives["High-Speed Aero Stability"] = clamp(40 + (n_wing * 30) + (f_fast_rebound/40 * 15) - (n_r_rh * 15))

# 2. NEGATIVE IMPACTS MATH (1% = Safe/Positive, 100% = Maximum Negative/Risk)
negatives = {}
negatives["Understeer: Mid-Corner Phase"] = clamp(20 + (n_f_arb * 35) + (n_f_spring * 20) + (n_preload * 10))
negatives["Understeer: High-Speed Phase"] = clamp(20 + (n_wing * 30) - (n_splitter * 20) + (n_f_rh * 15))
negatives["Understeer: Corner Exit (On Power)"] = clamp(20 + (n_preload * 25) + (n_f_arb * 15))
negatives["Oversteer: Corner Entry Snap"] = clamp(10 + (n_r_rh * 25) - (n_preload * 20) + (n_r_arb * 15) - (n_bb * 10))
negatives["Oversteer: Lift-Off"] = clamp(20 - (n_preload * 25) + (n_r_rh * 20) + (n_r_arb * 15))
negatives["Oversteer: Power-On Exit"] = clamp(10 + (n_r_arb * 35) + (n_r_spring * 20) - (n_toe_r_in * 15))
negatives["Kerb & Bump Sensitivity"] = clamp(30 + (n_f_spring * 20) + (n_f_arb * 15) + (f_fast_bump/40 * 25))
negatives["Bottoming Out / Stall Risk"] = clamp(90 - (f_bs_range/50 * 30) - (n_f_spring * 20) - (n_f_rh * 20))
negatives["Top Speed Drag Penalty"] = clamp(20 + (n_wing * 40) + (n_r_rh * 20) - (f_fast_rebound/40 * 15))
negatives["Tyre Wear Rate (Scrub)"] = clamp(40 + (abs(n_toe_f_out) * 20) + (abs(camber_f)/4.0 * 20) + (n_f_arb * 10))
negatives["ABS Reliance (Lockup Risk)"] = clamp(20 + (n_bb * 25) - (n_f_spring * 10))

# --- ANALYTICS ENGINE (Bottom Section) ---
static_rake = r_rh - f_rh

# Tie-down logic: Soft springs + high rebound = car gets sucked to the floor and stays there
aero_load_f = 20 + (n_splitter * 15) + (1.0 - n_f_rh) * 10
aero_load_r = 30 + (n_wing * 40) + (n_r_rh * 10)
front_squat = (aero_load_f * 20000) / f_spring
rear_squat = (aero_load_r * 25000) / r_spring

# Dynamic Rake is static minus how much more the rear squats than the front
dynamic_rake = static_rake - (rear_squat - front_squat)
if f_fast_rebound > 30 and r_fast_rebound > 30 and f_fast_bump < 10:
    dynamic_rake *= 0.5  # Tie-down heavily flattens dynamic rake

aero_balance = 40.0 + (n_splitter * 5.0) - (n_wing * 8.0) + (static_rake * 0.2)
braking_distance = 92.5 - (n_wing * 2.5) + (abs(0.53 - brake_bias/100) * 5.0)

# Corner Speeds (Estimated apex km/h)
base_slow = 72.0
base_med = 135.0
base_fast = 215.0

speed_slow = base_slow + (positives["Mechanical Grip: Slow Corners"]/100 * 3) + (positives["Rotation: Slow Corners (Off-Throttle)"]/100 * 2)
speed_med = base_med + (positives["Mechanical Grip: Medium/Fast"]/100 * 4) + (positives["Rotation: Medium Corners"]/100 * 2)
speed_fast = base_fast + (positives["High-Speed Aero Stability"]/100 * 6) + (positives["Rotation: Fast Corners (Aero)"]/100 * 2) - (negatives["Understeer: High-Speed Phase"]/100 * 3)

# Lap Time Simulator (Based on baseline pace)
# Silverstone heavily relies on High-Speed Aero and Med/Fast Grip
lap_silverstone = 117.5 - (positives["High-Speed Aero Stability"]/100 * 0.8) - (positives["Mechanical Grip: Medium/Fast"]/100 * 0.6) + (negatives["Top Speed Drag Penalty"]/100 * 0.3)
# Hungaroring relies on Slow/Med grip and Rotation
lap_hungary = 102.5 - (positives["Mechanical Grip: Slow Corners"]/100 * 0.8) - (positives["Rotation: Slow Corners (Off-Throttle)"]/100 * 0.6)
# Monza relies purely on Drag penalty and Braking
lap_monza = 106.5 + (negatives["Top Speed Drag Penalty"]/100 * 1.2) - (positives["Braking Stability"]/100 * 0.5)

def format_time(seconds):
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m}:{s:06.3f}"


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
st.header("📊 Live Telemetry & Analytics")

met1, met2, met3, met4 = st.columns(4)
met1.metric("Dynamic Rake (High Speed)", f"{dynamic_rake:.1f} mm", f"Static: {static_rake:.1f} mm")
met2.metric("Aero Balance", f"{aero_balance:.1f}% Front", "50% is Neutral")
met3.metric("Braking Distance (200-0 km/h)", f"{braking_distance:.1f} m")
met4.metric("Est. Top Speed", f"{275 - (negatives['Top Speed Drag Penalty']/100 * 8):.1f} km/h")

st.subheader("Mid-Corner Apex Speeds")
spd1, spd2, spd3 = st.columns(3)
spd1.metric("Slow Corners (e.g., Hairpins)", f"{speed_slow:.1f} km/h")
spd2.metric("Medium Corners", f"{speed_med:.1f} km/h")
spd3.metric("Fast Corners (e.g., Maggotts)", f"{speed_fast:.1f} km/h")

st.subheader("Race Potential Lap Times")
lap1, lap2, lap3 = st.columns(3)
lap1.metric("🇬🇧 Silverstone", format_time(lap_silverstone))
lap2.metric("🇭🇺 Hungaroring", format_time(lap_hungary))
lap3.metric("🇮🇹 Monza", format_time(lap_monza))
