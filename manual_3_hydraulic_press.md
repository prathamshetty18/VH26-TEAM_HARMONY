# Hydraulic Press — Model HP-2200 Troubleshooting Manual

## Section 1: Overview
[Page 1]
The Hydraulic Press Model HP-2200 is a 2,200-metric-ton down-acting industrial hydraulic forming press engineered for heavy automotive body panel stamping, composite compression molding, and precision cold forging operations. Operating in high-tonnage fabrication plants, stamping lines, and foundry press cells, the HP-2200 features a monolithic four-column pre-stressed tie-rod frame, dual high-volume axial piston variable-displacement hydraulic pumps, high-speed overhead prefill poppet valves, and a dedicated closed-circuit fluid cooling and conditioning system. The press is capable of delivering up to 280 bar operating pressure across four hydraulic cylinders, maintaining strict platen parallelism through closed-loop electro-hydraulic proportional servo valve controls.

## Section 2: Error Codes

[Page 2]
### H201 — Main Ram Proportional Pressure Loss
**Meaning:** Main hydraulic cylinder pressure transducer PT-01 detects that ram hydraulic pressure fails to achieve the commanded 280 bar tonnage within 4.0 seconds following the seating of the main prefill overhead poppet valve, preventing proper tonnage clamp.

**Probable Cause(s):** Blown or thermally deteriorated chevron packing ring seals on the primary 650 mm ram piston; sticking or mechanically contaminated proportional directional pressure relief valve PRV-1; foreign metal swarf or particle wedged on the main overhead prefill valve poppet seat, allowing oil to bypass back into the gravity overhead tank; internal barrel wall scoring inside the main cylinder.

**Corrective Action:**
1. Engage the mechanical platen safety latch blocks into position beneath the ram platen and depress the hydraulic system pressure de-energize pushbutton to bleed residual accumulator pressure down to 0 bar.
2. Check the electrical resistance of the proportional relief valve PRV-1 solenoid coil using a calibrated multimeter (standard coil resistance must measure between 18.5 and 24.0 ohms). Replace coil if open circuit.
3. Access the overhead prefill tank inspection port; remove and inspect the main poppet check valve seat for metallic debris, contamination, or scarred mating faces that prevent 100% positive sealing.
4. Inspect the cylinder rod glands beneath the main press crown for external fluid weepage or pooling hydraulic oil on the platen top surface. If fluid leakage exceeds 15 drops per minute, replace the main multi-lip chevron seal packing assembly.
5. Close the circuit, retract the safety latch blocks, and execute a dry pressure ramp test up to 150 bar in manual jog mode while logging transducer PT-01 voltage output on the diagnostics console.

[Page 2]
### H205 — Hydraulic Oil High Temperature Shutdown
**Meaning:** The resistance temperature transmitter TT-02 immersed in the main 1,500-liter oil reservoir registers a bulk hydraulic fluid temperature exceeding 65°C, triggering an automatic pump unload and cycle shutdown to prevent thermal breakdown of fluid anti-wear additives and seal failure.

**Probable Cause(s):** Heavily fouled, scaled, or clogged tube bundle in the external shell-and-tube water-cooled heat exchanger; plant cooling water supply shut off or water flow below 60 liters per minute; internal high-pressure relief valve bypassing continuously at full pressure setting due to an electrical sequencing fault; degraded ISO VG 46 hydraulic fluid undergoing severe shear thinning.

**Corrective Action:**
1. Keep the hydraulic circulation auxiliary pump running in low-pressure idle mode to circulate fluid through the cooling circuit; do not actuate main pressing cylinders.
2. Inspect the plant cooling tower water supply valve; verify cooling water inlet pressure is at least 3.5 bar and verify the supply water temperature is below 22°C.
3. Inspect the cooling water duplex basket strainer; switch over to the clean basket, remove the clogged strainer basket, and wash out calcium scale, silt, and algae.
4. Use a handheld FLIR infrared thermal camera to scan the main valve manifold block; identify any relief valves or bypass lines showing localized hot spots exceeding 75°C, indicating an internal continuous fluid bypass leak.
5. Extract a fluid sample from reservoir sample tap ST-1 and evaluate fluid clarity and oxidation level; if fluid is darkened, smells acrid, or shows kinematic viscosity below 38 cSt at 40°C, perform a full oil change with fresh ISO VG 46 mineral hydraulic fluid.

[Page 3]
### H312 — Nitrogen Accumulator Pre-Charge Pressure Low
**Meaning:** Pressure switch AP-03 mounted on the high-pressure bladder accumulator bank senses nitrogen pre-charge gas pressure dropping below the safe threshold of 110 bar during high-speed decompression transitions.

**Probable Cause(s):** Ruptured or torn synthetic rubber accumulator internal bladder; leaking Schrader gas charging valve core; mechanical seal deterioration around the accumulator top gas port plug; gradual nitrogen gas permeation during extended operational service.

**Corrective Action:**
1. Lower the press platen to bottom dead center and open the manual accumulator safety shutoff block dump valve; verify the analog system pressure gauge reads zero before attempting service.
2. Remove the protective gas valve cap from the accumulator shell and inspect for traces of hydraulic fluid inside the valve stem (the presence of liquid oil confirms a ruptured internal bladder).
3. If oil is present, unbolt the accumulator shell from its mounting rack, replace the internal elastomeric bladder kit (Part No. HP-ACC-B50), and replace the bottom anti-extrusion fluid poppet.
4. If no oil is present, connect a certified nitrogen charging and testing manifold with a 0-250 bar calibrated gauge to the gas valve stem.
5. Using a commercial bottle of dry high-purity industrial nitrogen gas (99.99% purity), recharge the accumulator slowly until the pre-charge pressure reaches the specification of 130 bar at 20°C ambient.
6. Check the gas charging valve core and top sealing plug using soapy water leak detection solution to ensure zero bubble formation.

[Page 3]
### H420 — Ram Platen Parallelism Skew Error
**Meaning:** The dual magnetostrictive absolute linear position transducers (LT-01 Left and LT-02 Right) measure a platen tilt or angular skew exceeding 0.35 millimeters across the 2,400 mm bed width during downward pressing motion, threatening tooling dies and column guide bushings.

**Probable Cause(s):** Severe off-center die placement creating an unbalanced reactive pressing torque; contaminated proportional servo flow valve controlling the left or right booster cylinder; galling or severe dry friction on one of the four main bronze column guide bushings; loose foundation anchor bolts under one corner of the press bed.

**Corrective Action:**
1. Immediately abort the pressing stroke and jog the main ram upward to top position in low-speed manual mode.
2. Check the stamping die alignment on the press bed bolster plate; verify the center of tonnage of the tooling die is positioned within +/- 5 mm of the bed theoretical center mark.
3. Clean and inspect the ground surfaces of the four hardened vertical tie-rod columns; check for dry abrasive galling, scoring, or bronze pickup.
4. Check the automatic centralized grease lubricator supplying the column bushings; verify grease reservoir is full of NLGI Grade 2 lithium grease with extreme pressure (EP) additives and verify grease lines are pumping smoothly to all 8 column lube ports.
5. Access the HMI controller calibration screen, select "Platen Parallelism Zero Calibration", and perform a closed-loop electronic leveling trim to balance the proportional flow valve drive signals.

[Page 4]
### H515 — Low Hydraulic Fluid Level Warning
**Meaning:** The dual-stage magnetic float level switch LS-02 inside the 1,500-liter primary hydraulic tank detects that the reservoir fluid level has dropped below the first-stage alarm threshold of 600 millimeters from the tank floor.

**Probable Cause(s):** High-pressure piping flange O-ring failure; ruptured flexible hydraulic hose on the bottom ejector cylinder assembly; leaking shaft seal on main variable displacement axial piston pump P1; hydraulic fluid loss into underground foundation trenches or press sump pit.

**Corrective Action:**
1. Perform an immediate visual walkaround of the press pit, pump basement, and cylinder overhead platform to trace active hydraulic fluid pools or dripping lines.
2. If an active fluid spray or hose failure is discovered, press the Emergency Stop immediately. Replace damaged high-pressure 4-wire spiral braided hose assemblies immediately.
3. Inspect SAE 4-bolt split flange connections across the main manifold blocks; tighten loose flange cap screws to 120 Nm torque or replace extruded 90 Durometer polyurethane O-rings.
4. Connect an offline mobile filter cart equipped with 10-micron water-absorbing filter elements to the reservoir quick-connect fill port.
5. Pump fresh, pre-filtered ISO VG 46 anti-wear hydraulic oil into the tank until the level sight gauge reaches the 85% full mark (approximately 400 liters required from first alarm point).
6. Reset the level fault alarm on the operator HMI panel.

[Page 4]
### H622 — Light Curtain Safety Violation Fault
**Meaning:** The Category 4 infrared safety light curtain array installed across the front operator loading aperture detects beam optical interruptions during a high-speed downward ram movement, commanding an instantaneous safety stop.

**Probable Cause(s):** Physical penetration of the optical safety plane by operator hands or tooling handling equipment; heavy oil mist, smoke, or airborne grease coating the optical transmitter or receiver lenses; mechanical vibration loosening the optical column alignment bracket, resulting in beam drift.

**Corrective Action:**
1. Confirm that all operators, transport carts, and raw sheet metal blanks are completely clear of the safety zone defined by the optical transmitter and receiver pillars.
2. Inspect the protective clear acrylic lenses of both the transmitter (TX) and receiver (RX) towers; gently wipe clean with a soft microfiber cloth dampened with mild soapy water. Do not use aggressive solvents that can craze the acrylic plastic.
3. Loosen the optical tower swivel mounting bolts slightly and adjust the vertical and horizontal angle while observing the diagnostic display bar on the receiver; align until all green channel indicators illuminate solidly.
4. Check the safety relay module SR-2 located inside control cabinet 1; verify both safety channel inputs K1 and K2 are energized simultaneously.
5. Press the illuminated yellow "Safety Barrier Reset" pushbutton located on the front operator control pedestal.

## Section 3: Common Symptoms (Natural Language)

[Page 5]
### Severe Hydraulic Hammer and Pipe Banging on Ram Decompression
**Likely Cause:** Rapid release of stored elastic strain energy in the hydraulic oil and frame steel caused by premature opening of the main prefill poppet or an improperly tuned decompression ramp parameter on the digital proportional valve controller.
**Corrective Action:** Access the hydraulic valve amplifier card setup parameters via the diagnostic laptop interface. Increase the decompression ramp time constant from 180 milliseconds to 420 milliseconds to enforce a gradual, linear pressure bleed-down before the main poppet is allowed to crack open. Inspect the pilot decompression cartridge valve poppet seat for internal scoring or a fatigued pilot spring. Check all hydraulic pipe clamps on the overhead delivery lines; tighten loose clamp bracket bolts and replace any cracked or hardened polypropylene clamp body inserts with fresh vibration-damping elastomer sleeves.

[Page 5]
### Jerky or Stuttering Ram Movement During Downward Approach
**Likely Cause:** Air entrainment in the main cylinder oil columns, stick-slip friction on dry tie-rod bronze guide bushings, or mechanical binding of the piston guide wear rings due to contaminated fluid.
**Corrective Action:** Jog the ram to top dead center. Slightly crack open the manual high-point bleed petcock valves situated at the highest apex of each of the four main cylinder top covers. Jog the ram slowly down at 10 mm/s in manual mode until continuous bubble-free hydraulic oil expels from the bleed ports, then retighten the petcocks securely. Inspect the tie-rod guide column surfaces; generously spray manual lubricating oil onto the columns and run three full-stroke cycles to coat the internal bronze bushings. If jerking persists, inspect the main cylinder internal sliding guide bands for debris contamination.

[Page 6]
### Hydraulic Pump Emitting Loud Cavitation Whine
**Likely Cause:** Restriction in the pump suction line caused by a heavily silted suction strainer inside the oil tank, high fluid viscosity due to cold reservoir oil below minimum operating temperature, or atmospheric air entering through a worn pump driveshaft seal.
**Corrective Action:** Immediately check reservoir fluid temperature gauge. If the oil is below 20°C, turn on the auxiliary electric immersion tank heaters and wait until the oil temperature reaches at least 32°C before running the main pumps under load. Check that the suction butterfly isolation valve is locked in the 100% full-open position. Drain the fluid level down to maintenance level and remove the 100-mesh wire cloth pump suction strainer from the bottom tank port; wash thoroughly in mineral spirits and blow dry with compressed air. Check the pump driveshaft lip seal for oil weeping or telltale suction air hissing sounds.

[Page 6]
### Failure to Hold Tonnage at End of Stroke
**Likely Cause:** Internal high-pressure oil bypassing across worn piston packing seals inside one of the main cylinders, a leaking pilot-operated cartridge check valve in the tonnage manifold, or a drifting proportional pressure control valve.
**Corrective Action:** Place a solid calibrated load cell block on the press bed and command a 2,000-ton clamp for 120 seconds in diagnostic hold mode. Record the rate of tonnage loss on the digital chart recorder; if tonnage drops at a rate greater than 3.0 tons per second, isolate the cylinders individually using the manifold ball valves to determine which cylinder has internal seal leakage. Disassemble the suspect cylinder manifold and remove the pilot-operated check valve cartridge; inspect the ground carbide valve seat under magnification for micro-cracks, erosion channels, or debris indents. Replace the valve cartridge and install new 90 Durometer backup rings.
