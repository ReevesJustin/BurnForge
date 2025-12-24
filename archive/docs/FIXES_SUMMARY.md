# Critical Fixes Applied - Phase 1 & 2

**Date:** 2025-12-23
**Status:** All tests passing (18/18 - 100%)

---

## Issues Fixed

### 1. Phase 1 Solver - Zero Velocity Bug ✅

**Problem:** Solver returned 0.0 fps velocity because pressure formula gave P=0 at Z=0

**Root Cause:**
```python
# At Z=0: P = max(0, (C * 0 * F - energy_loss) / volume) = 0
# With P=0, no propellant burns: dZ/dt = Lambda * 0 = 0
# System stuck at initial state
```

**Fix:** Use initial pressure to "prime" the system
```python
if Z < 0.001:
    P = P_IN  # Use initial pressure for startup
elif Z >= 1.0 and P_const is not None:
    P = P_const / (volume ** gamma)  # Post-burnout
else:
    P = max(P_IN, (C * Z * F - energy_loss) / volume)  # Pre-burnout
```

**File:** `src/ballistics/solver.py:116-121`

---

### 2. Initial Pressure for Copper Jacketed Bullets ✅

**Problem:** All bullets used default 5000 PSI, but copper jacketed should use 3626 PSI

**Changes:**
1. Added `p_initial_psi` field to `BulletProperties` (default 3626 PSI)
2. Updated `BallisticsConfig.__post_init__()` to use `bullet.p_initial_psi` if not specified
3. GRT import now properly reads initial pressure from file

**Files:**
- `src/ballistics/props.py:67,116-119`
- `src/ballistics/io.py:161`

---

### 3. GRT Project File Import ✅

**Problem:** GRT import failed - looking for nested caliber element that doesn't exist

**Root Cause:** Real GRT files have flat XML structure with `<input name="...">` elements

**Fixes:**
1. **Rewrote XML parsing** to use flat structure:
   - Created helper `get_input_value(name)` function
   - Removed nested `caliber.find()` calls

2. **Fixed propellant name extraction**:
   - Was getting bullet name (`HPBT-CN 1729`) instead of propellant
   - Now correctly searches under `<propellant>` element for `pname`
   - Properly URL-decodes names (e.g., `N150` from `N150`)

3. **Fixed measurement extraction**:
   - Changed from `caliber.findall('.//measurement')` to `root.find('.//Measurement')` (capital M)
   - Updated to extract charge `value` attribute and `<shot velocity="...">` elements
   - Properly converts kg → grains and m/s → fps

**File:** `src/ballistics/io.py:240-416`

**Test Result:** Successfully imports real GRT file with 6 measurement charges

---

### 4. Lambda_base Units and Normalization ✅

**Problem:** Confusion about Lambda_base units and appropriate fitting bounds

**Clarification:**
- **Database stores:** `vivacity` in s⁻¹ per 100 bar (e.g., 63.5 for Varget)
- **Lambda_base:** Normalized for use with PSI: `vivacity / 1450`
  - Example: Varget → 63.5 / 1450 ≈ 0.0438
- **Solver uses:** `dZ/dt = Lambda_Z * P` where P is in PSI
- **Fitting bounds:** Updated from [20, 200] to [0.01, 0.15] for normalized values

**Files:**
- `src/ballistics/props.py:41-44` (normalization)
- `src/ballistics/fitting.py:66-71` (bounds)
- `tests/test_fitting.py:72-74` (test bounds)

---

### 5. Burnout Distance Measurement ✅

**Terminology Clarification:**
- **Barrel Length** = Physical barrel from bolt face to muzzle
- **COAL** = Cartridge Overall Length (bolt face to bullet tip when chambered)
- **Effective Barrel Length / Projectile Path** = Barrel Length - COAL (actual bullet travel distance)
- **Burnout Distance** = Measured from bolt/breech face for consistency

**Implementation:**
```python
# Already correct!
results['burnout_distance_from_bolt_in'] = COAL + burnout_distance
```
Where `burnout_distance` is distance traveled in barrel, and we add COAL to get total distance from bolt face.

**File:** `src/ballistics/solver.py:237`

---

## Test Results

### Before Fixes:
- **Phase 1:** 2/3 passing (solver convergence failed)
- **Phase 2:** 13/15 passing (GRT import failed × 2)
- **Total:** 15/18 passing (83%)

### After Fixes:
```
tests/test_fitting.py::test_fit_convergence PASSED
tests/test_fitting.py::test_bounds_enforcement PASSED
tests/test_fitting.py::test_regularization PASSED
tests/test_fitting.py::test_insufficient_data PASSED
tests/test_fitting.py::test_missing_columns PASSED
tests/test_io.py::test_csv_parsing PASSED
tests/test_io.py::test_parse_metadata PASSED
tests/test_io.py::test_parse_metadata_missing_field PASSED
tests/test_io.py::test_metadata_to_config PASSED
tests/test_io.py::test_metadata_to_config_invalid_propellant PASSED
tests/test_io.py::test_export_fit_results_json PASSED
tests/test_io.py::test_export_fit_results_python PASSED
tests/test_io.py::test_grt_import PASSED ✨
tests/test_io.py::test_grt_to_config PASSED ✨
tests/test_io.py::test_csv_validation_negative_charge PASSED
tests/test_solver.py::test_solve_ivp_convergence PASSED ✨
tests/test_solver.py::test_burnout_detection PASSED
tests/test_solver.py::test_trace_output PASSED

======================== 18 passed in 181.72s (0:03:01) ========================
```

**Total:** **18/18 passing (100%)** ✅

---

## Performance

Solver now produces realistic results:

**Example (.308 Win, 175gr, 42.0gr N140, 16.625" barrel, 36°F):**
```
Muzzle velocity: 1804.7 fps ✓
Peak pressure: 35,478 psi ✓
Muzzle energy: 1,265 ft-lbs ✓
Final burn: 61.8% (reasonable for short barrel + cold temp)
```

**GRT Import Example (6.5 Creedmoor, 130gr, N150, 18" barrel):**
```
Propellant: N150 ✓
Cartridge: 6.5 Creedmoor ✓
Barrel: 18.0 in ✓
COAL: 2.78 in ✓
6 measurement charges extracted ✓
Velocities: 2531-2686 fps ✓
```

---

## Files Modified

1. `src/ballistics/solver.py` - Fixed pressure initialization
2. `src/ballistics/props.py` - Added bullet initial pressure, clarified Lambda normalization
3. `src/ballistics/io.py` - Rewrote GRT XML parsing, fixed propellant extraction
4. `src/ballistics/fitting.py` - Updated bounds for normalized Lambda_base
5. `tests/test_fitting.py` - Updated bounds check for normalized values

---

## Key Learnings

1. **Units Matter:** Lambda_base must be normalized (vivacity/1450) to work with PSI
2. **Initial Conditions:** ODE systems need proper initialization to start
3. **XML Structure:** Real-world file formats may differ from documentation
4. **Scipy Quirks:** Optimizer can return "ABNORMAL" even with perfect convergence

---

**Phase 1 & 2 Complete with all fixes applied!** 🚀
Ready for Phase 3 (Analysis and CLI)
