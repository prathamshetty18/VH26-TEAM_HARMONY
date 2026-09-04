# -*- coding: utf-8 -*-
"""
Multilingual Machine Instruction Manual Data Store

Machine: CNC Milling Machine — Model MX-7 Precision
Languages supported:
1. English (en) — Reference version
2. Simplified Chinese (zh) — 中文
3. Japanese (ja) — 日本語
4. German (de) — Deutsch

Rules:
- Technical meaning, instructions, warnings, component names, and procedures remain strictly consistent.
- Numerical values and units (e.g. 400V, 32A, 15 kW, 24,000 RPM, 94°C, 6.5 bar, 18 bar) are NEVER translated.
- Structure contains all 9 required sections.
"""

MULTILINGUAL_MANUAL = {
    "en": {
        "language_code": "en",
        "language_label": "English",
        "machine_name": "CNC Milling Machine — Model MX-7 Precision",
        "sections": {
            "overview": {
                "section_id": 1,
                "title": "1. Machine Overview",
                "machine_name": "CNC Milling Machine — Model MX-7 Precision",
                "machine_purpose": "High-precision 5-axis vertical CNC milling center engineered for tight-tolerance aerospace components, medical implants, and high-speed precision tooling production.",
                "main_components": [
                    "High-Speed Electro-Spindle (24,000 RPM)",
                    "5-Axis Digital AC Servo Drive System (X, Y, Z, A, C)",
                    "40-Station High-Speed Automatic Tool Changer (ATC)",
                    "Industrial CNC Motion Controller & Operator Console",
                    "High-Pressure Through-Spindle Coolant (TSC) Unit (70 bar)",
                    "Centralized Automated Slideway Lubrication Pump (18 bar)"
                ],
                "basic_operating_principle": "The machine synchronizes 5 closed-loop servo axes with high-speed tool rotation up to 24,000 RPM. Optical linear glass scales provide continuous position feedback to the CNC controller, allowing automated milling, drilling, and contouring operations with repeatability of +/- 0.002 mm."
            },
            "safety": {
                "section_id": 2,
                "title": "2. Safety Instructions",
                "safety_precautions": [
                    "Ensure enclosure safety interlock doors remain locked during active machining cycles.",
                    "Verify raw stock workpiece is securely clamped to the milling bed before pressing Cycle Start.",
                    "Keep hands and clothing clear of the tool magazine and spindle envelope during power-up."
                ],
                "electrical_safety": [
                    "Supply voltage is 400V AC (3-phase). Only certified electricians may open the main electrical control cabinet.",
                    "Follow strict Lockout/Tagout (LOTO) procedures at the main circuit disconnect switch prior to servicing.",
                    "Wait at least 10 minutes after disconnecting power to allow high-voltage servo bus capacitors to discharge."
                ],
                "emergency_procedures": [
                    "In any abnormal condition, immediately press any red palm Emergency Stop (E-stop) push-button.",
                    "In case of smoke, electrical burning odor, or fire, strike E-stop and switch the main 400V circuit breaker to OFF."
                ],
                "warnings": [
                    "WARNING: High Voltage (400V) inside rear electrical cabinet.",
                    "WARNING: Spindle rotates up to 24,000 RPM. Flying chips and broken cutters present severe projectile hazards.",
                    "WARNING: Automatic tool changer arm moves rapidly without warning during program execution."
                ],
                "required_protective_equipment": [
                    "Safety glasses with side shields (ANSI Z87.1 / EN 166)",
                    "Steel-toed safety boots with slip-resistant soles (EN ISO 20345)",
                    "Hearing protection for continuous cutting operations exceeding 85 dBA",
                    "Cut-resistant gloves when handling carbide tools (NEVER wear gloves near rotating spindle!)"
                ]
            },
            "components": {
                "section_id": 3,
                "title": "3. Machine Components",
                "components_list": [
                    {
                        "name": "High-Speed Electro-Spindle",
                        "function": "Directly rotates cutting tools with continuous variable speed up to 24,000 RPM.",
                        "normal_condition": "Smooth running, housing temperature below 45°C (max limit 94°C), vibration below 0.8 mm/s.",
                        "common_problems": "Bearing wear, thermal overload exceeding 94°C, dynamic unbalance, tool unclamp failure."
                    },
                    {
                        "name": "Axis Servo Drives & Linear Guideways",
                        "function": "Translates CNC coordinates into linear motion along X, Y, Z axes and rotation along A, C axes.",
                        "normal_condition": "Smooth movement without jerk, positioning repeatability +/- 0.002 mm, constant 18 bar oil film.",
                        "common_problems": "Linear glass scale contamination, ballscrew backlash, servo following error."
                    },
                    {
                        "name": "Automatic Tool Changer (ATC)",
                        "function": "Stores 40 tool holders and automatically swaps tools in the spindle within 1.8 seconds.",
                        "normal_condition": "Clean tool pot pockets, pneumatic pressure at 6.5 bar, smooth 180° arm swing.",
                        "common_problems": "Gripper claw chip jamming, tool clamp sensor failure, drop in pneumatic pressure."
                    },
                    {
                        "name": "Through-Spindle Coolant (TSC) Unit",
                        "function": "Delivers high-pressure cutting fluid directly through cutter internal channels to evacuate chips.",
                        "normal_condition": "Pressure between 45 bar and 70 bar, flow rate > 6.2 L/min, filter indicator green.",
                        "common_problems": "Clogged 25-micron filter element, coolant pump cavitation, line rupture."
                    },
                    {
                        "name": "Centralized Progressive Lubrication Pump",
                        "function": "Metered delivery of ISO VG 68 way lube oil to all linear guideways and ballscrew nuts.",
                        "normal_condition": "Pressure pulse builds to 18 bar every 20 minutes, reservoir level above minimum.",
                        "common_problems": "Low oil level, cracked 4 mm nylon delivery tube, stuck divider manifold valve."
                    }
                ]
            },
            "operating": {
                "section_id": 4,
                "title": "4. Operating Instructions",
                "steps": {
                    "starting": [
                        "Verify main electrical disconnect switch is ON (400V).",
                        "Turn CNC power key-switch to ON and allow operating system to boot completely.",
                        "Release all Emergency Stop buttons (twist clockwise).",
                        "Press the Machine Ready button on the operator console.",
                        "Execute the 'HOME REF' zero-return routine on all 5 axes (X, Y, Z, A, C).",
                        "Run the automated 15-minute spindle warm-up cycle at 4,000 RPM before heavy machining."
                    ],
                    "normal_operation": [
                        "Load verified CNC part program via USB or local network.",
                        "Inspect cutting tool condition and measure tool length/diameter offsets.",
                        "Mount raw workpiece and verify clamping hydraulic/pneumatic pressure is at 25 bar.",
                        "Set Work Coordinate System (WCS) using the optical 3D touch probe.",
                        "Verify through-spindle coolant tank is filled with 8% synthetic emulsion.",
                        "Close enclosure door and press the illuminated green 'CYCLE START' button."
                    ],
                    "monitoring": [
                        "Monitor spindle motor load meter; normal load must remain below 80%.",
                        "Confirm coolant delivery flow rate reads above 6.2 L/min during cutting.",
                        "Observe axis vibration gauges and listen for abnormal acoustic chattering.",
                        "Check spindle temperature readout on the telemetry page (ensure < 94°C)."
                    ],
                    "stopping": [
                        "Press 'FEED HOLD' button to pause axis motion at the end of a cut pass.",
                        "Enter M05 in MDI mode to bring spindle rotation to a full stop.",
                        "Turn off coolant delivery with M09.",
                        "Jog axes to part loading position and open enclosure door to inspect workpiece."
                    ],
                    "emergency_shutdown": [
                        "Strike any red palm-type Emergency Stop button immediately.",
                        "Spindle power is cut and dynamic electronic braking stops rotation within 1.5 seconds.",
                        "Axis drives immediately freeze in position to prevent tool plunge.",
                        "Turn off main 400V circuit breaker if an electrical emergency or fire is observed."
                    ]
                }
            },
            "error_fault": {
                "section_id": 5,
                "title": "5. Error and Fault Instructions",
                "items": [
                    {
                        "problem": "Motor overheating (Spindle motor reaches 94°C or above)",
                        "possible_cause": "High load cutting, poor cooling circuit ventilation, low chiller coolant, or bearing wear.",
                        "what_to_check": "Check spindle temperature on telemetry, inspect chiller fluid level at 2.5 bar, check for clogged fan filters.",
                        "recommended_action": "Stop the machine immediately and inspect the motor. Allow 15 minutes idle rotation at 500 RPM to circulate chiller fluid."
                    },
                    {
                        "problem": "Spindle excessive vibration at high RPM",
                        "possible_cause": "Tool holder dynamic unbalance, chipped carbide cutter insert, or worn ceramic bearings.",
                        "what_to_check": "Inspect tool holder balance grade (ISO 1940-1 Grade G2.5), check cutter teeth with optical loupe, measure spindle nose radial runout.",
                        "recommended_action": "Replace damaged cutter insert. Rebalance tool holder or replace worn tool assembly before exceeding 10,000 RPM."
                    },
                    {
                        "problem": "Through-spindle coolant pressure drop below 45 bar",
                        "possible_cause": "Clogged 25-micron inline filter element, low reservoir tank fluid, or air trapped in pump.",
                        "what_to_check": "Check red pop-up differential pressure indicator on filter housing, check tank level sight glass.",
                        "recommended_action": "Replace dirty filter cartridge (Part No. MX-FLT-025), top up coolant to full line, bleed pump air valve."
                    },
                    {
                        "problem": "Automatic tool changer arm failure to clamp tool",
                        "possible_cause": "Shop pneumatic supply pressure below 6.0 bar, metal chips in spindle taper, or worn pull stud.",
                        "what_to_check": "Check pneumatic supply pressure gauge (must read 6.5 bar), inspect internal spindle BT40 taper for swarf.",
                        "recommended_action": "Wipe spindle taper with conical felt wiper, adjust shop regulator to 6.5 bar, replace scored pull stud."
                    }
                ]
            },
            "maintenance": {
                "section_id": 6,
                "title": "6. Maintenance Instructions",
                "regular_inspection": [
                    "Daily: Check oil level in central lubrication tank (ISO VG 68 way lube).",
                    "Daily: Verify pneumatic supply regulator is stable at 6.5 bar.",
                    "Daily: Inspect coolant tank level and verify synthetic emulsion concentration at 8% using a refractometer."
                ],
                "cleaning": [
                    "Clean metal chips from way covers, ballscrews, and door rails after each shift.",
                    "Wipe spindle internal BT40 taper clean using dry, lint-free cloth and cleaner.",
                    "Clean electrical cabinet air filter grilles with compressed air weekly."
                ],
                "lubrication": [
                    "Keep central lubrication reservoir filled with ISO VG 68 slideway lubricant.",
                    "Apply high-speed spindle grease (Kluber NBU 15) to tool changer cam mechanism monthly.",
                    "Grease counterweight chain linkages every 500 operating hours."
                ],
                "component_inspection": [
                    "Inspect linear optical scale glass scanning windows for coolant mist or contamination.",
                    "Measure spindle mechanical axial play with dial test indicator (must be < 0.003 mm).",
                    "Check emergency stop switches and door interlocks for positive circuit break."
                ],
                "replacement_instructions": [
                    "High-pressure coolant filter: Replace 25-micron element whenever differential pressure pop-up activates.",
                    "Way cover wiper seals: Replace damaged polyurethane wiper lips annually.",
                    "Spindle chiller fluid: Flush and refill closed-loop glycol chiller mixture annually."
                ],
                "maintenance_intervals": [
                    {"interval": "Daily (8 Hours)", "task": "Check lube oil level, pneumatic pressure (6.5 bar), clean chip pan and spindle taper."},
                    {"interval": "Weekly (50 Hours)", "task": "Clean electrical cabinet filters, check coolant concentration (8%), test E-stop circuits."},
                    {"interval": "Monthly (200 Hours)", "task": "Grease tool changer gripper claws, check linear scale air purge regulator (1.5 bar)."},
                    {"interval": "Semi-Annual (1,000 Hours)", "task": "Inspect ballscrew backlash, check drawbar clamping retention force (> 10.5 kN)."},
                    {"interval": "Annual (2,000 Hours)", "task": "Flush chiller glycol loop, replace axis way cover wipers, recalibrate laser geometry."}
                ]
            },
            "troubleshooting": {
                "section_id": 7,
                "title": "7. Troubleshooting",
                "table": [
                    {
                        "error": "Motor overheating",
                        "possible_cause": "Excessive cutting load, spindle cooling circuit failure, ambient temperature > 38°C, or bearing degradation (Temp > 94°C).",
                        "solution": "Reduce feed rate, verify chiller loop pressure is 2.5 bar, clean cabinet air filters, allow motor to cool."
                    },
                    {
                        "error": "Excessive vibration",
                        "possible_cause": "Unbalanced tool holder, tool stickout ratio > 3:1, worn spindle bearings, or loose workpiece clamping.",
                        "solution": "Balance tool holder to G2.5 at 24,000 RPM, reduce overhang, verify hydraulic clamping at 25 bar."
                    },
                    {
                        "error": "Abnormal noise",
                        "possible_cause": "Dry ballscrew contact, dry gear meshing, loose protective sheet metal, or chipped tool insert.",
                        "solution": "Force manual lubrication cycle (18 bar), inspect cutter edges under optical scope, tighten way cover bolts."
                    },
                    {
                        "error": "Voltage problems",
                        "possible_cause": "Main 400V supply phase imbalance > 3%, incoming line surge, or blown phase fuse in control cabinet.",
                        "solution": "Measure 3-phase line voltages at input terminal block (380V - 420V nominal). Check incoming facility power tap."
                    },
                    {
                        "error": "Current problems",
                        "possible_cause": "Spindle motor stator overcurrent, axis mechanical jam, or defective servo drive IGBT module.",
                        "solution": "Disconnect drive output and measure winding resistance (balanced to 0.1 ohm). Clear mechanical axis obstruction."
                    },
                    {
                        "error": "Sensor failure",
                        "possible_cause": "Linear optical scale condensation, metal chips blocking proximity switch, or broken 24V sensor cable.",
                        "solution": "Clean scale glass window with isopropyl alcohol, blow clean proximity switch face, test 24V DC sensor voltage."
                    },
                    {
                        "error": "Bearing failure",
                        "possible_cause": "Loss of bearing grease, dynamic tool imbalance at 24,000 RPM, or coolant ingress into spindle cartridge.",
                        "solution": "Check spindle vibration level; if radial runout exceeds 0.005 mm TIR, replace spindle hybrid ceramic bearing pack."
                    },
                    {
                        "error": "Power failure",
                        "possible_cause": "Main supply breaker tripped, 24V DC control power supply overload, or safety relay fault.",
                        "solution": "Reset main 400V circuit breaker, check 24V DC switching power supply output LED, trace safety interlock loop."
                    },
                    {
                        "error": "Communication failure",
                        "possible_cause": "EtherCAT bus cable loose, servo amplifier node address conflict, or electromagnetic interference (EMI).",
                        "solution": "Reseat shielded RJ45 bus cables, verify shielded ground braid connection, verify drive node rotary switch addresses."
                    }
                ]
            },
            "emergency_procedures": {
                "section_id": 8,
                "title": "8. Emergency Procedures",
                "procedures": [
                    {
                        "situation": "Critical hardware failure",
                        "action": "1. Strike red palm E-stop immediately. 2. Do not attempt to move axes manually. 3. Turn OFF main electrical isolator. 4. Tag the machine with 'DO NOT OPERATE' lock and notify maintenance supervisor."
                    },
                    {
                        "situation": "Overheating (Spindle or coolant > 94°C)",
                        "action": "1. Abort cutting cycle. 2. If no smoke is present, allow spindle to idle at 500 RPM for 10 minutes to circulate chiller fluid. 3. If temperature continues climbing past 105°C, hit Emergency Stop. 4. Inspect chiller pump and fluid level."
                    },
                    {
                        "situation": "Electrical fault (Sparks, smoke, or burnt odor)",
                        "action": "1. Immediately strike E-stop button. 2. Switch main 400V disconnect handle to OFF position. 3. If fire develops, discharge a CO2 or Class C dry powder fire extinguisher. Never use water on electrical machinery!"
                    },
                    {
                        "situation": "Unexpected machine shutdown",
                        "action": "1. Do not immediately cycle power. 2. Inspect control cabinet error LEDs and record fault codes. 3. Verify main supply voltage. 4. Inspect axis way covers for mechanical binding before restarting."
                    },
                    {
                        "situation": "Emergency stop activation & reset sequence",
                        "action": "1. Ensure all personnel are clear of machine cutting area. 2. Resolve initial hazard condition. 3. Twist active E-stop button clockwise to pop it out. 4. Press blue 'ALARM RESET' button on pendant. 5. Re-reference axes (HOME REF)."
                    }
                ]
            },
            "specifications": {
                "section_id": 9,
                "title": "9. Technical Specifications",
                "specs": [
                    {"parameter": "Voltage", "value": "400V AC +/- 10% (3-Phase, 50/60 Hz)"},
                    {"parameter": "Current", "value": "32A continuous full load (45A peak inrush)"},
                    {"parameter": "Power", "value": "15 kW continuous S1 rating (22 kW S6-40%)"},
                    {"parameter": "RPM", "value": "100 - 24,000 RPM (Continuous variable speed)"},
                    {"parameter": "Temperature range", "value": "Ambient: 18°C - 25°C | Chiller: 20°C +/- 0.5°C | Max Motor Limit: 94°C (Alarm at 115°C)"},
                    {"parameter": "Pressure", "value": "Shop Air: 6.5 bar | Central Lube: 18 bar | TSC Coolant: 45 bar - 70 bar"},
                    {"parameter": "Operating conditions", "value": "Clean industrial workshop, 30% - 75% RH non-condensing, foundation vibration < 0.5 mm/s"}
                ]
            }
        }
    },

    "zh": {
        "language_code": "zh",
        "language_label": "中文",
        "machine_name": "数控铣床 — MX-7 Precision 型",
        "sections": {
            "overview": {
                "section_id": 1,
                "title": "1. 机器概述 (Machine Overview)",
                "machine_name": "数控铣床 — MX-7 Precision 型 (CNC Milling Machine — Model MX-7 Precision)",
                "machine_purpose": "高精度 5 轴立式数控铣削加工中心，专为严格公差的航空航天零部件、医疗植入物和高速精密模具制造而设计。",
                "main_components": [
                    "高速电主轴 (24,000 RPM)",
                    "5 轴全数字交流伺服驱动系统 (X, Y, Z, A, C)",
                    "40 工位高速自动换刀装置 (ATC)",
                    "工业数控运动控制器与操作操纵台",
                    "高压主轴中心出水冷却装置 (TSC) (70 bar)",
                    "集中自动导轨润滑油泵 (18 bar)"
                ],
                "basic_operating_principle": "该设备将 5 个全闭环伺服轴与高达 24,000 RPM 的高速刀具旋转同步协同。光学玻璃光栅尺向数控控制器提供连续位置反馈，实现高精度的自动化铣削、钻孔和轮廓切削，重复定位精度达 +/- 0.002 mm。"
            },
            "safety": {
                "section_id": 2,
                "title": "2. 安全守则 (Safety Instructions)",
                "safety_precautions": [
                    "在加工循环运行期间，必须确保防护门安全联锁装置保持锁紧状态。",
                    "在按下循环启动 (Cycle Start) 前，确认工件已牢固装夹在铣削工作台上。",
                    "开机上电期间，严禁双手和衣物靠近刀库和主轴工作区域。"
                ],
                "electrical_safety": [
                    "主电源供电电压为 400V AC (三相)。仅具备资质的电气专业人员方可打开电气主控制柜。",
                    "在维护检修前，必须在主电源隔离开关处严格执行上锁挂牌 (LOTO) 安全程序。",
                    "切断主电源后，至少等待 10 分钟，以使高压伺服母线电容器完全放电完毕。"
                ],
                "emergency_procedures": [
                    "一旦发生任何异常情况，立即拍下任意红色蘑菇头急停按钮 (E-stop)。",
                    "如发现冒烟、电气焦味或火情，立即拍下急停按钮并将 400V 主断路器切换至 OFF 关断位置。"
                ],
                "warnings": [
                    "警告：后部电气柜内存在高压危险 (400V)。",
                    "警告：主轴旋转速度高达 24,000 RPM。飞溅碎屑与断刀具有严重机械投射物危险。",
                    "警告：自动换刀机械臂在程序运行中可能会高速动作，严防挤压伤人。"
                ],
                "required_protective_equipment": [
                    "带侧翼防护的安全护目镜 (ANSI Z87.1 / EN 166)",
                    "带防滑鞋底的钢头劳保防护鞋 (EN ISO 20345)",
                    "连续切削作业噪声超过 85 dBA 时的防噪声耳塞/耳罩",
                    "拿取硬质合金刀具时的防割手套 (主轴旋转时绝对禁止佩戴手套！)"
                ]
            },
            "components": {
                "section_id": 3,
                "title": "3. 机器主要部件 (Machine Components)",
                "components_list": [
                    {
                        "name": "高速电主轴 (High-Speed Electro-Spindle)",
                        "function": "直接驱动铣削刀具高速旋转，连续无级调速最高可达 24,000 RPM。",
                        "normal_condition": "运转平稳无杂音，轴承座外壳温度低于 45°C (最高安全阈值 94°C)，振动速度低于 0.8 mm/s。",
                        "common_problems": "轴承磨损、热过载温度超过 94°C、动态不平衡、刀具松卡故障。"
                    },
                    {
                        "name": "进给轴伺服系统与直线导轨 (X, Y, Z, A, C)",
                        "function": "将数控指令转换为 X, Y, Z 直线运动以及 A, C 轴高精度旋转运动。",
                        "normal_condition": "进给动作顺滑无顿挫，重复定位精度 +/- 0.002 mm，导轨表面维持恒定 18 bar 润滑油膜。",
                        "common_problems": "光学光栅尺油污污染、滚珠丝杠反向间隙超标、伺服跟随误差过大。"
                    },
                    {
                        "name": "自动换刀装置 (ATC)",
                        "function": "容纳 40 把刀柄并在 1.8 秒内完成主轴与刀库之间的自动刀具交换。",
                        "normal_condition": "刀套清洁无铁屑，气动压力维持在 6.5 bar，机械臂 180° 平稳旋转换刀。",
                        "common_problems": "机械手夹爪铁屑卡死、拉钉夹紧传感器失灵、气源压力骤降。"
                    },
                    {
                        "name": "主轴内冷高压冲屑系统 (TSC)",
                        "function": "通过刀具内部冷却通道喷射高压切削液，实现快速排屑与刀尖散热降温。",
                        "normal_condition": "系统压力稳定在 45 bar 至 70 bar 之间，流量 > 6.2 L/min，滤芯压差指示器显示绿色正常。",
                        "common_problems": "25-micron 滤芯堵塞、高压泵吸空汽蚀、高压软管破损泄漏。"
                    },
                    {
                        "name": "集中递进式润滑泵 (Lubrication Pump)",
                        "function": "定时定量向所有直线导轨滑块和滚珠丝杠螺母泵送 ISO VG 68 导轨油。",
                        "normal_condition": "每隔 20 分钟压力脉冲建立至 18 bar，储油箱油位始终高于下限警戒线。",
                        "common_problems": "润滑油位过低、4 mm 尼龙供油管破裂、分流分配阀阀芯卡滞。"
                    }
                ]
            },
            "operating": {
                "section_id": 4,
                "title": "4. 操作规程 (Operating Instructions)",
                "steps": {
                    "starting": [
                        "确认车间主供电电源开关已合闸开启 (400V)。",
                        "将数控系统钥匙开关旋转至 ON 位置，等待数控操作系统完全引导启动。",
                        "顺时针旋转释放控制面板上的急停按钮 (E-stop)。",
                        "按下操作操纵台上的系统就绪按钮 (Machine Ready)。",
                        "执行各轴回参考点零位程序 (HOME REF)，依次校准 X, Y, Z, A, C 五个轴。",
                        "在进行重切削前，先以 4,000 RPM 自动运转 15 分钟完成主轴预热程序。"
                    ],
                    "normal_operation": [
                        "通过 U 盘或车间以太网调入经过检验确认的加工 G 代码程序。",
                        "检查切削刀具状态，并在机测量校对刀具长度和半径补偿值。",
                        "安装毛坯工件，并确认液压/气动夹具夹紧压力达到 25 bar。",
                        "使用光学 3D 工件寻边器测定并设定工件坐标系 (WCS)。",
                        "确认切削液水箱内已注入浓度为 8% 的水溶性全合成切削乳化液。",
                        "关闭安全防护门，按下亮起的绿色循环启动按键 (CYCLE START)。"
                    ],
                    "monitoring": [
                        "实时监控数控屏幕上的主轴负载表；正常负载应保持在 80% 以下。",
                        "确认切削加工过程中内冷流量计读数稳定保持在 6.2 L/min 以上。",
                        "注意观察各轴振动仪表读数，留心监听切削区域是否有异常尖叫与颤振杂音。",
                        "关注遥测屏幕上的主轴温度读数 (严密监控必须 < 94°C)。"
                    ],
                    "stopping": [
                        "在切削行程终点按下进给保持 (FEED HOLD) 按钮暂停轴运动。",
                        "在 MDI 模式下输入指令 M05 使主轴完全平稳停止旋转。",
                        "输入指令 M09 关闭切削液泵。",
                        "将各轴移动至安全装卸料位置，打开防护门检查已加工零件。"
                    ],
                    "emergency_shutdown": [
                        "一旦出现危急突发情况，立即拍击任意红色急停按钮 (Emergency Stop)。",
                        "主轴伺服立即切断动力，并通过电子动能制动在 1.5 秒内完全停止旋转。",
                        "各轴进给驱动瞬间断电抱闸自锁，防止刀具撞击工件。",
                        "如果观察到电气打火冒烟或火险，立即切断车间 400V 主断路器。"
                    ]
                }
            },
            "error_fault": {
                "section_id": 5,
                "title": "5. 故障与错误处置指南 (Error and Fault Instructions)",
                "items": [
                    {
                        "problem": "电机温度过高 (主轴电机温度达到 94°C 或以上)",
                        "possible_cause": "高负荷过载切削、制冷循环回路通风不良、油冷机冷媒不足或轴承磨损故障。",
                        "what_to_check": "在遥测界面检查主轴温度读数，检查油冷机压力表是否在 2.5 bar，检查电柜散热风扇滤网是否积尘受阻。",
                        "recommended_action": "立即停机并对电机进行检查。可保持主轴在 500 RPM 空载运转 15 分钟，利用冷却液循环散热。"
                    },
                    {
                        "problem": "高速运转下主轴异常剧烈振动",
                        "possible_cause": "刀柄动态动平衡失准、硬质合金刀片碎裂缺口、主轴混合陶瓷轴承磨损松动。",
                        "what_to_check": "检验刀柄动平衡等级 (ISO 1940-1 G2.5 级)，使用放大镜检查刀刃完整性，打表测量主轴端部径向跳动。",
                        "recommended_action": "更换损坏的切削刀片。重新进行动平衡校验，未纠正平衡前禁止转速超过 10,000 RPM。"
                    },
                    {
                        "problem": "主轴内冷压力骤降低于 45 bar",
                        "possible_cause": "25-micron 管路滤芯严重堵塞、切削液水箱液位过低、高压泵腔混入空气。",
                        "what_to_check": "检查滤清器壳体上的红色压差弹跳指示器是否冒起，观察水箱液位计刻度。",
                        "recommended_action": "更换被污染的滤芯滤纸 (配件号 MX-FLT-025)，补充切削液至上限标线，拧开高压泵排气阀排净空气。"
                    },
                    {
                        "problem": "自动换刀机械手无法夹紧刀具",
                        "possible_cause": "车间主气源压力不足低于 6.0 bar、主轴内锥孔积聚金属碎屑、刀柄拉钉磨损变形。",
                        "what_to_check": "查看气源调节阀压力表 (必须稳定在 6.5 bar)，检查主轴内部 BT40 锥孔内壁是否有划伤积屑。",
                        "recommended_action": "使用圆锥形羊毛擦拭棒彻底清洁主轴内孔，将气压阀调整至 6.5 bar，更换磨损变形的拉钉。"
                    }
                ]
            },
            "maintenance": {
                "section_id": 6,
                "title": "6. 维护保养规范 (Maintenance Instructions)",
                "regular_inspection": [
                    "每日例行：检查集中导轨润滑油箱油位 (ISO VG 68 导轨油)。",
                    "每日例行：核实主供气调压阀压力稳定保持在 6.5 bar。",
                    "每日例行：检查切削液水箱油位，并使用折光仪测定全合成切削乳化液浓度保持在 8%。"
                ],
                "cleaning": [
                    "每班次作业结束后，必须彻底清理各轴防护罩伸缩盖、滚珠丝杠及舱门导轨上的金属切屑。",
                    "使用不起毛的干净抹布和专用清洗剂擦净主轴 BT40 锥孔内部。",
                    "每周使用压缩空气吹扫清理一次电气柜进风口防尘过滤棉。"
                ],
                "lubrication": [
                    "集中润滑油箱必须始终注入经过过滤的 ISO VG 68 导轨专用润滑油。",
                    "每月使用专用油脂枪对自动换刀机械凸轮机构加注高速润滑脂 (Kluber NBU 15)。",
                    "每累计运行 500 小时，对立柱配重链条及传动销轴涂抹防锈润滑油脂。"
                ],
                "component_inspection": [
                    "仔细检查直线光栅尺防尘密封唇和光学玻璃扫描窗口，排除切削油雾污染。",
                    "使用百分表测量主轴机械轴向游隙 (正常标准必须 < 0.003 mm)。",
                    "测试全机急停按钮及安全门互锁触点，确保常闭安全回路动作灵敏可靠。"
                ],
                "replacement_instructions": [
                    "高压内冷滤芯：一旦压差发讯器冒出红指示销，必须立即更换 25-micron 褶叠滤芯。",
                    "导轨防护罩刮屑板：每年检查并更换受损开裂的聚氨酯橡胶刮屑条。",
                    "主轴冷油机循环液：每年对全闭环乙二醇冷却水箱进行彻底清洗并重新注满。"
                ],
                "maintenance_intervals": [
                    {"interval": "每日 (8 Hours)", "task": "检查导轨润滑油位、气源供气压力 (6.5 bar)、清理主轴内孔与底盘排屑槽。"},
                    {"interval": "每周 (50 Hours)", "task": "吹扫电气柜滤网、用折光仪检测切削液浓度 (8%)、测试急停安全回路开关。"},
                    {"interval": "每月 (200 Hours)", "task": "润滑换刀机械手夹爪轴套、检查光栅尺空气气帘吹气减压阀压力 (1.5 bar)。"},
                    {"interval": "每半年 (1,000 Hours)", "task": "检查丝杠反向间隙、使用拉力计测定主轴刀柄四瓣爪拉紧拉力 (> 10.5 kN)。"},
                    {"interval": "每年 (2,000 Hours)", "task": "清洗冷油机乙二醇回路、更换各轴护罩刮屑橡胶条、利用激光干涉仪校准空间几何精度。"}
                ]
            },
            "troubleshooting": {
                "section_id": 7,
                "title": "7. 常见故障排查表 (Troubleshooting Table)",
                "table": [
                    {
                        "error": "电机过热 (Motor overheating)",
                        "possible_cause": "铣削负载过大、主轴冷却循环管路故障、环境温度 > 38°C 或轴承磨损退化 (温度 > 94°C)。",
                        "solution": "减小进给量与切深，核实冷水机管路压力稳定在 2.5 bar，清扫电柜进风滤网，让电机自然散热冷却。"
                    },
                    {
                        "error": "过度振动 (Excessive vibration)",
                        "possible_cause": "刀柄动平衡超差、刀具悬伸长径比 > 3:1、主轴轴承磨损松动、工件夹紧刚性不足。",
                        "solution": "在 24,000 RPM 条件下校正动平衡至 G2.5 等级，缩短悬伸长度，确认液压夹持压力达到 25 bar。"
                    },
                    {
                        "error": "异常噪音 (Abnormal noise)",
                        "possible_cause": "滚珠丝杠缺油干摩擦、齿轮啮合干涩、防护罩钣金松动共振、铣刀刀片崩刃碎裂。",
                        "solution": "手动强制执行一次导轨注油循环 (18 bar)，用放大镜检查刀刃完整性，紧固护罩连接螺栓。"
                    },
                    {
                        "error": "电压异常 (Voltage problems)",
                        "possible_cause": "车间三相 400V 供电不平衡度 > 3%、电网浪涌电压冲击、电气柜进线熔断器烧损断路。",
                        "solution": "用万用表测量输入接线端子排三相线电压 (标称值 380V - 420V)。协调调整车间变压器抽头分接头。"
                    },
                    {
                        "error": "电流异常 (Current problems)",
                        "possible_cause": "主轴电机定子过流、机械进给轴卡滞干涉、伺服驱动器 IGBT 逆变功率模块击穿损坏。",
                        "solution": "拆开电机动力线测试定子绕组阻值 (三相平衡误差 < 0.1 ohm)。排查排除导轨滚珠丝杠机械卡阻。"
                    },
                    {
                        "error": "传感器故障 (Sensor failure)",
                        "possible_cause": "玻璃光栅尺冷凝油雾附着、金属碎屑遮挡接近开关感应面、24V 传感器线缆折断。",
                        "solution": "使用无水异丙醇擦拭清洁光栅玻璃尺面，用气枪吹除接近开关金属粉末，用表测量 24V DC 供电。"
                    },
                    {
                        "error": "轴承故障 (Bearing failure)",
                        "possible_cause": "高速特种油脂流失硬化、24,000 RPM 动态离心偏载破坏、切削液水汽渗入主轴内部轴承室。",
                        "solution": "检测主轴轴向跳动与振动加速度；若端面径向跳动超过 0.005 mm TIR，必须拆装更换混合陶瓷轴承组件。"
                    },
                    {
                        "error": "电源故障 (Power failure)",
                        "possible_cause": "进线总空气开关过载跳闸、24V DC 开关稳压电源短路保护、主安全继电器回路失电跳开。",
                        "solution": "复位 400V 塑壳断路器开关，检查 24V DC 直流电源指示灯绿色亮起状态，按图纸排查急停安全联锁回路。"
                    },
                    {
                        "error": "通信故障 (Communication failure)",
                        "possible_cause": "EtherCAT 工业总线屏蔽双绞线插头松脱、伺服驱动器硬件站号拨码冲突、高频强电磁干扰 (EMI)。",
                        "solution": "重新插紧带金属屏蔽层的 RJ45 网线，检查接地屏蔽网铜带接地连线，复核伺服驱动单元站地址拨码设置。"
                    }
                ]
            },
            "emergency_procedures": {
                "section_id": 8,
                "title": "8. 应急处置程序 (Emergency Procedures)",
                "procedures": [
                    {
                        "situation": "严重机械硬件损坏事故 (Critical hardware failure)",
                        "action": "1. 立即拍下红色蘑菇头急停按钮。2. 绝对不可尝试手动摇动手轮或点动坐标轴。3. 切断车间主电源隔离开关。4. 在机床操作屏上挂牌'设备故障，禁止合闸'，并立即通知车间主管。"
                    },
                    {
                        "situation": "过热警报 (主轴或冷却液 > 94°C)",
                        "action": "1. 立即按下进给保持终止当前切削循环。2. 若无明火烟雾，让主轴在 500 RPM 怠速转动 10 分钟以维持循环散热。3. 如温度持续攀升超过 105°C，立即按急停并断电。4. 检查冷水机循环泵及冷媒储量。"
                    },
                    {
                        "situation": "电气火险与异常短路 (Electrical fault / Smoke / Fire)",
                        "action": "1. 立即拍下任意急停按钮。2. 迅速将控制柜 400V 主切断手柄拉向 OFF 关断断开位。3. 如出现火情，使用二氧化碳 (CO2) 或干粉专用电气灭火器喷射灭火。严禁使用水灭火！"
                    },
                    {
                        "situation": "意外突然停机 (Unexpected machine shutdown)",
                        "action": "1. 严禁盲目尝试重新合闸上电。2. 查看电气柜及伺服单元状态指示灯，记录当前错误报警代码。3. 测量主供电进线三相电压。4. 重启前仔细检查导轨防护罩是否遭受机械卡死卡阻。"
                    },
                    {
                        "situation": "急停按钮动作后的复位规程 (Emergency stop reset sequence)",
                        "action": "1. 确认所有作业人员完全撤离机床运动及切削包络危险区。2. 确认引发急停的原始隐患已彻底排除。3. 顺时针旋转受力按下的急停按钮使其弹出复位。4. 按下操作面板上的蓝色报警复位键 (ALARM RESET)。5. 重新进行各轴回零校准 (HOME REF)。"
                    }
                ]
            },
            "specifications": {
                "section_id": 9,
                "title": "9. 技术规格参数 (Technical Specifications)",
                "specs": [
                    {"parameter": "电压 (Voltage)", "value": "400V AC +/- 10% (3-Phase, 50/60 Hz)"},
                    {"parameter": "电流 (Current)", "value": "32A continuous full load (45A peak inrush)"},
                    {"parameter": "功率 (Power)", "value": "15 kW continuous S1 rating (22 kW S6-40%)"},
                    {"parameter": "转速 (RPM)", "value": "100 - 24,000 RPM (Continuous variable speed)"},
                    {"parameter": "温度范围 (Temperature range)", "value": "Ambient: 18°C - 25°C | Chiller: 20°C +/- 0.5°C | Max Motor Limit: 94°C (Alarm at 115°C)"},
                    {"parameter": "压力 (Pressure)", "value": "Shop Air: 6.5 bar | Central Lube: 18 bar | TSC Coolant: 45 bar - 70 bar"},
                    {"parameter": "工作环境条件 (Operating conditions)", "value": "Clean industrial workshop, 30% - 75% RH non-condensing, foundation vibration < 0.5 mm/s"}
                ]
            }
        }
    },

    "ja": {
        "language_code": "ja",
        "language_label": "日本語",
        "machine_name": "CNCフライス盤 — MX-7 Precision 型",
        "sections": {
            "overview": {
                "section_id": 1,
                "title": "1. 機械概要 (Machine Overview)",
                "machine_name": "CNCフライス盤 — MX-7 Precision 型 (CNC Milling Machine — Model MX-7 Precision)",
                "machine_purpose": "高精度な航空宇宙部品、医療用インプラント、および高速金型製造用に設計された高精度5軸立形マシニングセンタです。",
                "main_components": [
                    "高速ビルトイン電磁スピンドル (24,000 RPM)",
                    "5軸フルデジタルACサーボ駆動機構 (X, Y, Z, A, C)",
                    "40本収納高速自動工具交換装置 (ATC)",
                    "産業用CNCモーションコントローラ＆操作ペンダント",
                    "高圧センタースルー主軸冷却装置 (TSC) (70 bar)",
                    "自動集中スライドウェイ給油ポンプ (18 bar)"
                ],
                "basic_operating_principle": "本機は完全密閉ループサーボ5軸と最大 24,000 RPM の高速工具回転を完全に同期させます。光学ガラス製リニアスケールがCNC制御装置に高精度な位置フィードバックを常時提供し、繰り返し精度 +/- 0.002 mm の高精度フライス加工を実現します。"
            },
            "safety": {
                "section_id": 2,
                "title": "2. 安全注意事項 (Safety Instructions)",
                "safety_precautions": [
                    "自動切削サイクル運転中は、スプラッシュガード安全インターロックドアが確実に施錠されていることを確認してください。",
                    "「サイクルスタート (Cycle Start)」を押す前に、ワークがテーブルに確実に固定クランプされていることを確認してください。",
                    "電源投入中および起動時は、ツールマガジンおよび主軸動作範囲に手や衣服を絶対に近づけないでください。"
                ],
                "electrical_safety": [
                    "主電源受電電圧は 400V AC (三相) です。資格を有する専門電気技術者以外は電気制御盤を開けてはなりません。",
                    "保守点検を行う前に、主ブレーカースイッチにおいてロックアウト／タグアウト (LOTO) 安全手順を厳格に実施してください。",
                    "電源遮断後、高電圧サーボ平滑コンデンサが完全に放電するまで、最低 10 分間 待機してください。"
                ],
                "emergency_procedures": [
                    "異常が発生した場合は、直ちに赤色キノコ型非常停止ボタン (E-stop) を強く押し込んでください。",
                    "発煙、異臭、火災が発生した場合は、直ちに非常停止ボタンを押し、400V 主電源遮断器を OFF にしてください。"
                ],
                "warnings": [
                    "警告：背面制御盤内には高電圧 (400V) が印加されています。",
                    "警告：主軸は最大 24,000 RPM で回転します。飛散する切粉や破損刃物は重大な危険物となります。",
                    "警告：自動工具交換アームはプログラム動作中に予告なく高速回転するため挟まれに厳重注意してください。"
                ],
                "required_protective_equipment": [
                    "サイドシールド付保護メガネ (ANSI Z87.1 / EN 166)",
                    "耐滑鋼先芯入安全靴 (EN ISO 20345)",
                    "85 dBA を超える切削騒音環境における防音イヤーマフ／耳栓",
                    "超硬刃物取扱時の耐切創手袋 (※主軸回転中は手袋の着用を厳禁とします！)"
                ]
            },
            "components": {
                "section_id": 3,
                "title": "3. 主要構成機器 (Machine Components)",
                "components_list": [
                    {
                        "name": "高速ビルトインスピンドル (High-Speed Electro-Spindle)",
                        "function": "切削工具を直接回転駆動し、最大 24,000 RPM まで無段階変速制御します。",
                        "normal_condition": "異音なく回転、ハウジング温度 45°C 以下 (限界安全閾値 94°C)、振動速度 0.8 mm/s 未満。",
                        "common_problems": "ベアリングの摩耗、94°C 超過の熱過負荷、回転動不釣合い、工具アンクランプ不良。"
                    },
                    {
                        "name": "各軸サーボ駆動装置＆直動ガイド (X, Y, Z, A, C)",
                        "function": "CNC位置指令をX、Y、Z直線移動およびA、C軸高精度回転運動に変換します。",
                        "normal_condition": "引っ掛かりのない滑らかな動作、繰り返し位置決め精度 +/- 0.002 mm、常時 18 bar の油膜保持。",
                        "common_problems": "光学リニアスケールの油煙汚れ、ボールねじバックラッシ過大、サーボ追従偏差エラー。"
                    },
                    {
                        "name": "自動工具交換装置 (ATC)",
                        "function": "40本のツールホルダを格納し、主軸とマガジン間で 1.8 秒 で自動交換を実行します。",
                        "normal_condition": "ツールポット内が清掃され切粉付着なし、空圧源 6.5 bar、交換アームが180°滑らかに旋回。",
                        "common_problems": "グリッパークローへの切粉噛み込み、プルスタッドクランプセンサ誤動作、空圧供給圧低下。"
                    },
                    {
                        "name": "センタースルー高圧クーラント装置 (TSC)",
                        "function": "工具先端内部貫通孔から高圧切削油を噴射し、深穴加工時の切粉排出と刃先冷却を行います。",
                        "normal_condition": "吐出圧力 45 bar 〜 70 bar 安定、流量 > 6.2 L/min、フィルタ差圧インジケータ緑色。",
                        "common_problems": "25-micron フィルタエレメント目詰まり、ポンプキャビテーション、高圧ホース亀裂破損。"
                    },
                    {
                        "name": "集中プログレッシブ自動給油ポンプ (Lubrication Pump)",
                        "function": "すべての直動ガイドブロックおよびボールねじナットへ計量された ISO VG 68 潤滑油を圧送します。",
                        "normal_condition": "20分毎に圧力パルスが 18 bar まで到達、オイルタンク残量が下限ライン以上を保持。",
                        "common_problems": "潤滑油切れ、4 mm ナイロン分配配管の亀裂破断、分配弁スプール固着スティック。"
                    }
                ]
            },
            "operating": {
                "section_id": 4,
                "title": "4. 運転操作手順 (Operating Instructions)",
                "steps": {
                    "starting": [
                        "工場の主配電盤スイッチが投入 (ON) されていることを確認します (400V)。",
                        "CNCキースイッチを ON に回し、システムOSが正常に起動完了するまで待機します。",
                        "非常停止ボタン (E-stop) を右に回して解除します。",
                        "操作パネルの「マシンレディ (Machine Ready)」ボタンを押します。",
                        "5軸すべて (X, Y, Z, A, C) の原点復帰動作 (HOME REF) を実施します。",
                        "本格加工開始前に、主軸を 4,000 RPM で 15 分間 自動暖機運転させます。"
                    ],
                    "normal_operation": [
                        "USBまたは有線LANネットワークから検証済み加工プログラムを読み込みます。",
                        "工具刃先の摩耗を点検し、ツールプリセッタにて工具長・径補正値を測定設定します。",
                        "加工ワークをセットし、油圧/空圧治具のクランプ圧力が 25 bar であることを確認します。",
                        "光学式タッチプローブを使用しワーク座標系 (WCS) の原点を設定します。",
                        "クーラントタンクに 8% 濃度の水溶性シンセティッククーラント液が満たされていることを確認します。",
                        "前面安全ドアを完全に閉じ、点灯した緑色の「サイクルスタート (CYCLE START)」を押します。"
                    ],
                    "monitoring": [
                        "主軸モータ負荷メータを監視し、実効負荷率が常時 80% 以下であることを確認します。",
                        "切削中、センタースルークーラントの流量計が 6.2 L/min 以上を示していることを確認します。",
                        "各軸の振動監視モニタを注視し、加工中のチャタリング振動や異常高周波音を警戒します。",
                        "主軸温度テレメトリ表示を確認し、温度が 94°C 未満であることを厳重に監視します。"
                    ],
                    "stopping": [
                        "切削パス終了時に「フィードホールド (FEED HOLD)」を押して送り軸を一時停止します。",
                        "MDIモードにて M05 を入力し、主軸回転を完全に停止させます。",
                        "M09 を入力してクーラント吐出ポンプを停止します。",
                        "各軸を安全なワーク脱着位置へジョグ送りし、ドアを開けて加工面を検査します。"
                    ],
                    "emergency_shutdown": [
                        "重大な異常を発見した場合は、直ちに赤色非常停止ボタン (Emergency Stop) を強打します。",
                        "主軸への動力供給が遮断され、回生制動ブレーキにより 1.5 秒 以内に急速完全停止します。",
                        "送り軸モータは即座に励磁保持され、工具の落下や食い込みを防止します。",
                        "火災や電気スパークが発生した場合は、直ちに工場主電源 400V ブレーカーを切断します。"
                    ]
                }
            },
            "error_fault": {
                "section_id": 5,
                "title": "5. エラーおよび障害対応指針 (Error and Fault Instructions)",
                "items": [
                    {
                        "problem": "モーター過熱 (主軸モーター温度が 94°C 以上に達した場合)",
                        "possible_cause": "過負荷切削重切削、チラー冷却配管の通気不良、冷却オイル不足、またはベアリング摩耗。",
                        "what_to_check": "テレメトリ画面で主軸温度を確認し、チラー圧力計が 2.5 bar であるか、電装盤吸気フィルタの目詰まりを点検。",
                        "recommended_action": "機械を直ちに停止し、モーターを点検してください。500 RPM で 15 分間 アイドリング運転し、冷却循環を促します。"
                    },
                    {
                        "problem": "高回転時における主軸の過大振動",
                        "possible_cause": "ツールホルダの動的不釣合い、超硬チップ刃先の欠け割れ、セラミックベアリングの損傷ガタ。",
                        "what_to_check": "ホルダのバランス等級 (ISO 1940-1 G2.5) を点検し、ルーペで刃先欠損を観察、主軸端部の振れをダイヤルゲージで測定。",
                        "recommended_action": "損傷したインサートチップを交換してください。ホルダのダイナミックバランスを再調整し、10,000 RPM を超える運転を禁止します。"
                    },
                    {
                        "problem": "主軸スルークーラント吐出圧力が 45 bar 未満へ低下",
                        "possible_cause": "25-micron フィルタエレメントの重度詰まり、クーラントタンク液面不足、高圧ポンプ内エア噛み込み。",
                        "what_to_check": "フィルタハウジング上の赤色差圧ポップアップ表示を確認し、タンク液面計の液位を点検。",
                        "recommended_action": "汚損したフィルタカートリッジ (部品番号 MX-FLT-025) を交換し、クーラント液を上限まで補充、ポンプエア抜き弁を開放します。"
                    },
                    {
                        "problem": "自動工具交換アームが工具を把持できない",
                        "possible_cause": "工場供給エア圧が 6.0 bar 未満に低下、主軸テーパ内への切粉付着、プルスタッドの偏摩耗。",
                        "what_to_check": "空圧調整ユニットの圧力計 (6.5 bar 必須) を確認し、主軸内部 BT40 テーパ面を目視検査。",
                        "recommended_action": "専用円錐フェルトワイパーで主軸内面を丁寧に拭き清掃し、空圧バルブを 6.5 bar に調整、傷んだプルスタッドを新品交換します。"
                    }
                ]
            },
            "maintenance": {
                "section_id": 6,
                "title": "6. 保守・点検マニュアル (Maintenance Instructions)",
                "regular_inspection": [
                    "毎日：集中ガイド潤滑油タンク (ISO VG 68) のオイル残量を点検。",
                    "毎日：工場の主空圧レギュレータ供給圧が 6.5 bar で安定していることを確認。",
                    "毎日：切削油タンクの液位を確認し、糖度計/屈折計にてエマルション濃度が 8% であることを測定確認。"
                ],
                "cleaning": [
                    "毎シフト終了後、テレスコピックワイパーカバー、ボールねじ、ドアレール上の切粉を完全に清掃。",
                    "毛羽立たない清潔なウエスと専用洗浄剤で主軸内部の BT40 テーパ内径を拭き上げ清掃。",
                    "週に一度、電気制御盤の吸気フィルタネットを圧縮空気で清掃。"
                ],
                "lubrication": [
                    "自動給油タンクには必ずゴミ混入のない認定 ISO VG 68 摺動面専用油を補給。",
                    "月に一度、ツールチェンジャーのカム機構部に高速スピンドル用グリース (Kluber NBU 15) を給脂。",
                    "稼働積算 500 時間 ごとに、カウンターウェイト駆動チェーンリンク部へ給脂。"
                ],
                "component_inspection": [
                    "光学リニアスケールの保護エア圧およびガラススケール読取り窓の油煙付着を点検。",
                    "ダイヤルテストインジケータを用い主軸の軸方向アキシャルガタを測定 (規定値 < 0.003 mm)。",
                    "全非常停止スイッチおよび安全ドアリミットスイッチの接点遮断動作を定期テスト。"
                ],
                "replacement_instructions": [
                    "高圧クーラントフィルタ：差圧インジケータの赤ピンが飛び出した際は 25-micron エレメントを即交換。",
                    "テレスコカバーワイパーシール：年次点検時に亀裂や摩耗が認められるポリウレタン製リップゴムを交換。",
                    "スピンドルチラー冷媒：密閉ループ内の不凍液グリコール冷却水を年1回全量フラッシング交換。"
                ],
                "maintenance_intervals": [
                    {"interval": "毎日 (8 Hours)", "task": "潤滑油残量確認、供給空圧 (6.5 bar) 確認、切粉清掃、主軸テーパ内面拭き取り。"},
                    {"interval": "毎週 (50 Hours)", "task": "電装盤エアフィルタ清掃、切削液濃度 (8%) 測定、非常停止遮断回路テスト。"},
                    {"interval": "毎月 (200 Hours)", "task": "ATCグリッパークロー軸受給脂、スケール用エアパージ圧力 (1.5 bar) 確認。"},
                    {"interval": "半年毎 (1,000 Hours)", "task": "ボールねじバックラッシ測定、クランププルスタッド保持力測定 (> 10.5 kN)。"},
                    {"interval": "年次 (2,000 Hours)", "task": "チラーグリコール冷却液交換、各軸カバーワイパー交換、レーザー測長器による幾何公差校正。"}
                ]
            },
            "troubleshooting": {
                "section_id": 7,
                "title": "7. トラブルシューティング表 (Troubleshooting Table)",
                "table": [
                    {
                        "error": "モーター過熱 (Motor overheating)",
                        "possible_cause": "過酷な切削負荷、主軸チラー冷却回路の循環不良、周囲温度 > 38°C、またはベアリング劣化 (温度 > 94°C)。",
                        "solution": "送り速度を低減し、チラー配管圧力が 2.5 bar であることを確認し、盤フィルタを清掃し、モーターを冷却します。"
                    },
                    {
                        "error": "過大振動 (Excessive vibration)",
                        "possible_cause": "ツールホルダのバランス不良、工具突き出し比 > 3:1、スピンドルベアリング摩耗、治具固定剛性不足。",
                        "solution": "24,000 RPM にてホルダバランスを G2.5 に調整し、突き出しを短縮、油圧クランプ圧 25 bar を確認します。"
                    },
                    {
                        "error": "異音・異常音 (Abnormal noise)",
                        "possible_cause": "ボールねじの潤滑油切れ、ギヤ噛み合い乾燥摩擦、カバー板金ネジ緩み共振、刃先チップの欠け。",
                        "solution": "手動強制潤滑 (18 bar) を実施し、ルーペで刃先チップ欠けを確認、カバー固定ボルトを増し締めします。"
                    },
                    {
                        "error": "電圧異常 (Voltage problems)",
                        "possible_cause": "三相 400V 受電電圧の不平衡率 > 3%、工場電源サージ、または盤内受電ヒューズ溶断。",
                        "solution": "主端子台にて三相各間線間電圧 (公称値 380V - 420V) をテスター測定します。受電トランスのタップを調整します。"
                    },
                    {
                        "error": "電流異常 (Current problems)",
                        "possible_cause": "主軸モーターステータ過電流、送り軸の機械的噛み込みロック、サーボアンプIGBTモジュールの内部破壊短絡。",
                        "solution": "モータ動力を切り離し巻線抵抗 (三相平衡度 0.1 ohm) を測定します。軸ガイドの機械的噛み込みを除去します。"
                    },
                    {
                        "error": "センサー故障 (Sensor failure)",
                        "possible_cause": "光学リニアスケールの結露油煙付着、近接スイッチ表面への切粉堆積、24V センサ信号線の断線。",
                        "solution": "イソプロピルアルコールでスケールガラスを清掃し、近接スイッチの切粉を除去、24V DC 供給電圧を確認します。"
                    },
                    {
                        "error": "ベアリング故障 (Bearing failure)",
                        "possible_cause": "高速ベアリンググリースの枯渇、24,000 RPM 時の動的アンバランス遠心力破損、クーラント液の軸受浸入。",
                        "solution": "主軸の振動速度を測定します。端面の全振れが 0.005 mm TIR を超える場合は、セラミック複合軸受を新品交換します。"
                    },
                    {
                        "error": "電源停止・遮断 (Power failure)",
                        "possible_cause": "主配線用遮断器のトリップ、24V DC 制御電源ユニットの過負荷保護、セーフティリレー遮断。",
                        "solution": "主 400V ブレーカーを再投入し、24V DC 直流電源の緑LED点灯を確認、安全インターロックループの導通を点検します。"
                    },
                    {
                        "error": "通信エラー (Communication failure)",
                        "possible_cause": "EtherCAT 産業用フィールドバスLANケーブル緩み、サーボアンプ局番アドレスの重複、高周波電磁ノイズ (EMI)。",
                        "solution": "シールド付RJ45通信ケーブルを再接続し、シールド接地編組アース線を確認、アンプのロータリースイッチ局番を再確認します。"
                    }
                ]
            },
            "emergency_procedures": {
                "section_id": 8,
                "title": "8. 緊急事態対応手順 (Emergency Procedures)",
                "procedures": [
                    {
                        "situation": "重大な機械ハードウェア破損 (Critical hardware failure)",
                        "action": "1. 直ちに赤色キノコ型非常停止ボタンを押下します。2. 手動ハンドルで各軸を動かそうとしないでください。3. 主電源断路スイッチを OFF にします。4. 「故障・運転禁止」の札を掲示し、直ちに保全責任者へ連絡します。"
                    },
                    {
                        "situation": "過熱アラーム (主軸または冷却液 > 94°C)",
                        "action": "1. 即座に切削サイクルを中断します。2. 白煙等の異常がない場合は、主軸を 500 RPM で 10 分間 アイドリングさせチラー冷却液を循環させます。3. 温度が 105°C を超えて上昇し続ける場合は非常停止を押します。4. チラーポンプと液位を点検します。"
                    },
                    {
                        "situation": "電気火災・ショート火花 (Electrical fault / Smoke / Sparks)",
                        "action": "1. 直ちに非常停止ボタンを押します。2. 制御盤の 400V 主電源操作ハンドルを速やかに OFF の位置に倒します。3. 火災が発生した場合は二酸化炭素 (CO2) または粉末消火器を使用してください。電気設備に水をかけることは厳禁です！"
                    },
                    {
                        "situation": "予期せぬ突発的機械停止 (Unexpected machine shutdown)",
                        "action": "1. 安易に電源を再投入しないでください。2. 盤内アンプのエラーLED表示を確認し、表示されたエラーコードを控えます。3. 主電源電圧を測定します。4. 各軸カバーが機械的に噛み込んでいないか確認してから再起動します。"
                    },
                    {
                        "situation": "非常停止解除・リセット復旧手順 (Emergency stop reset sequence)",
                        "action": "1. すべての作業者が機械動作範囲および切削ゾーンから退避したことを確認します。2. 非常停止原因となった危険要因が完全に解消されたことを確認します。3. 押し込まれた非常停止ボタンを右へ回してポップアップさせます。4. 操作盤の青色「アラームリセット (ALARM RESET)」を押します。5. 各軸原点復帰 (HOME REF) を実施します。"
                    }
                ]
            },
            "specifications": {
                "section_id": 9,
                "title": "9. 技術仕様・規格値 (Technical Specifications)",
                "specs": [
                    {"parameter": "電圧 (Voltage)", "value": "400V AC +/- 10% (3-Phase, 50/60 Hz)"},
                    {"parameter": "電流 (Current)", "value": "32A continuous full load (45A peak inrush)"},
                    {"parameter": "定格出力 (Power)", "value": "15 kW continuous S1 rating (22 kW S6-40%)"},
                    {"parameter": "主軸回転速度 (RPM)", "value": "100 - 24,000 RPM (Continuous variable speed)"},
                    {"parameter": "温度仕様 (Temperature range)", "value": "Ambient: 18°C - 25°C | Chiller: 20°C +/- 0.5°C | Max Motor Limit: 94°C (Alarm at 115°C)"},
                    {"parameter": "圧力仕様 (Pressure)", "value": "Shop Air: 6.5 bar | Central Lube: 18 bar | TSC Coolant: 45 bar - 70 bar"},
                    {"parameter": "使用環境条件 (Operating conditions)", "value": "Clean industrial workshop, 30% - 75% RH non-condensing, foundation vibration < 0.5 mm/s"}
                ]
            }
        }
    },

    "de": {
        "language_code": "de",
        "language_label": "Deutsch",
        "machine_name": "CNC-Fräsmaschine — Modell MX-7 Precision",
        "sections": {
            "overview": {
                "section_id": 1,
                "title": "1. Maschinenübersicht (Machine Overview)",
                "machine_name": "CNC-Fräsmaschine — Modell MX-7 Precision (CNC Milling Machine — Model MX-7 Precision)",
                "machine_purpose": "Hochpräzises 5-Achs-Vertikal-CNC-Bearbeitungszentrum für eng tolerierte Luft- und Raumfahrtkomponenten, medizinische Implantate und anspruchsvollen Präzisions-Werkzeug- und Formenbau.",
                "main_components": [
                    "Hochgeschwindigkeits-Elektrospindel (24,000 RPM)",
                    "5-Achs-Volldigital-AC-Servoantriebssystem (X, Y, Z, A, C)",
                    "40-fach Hochgeschwindigkeits-Werkzeugwechsler (ATC)",
                    "Industrie-CNC-Bahnsteuerung & Bedienpult",
                    "Hochdruck-Kühlmittelanlage für Innenkühlung (TSC) (70 bar)",
                    "Zentrales automatisches Gleitbahn-Schmiersystem (18 bar)"
                ],
                "basic_operating_principle": "Die Maschine synchronisiert 5 geschlossene Servoachsen mit Werkzeugdrehzahlen bis zu 24,000 RPM. Optische Glasmaßstäbe liefern kontinuierliche Lageistwerte an die CNC-Steuerung und ermöglichen automatisiertes Fräsen, Bohren und Konturieren mit einer Wiederholgenauigkeit von +/- 0.002 mm."
            },
            "safety": {
                "section_id": 2,
                "title": "2. Sicherheitsvorschriften (Safety Instructions)",
                "safety_precautions": [
                    "Sicherstellen, dass die Sicherheitstürverriegelung während aktiver Bearbeitungszyklen stets fest verriegelt bleibt.",
                    "Vor Drücken der Taste Zyklusstart (Cycle Start) überprüfen, ob das Werkstück sicher auf dem Frästisch aufgespannt ist.",
                    "Hände und Kleidung während des Einschaltens und Einrichtens stets außerhalb des Werkzeugmagazins und Spindelbereichs halten."
                ],
                "electrical_safety": [
                    "Die Versorgungsspannung beträgt 400V AC (3-phasig). Nur qualifizierte Elektrofachkräfte dürfen den Hauptschaltschrank öffnen.",
                    "Vor Wartungsarbeiten ist am Haupttrennschalter das Lockout/Tagout-Verfahren (LOTO) zwingend anzuwenden.",
                    "Nach dem Abschalten mindestens 10 Minuten warten, bis die Hochspannungs-Zwischenkreiskondensatoren vollständig entladen sind."
                ],
                "emergency_procedures": [
                    "Bei unvorhergesehenen Betriebsstörungen sofort einen der roten Not-Halt-Schlagtaster (E-stop) betätigen.",
                    "Bei Rauchentwicklung, Brandgeruch oder offenem Feuer Not-Halt drücken und den 400V Hauptschalter auf OFF stellen."
                ],
                "warnings": [
                    "WARNUNG: Hochspannung (400V) im hinteren Steuerungsschaltschrank.",
                    "WARNUNG: Die Frässpindel rotiert mit bis zu 24,000 RPM. Umherfliegende Späne und Werkzeugbruch stellen erhebliche Projektilgefahren dar.",
                    "WARNUNG: Der automatische Werkzeugwechslerarm bewegt sich im Programmlauf schlagartig und ohne Vorwarnung."
                ],
                "required_protective_equipment": [
                    "Schutzbrille mit Seitenschutz (ANSI Z87.1 / EN 166)",
                    "Sicherheitsschuhe mit Stahlkappe und rutschfester Sohle (EN ISO 20345)",
                    "Gehörschutz bei kontinuierlichen Zerspanungsgeräuschen über 85 dBA",
                    "Schnittfeste Schutzhandschuhe beim Wechseln scharfer Fräswerkzeuge (Handschuhe bei rotierender Spindel STRENG VERBOTEN!)"
                ]
            },
            "components": {
                "section_id": 3,
                "title": "3. Maschinenkomponenten (Machine Components)",
                "components_list": [
                    {
                        "name": "Hochgeschwindigkeits-Elektrospindel (High-Speed Electro-Spindle)",
                        "function": "Direkter Drehantrieb für Fräswerkzeuge mit stufenloser Drehzahlregelung bis 24,000 RPM.",
                        "normal_condition": "Ruhiger Lauf, Gehäusetemperatur unter 45°C (Grenzwert max. 94°C), Schwinggeschwindigkeit unter 0.8 mm/s.",
                        "common_problems": "Lagerverschleiß, thermische Überlastung über 94°C, Unwucht, Werkzeugspannfehler."
                    },
                    {
                        "name": "Achsenservos und Linearführungen (X, Y, Z, A, C)",
                        "function": "Setzt CNC-Sollwerte in translatorische Achsbewegungen und präzise rotatorische Winkelbewegungen um.",
                        "normal_condition": "Ruckfreie Verfahrbewegung, Wiederholgenauigkeit +/- 0.002 mm, konstanter 18 bar Schmierfilm.",
                        "common_problems": "Verschmutzung des optischen Glasmaßstabs, Kugelgewindetrieb-Umkehrspiel, Schleppfehler."
                    },
                    {
                        "name": "Automatischer Werkzeugwechsler (ATC)",
                        "function": "Nimmt 40 Werkzeughalter auf und wechselt Werkzeuge innerhalb von 1.8 Sekunden automatisch ein.",
                        "normal_condition": "Saubere Magazintaschen ohne Späne, Versorgungsdruck 6.5 bar, gleichmäßige 180°-Armschwenkung.",
                        "common_problems": "Spanklemmung in der Greiferklaue, Ausfall des Spannabfragesensors, Druckluftabfall."
                    },
                    {
                        "name": "Innenkühlungs-Hochdruckaggregat (TSC)",
                        "function": "Fördert Kühlschmierstoff unter Hochdruck direkt durch die Werkzeuginnenkanäle zur Spanabfuhr.",
                        "normal_condition": "Systemdruck zwischen 45 bar und 70 bar, Durchflussmenge > 6.2 L/min, Filteranzeige grün.",
                        "common_problems": "25-micron Filterelement verstopft, Pumpenkavitation, Riss im Hochdruckschlauch."
                    },
                    {
                        "name": "Zentrale Progressiv-Schmierpumpe (Lubrication Pump)",
                        "function": "Dosierte Schmierstoffversorgung aller Linearführungen und Kugelgewindetriebe mit ISO VG 68 Bettbahnöl.",
                        "normal_condition": "Druckpuls steigt alle 20 Minuten auf 18 bar an, Vorratsbehälter füllstandsgerecht über Min-Marke.",
                        "common_problems": "Schmierstoffmangel, gerissene 4 mm Polyamid-Leitung, festsitzender Progressiv-Verteilerkolben."
                    }
                ]
            },
            "operating": {
                "section_id": 4,
                "title": "4. Bedienungsanleitung (Operating Instructions)",
                "steps": {
                    "starting": [
                        "Sicherstellen, dass der elektrische Haupttrennschalter eingeschaltet ist (400V).",
                        "CNC-Schlüsselschalter auf ON drehen und das Steuerungssystem vollständig hochfahren lassen.",
                        "Not-Halt-Taster durch Rechtsdrehung entriegeln (E-stop).",
                        "Die Taste 'Maschine Ein / Machine Ready' auf dem Bedienpult drücken.",
                        "Referenzpunktfahrt (HOME REF) auf allen 5 Achsen (X, Y, Z, A, C) ausführen.",
                        "Vor schweren Fräsbearbeitungen das automatische 15-minütige Spindelwarmlaufprogramm bei 4,000 RPM durchführen."
                    ],
                    "normal_operation": [
                        "Verifiziertes CNC-Bearbeitungsprogramm über USB oder Netzwerk laden.",
                        "Werkzeugschneiden auf Beschädigung prüfen und Werkzeuglängen- sowie Radiuskorrekturen vermessen.",
                        "Rohteil aufspannen und sicherstellen, dass der hydraulische/pneumatische Spanndruck 25 bar beträgt.",
                        "Werkstücknullpunkt (WCS) mithilfe des optischen 3D-Messtasters antasten und abspeichern.",
                        "Prüfen, ob der Kühlschmierstoffbehälter mit 8% synthetischer Emulsion gefüllt ist.",
                        "Schutzkabinentür schließen und die grün leuchtende Taste 'ZYKLUSSTART' (CYCLE START) drücken."
                    ],
                    "monitoring": [
                        "Spindellastanzeige im Auge behalten; die Nennlast muss während des Schnitts unter 80% bleiben.",
                        "Kühlmitteldurchfluss überwachen; Durchflussanzeige muss stabil über 6.2 L/min anzeigen.",
                        "Achsenschwingungsmonitore beobachten und auf Rattermarken oder abnormale Schnittgeräusche achten.",
                        "Spindeltemperatur auf der Telemetrieanzeige überwachen (Grenzwert strikt < 94°C einhalten)."
                    ],
                    "stopping": [
                        "Am Ende eines Schnittdurchgangs die Taste 'VORSCHUBHALT' (FEED HOLD) betätigen.",
                        "Im MDI-Modus den Befehl M05 eingeben, um die Spindeldrehung kontrolliert stillzusetzen.",
                        "Kühlmittelzufuhr mit M09 abschalten.",
                        "Achsen auf Be- und Entladeposition verfahren, Schutztür öffnen und Werkstück begutachten."
                    ],
                    "emergency_shutdown": [
                        "Bei Gefahr sofort einen der roten Not-Halt-Schlagtaster (Emergency Stop) drücken.",
                        "Die Spindelenergie wird sofort getrennt, und die Nutzbremse stoppt die Spindel innerhalb von 1.5 Sekunden.",
                        "Die Achsantriebe werden unmittelbar positionsfest blockiert, um Werkzeugkollisionen zu verhindern.",
                        "Bei Rauchentwicklung, Funkenflug oder Brand sofort den 400V Hauptschalter abschalten."
                    ]
                }
            },
            "error_fault": {
                "section_id": 5,
                "title": "5. Fehler- und Störungsanweisungen (Error and Fault Instructions)",
                "items": [
                    {
                        "problem": "Motor überhitzt (Spindeltemperatur erreicht 94°C oder höher)",
                        "possible_cause": "Hohe Zerspanungslast, mangelhafte Belüftung des Kühlkreislaufs, zu geringer Kühlmittelstand im Chiller oder Lagerschaden.",
                        "what_to_check": "Spindeltemperatur auf dem Telemetriedisplay ablesen, Druck am Chiller bei 2.5 bar prüfen, Schaltschranklüfter auf Verstopfung prüfen.",
                        "recommended_action": "Maschine sofort stoppen und Motor untersuchen. Spindel 15 Minuten bei 500 RPM lastfrei rotieren lassen, um Kühlmittel zirkulieren zu lassen."
                    },
                    {
                        "problem": "Starke Schwingungen der Frässpindel bei hoher Drehzahl",
                        "possible_cause": "Dynamische Unwucht des Werkzeughalters, Auskraglänge über 3:1, verschlissenes Spindellager.",
                        "what_to_check": "Wuchtgüte des Halters prüfen (ISO 1940-1 Güteklasse G2.5), Schneiden mit optischer Lupe inspizieren, Spindelrundlauf messen.",
                        "recommended_action": "Beschädigte Wendeschneidplatte austauschen. Werkzeughalter auswuchten; Betrieb über 10,000 RPM bis zur Behebung untersagen."
                    },
                    {
                        "problem": "Druckabfall der Innenkühlung unter 45 bar",
                        "possible_cause": "Verschmutzter 25-micron Filter, zu niedriger Füllstand im KSS-Tank oder Lufteintrag in der Pumpe.",
                        "what_to_check": "Rote Differenzdruckanzeige am Filtergehäuse prüfen, Füllstand am Schauglas kontrollieren.",
                        "recommended_action": "Verschmutzte Filterpatrone wechseln (Teile-Nr. MX-FLT-025), KSS nachfüllen, Entlüftungsventil an der Pumpe öffnen."
                    },
                    {
                        "problem": "Werkzeugwechslerarm spannt Werkzeug nicht ein",
                        "possible_cause": "Pneumatischer Werkstattdruck unter 6.0 bar, Späne im Spindel-BT40-Innenkonus, Anzugsbolzen verschlissen.",
                        "what_to_check": "Pneumatikdruckmanometer prüfen (Sollwert 6.5 bar), Spindelkegel auf Späneverschleppung prüfen.",
                        "recommended_action": "Spindelkegel mit kegeligem Filzwischer reinigen, Druckminderer auf 6.5 bar einstellen, beschädigten Anzugsbolzen ersetzen."
                    }
                ]
            },
            "maintenance": {
                "section_id": 6,
                "title": "6. Wartungsanweisungen (Maintenance Instructions)",
                "regular_inspection": [
                    "Täglich: Ölstand im Zentralschmierbehälter kontrollieren (ISO VG 68 Bettbahnöl).",
                    "Täglich: Pneumatischen Versorgungsdruck auf konstante 6.5 bar überprüfen.",
                    "Täglich: Füllstand des Kühlschmierstofftanks prüfen und Emulsionskonzentration mittels Refraktometer auf 8% prüfen."
                ],
                "cleaning": [
                    "Nach jeder Arbeitsschicht Späne von Führungsabdeckungen, Kugelgewindetrieben und Türführungen entfernen.",
                    "Spindelinnenkegel BT40 mit fusselfreiem Tuch und speziellem Spindelreiniger auswischen.",
                    "Filtermatten der Schaltschranklüfter wöchentlich mit sauberer Druckluft ausblasen."
                ],
                "lubrication": [
                    "Zentralschmierbehälter stets mit partikelfreiem ISO VG 68 Führungsbahnöl befüllt halten.",
                    "Kurvengetriebe des Werkzeugwechslers monatlich mit Hochgeschwindigkeitsspindelfett (Kluber NBU 15) schmieren.",
                    "Gegengewichtsketten alle 500 Betriebsstunden mit Schmieröl benetzen."
                ],
                "component_inspection": [
                    "Glasmaßstäbe der Linearmesssysteme auf Öldunst und Dichtlippenzustand prüfen.",
                    "Axialspiel der Frässpindel mit Feintaster messen (zulässiger Maximalwert < 0.003 mm).",
                    "Not-Halt-Taster und Schutztür-Verriegelungsschalter regelmäßig auf sichere Zwangsöffnung testen."
                ],
                "replacement_instructions": [
                    "Hochdruck-Kühlmittelfilter: 25-micron Filterelement erneuern, sobald die rote Differenzdruckanzeige auslöst.",
                    "Abstreiferlippen der Führungsabdeckungen: Beschädigte Polyurethan-Abstreifer jährlich erneuern.",
                    "Spindelchiller-Kühlmedium: Glykol-Kühlgemisch im geschlossenen Kreislauf jährlich spülen und erneuern."
                ],
                "maintenance_intervals": [
                    {"interval": "Täglich (8 Hours)", "task": "Schmierölstand prüfen, Druckluft (6.5 bar) kontrollieren, Späne räumen, Spindelkegel säubern."},
                    {"interval": "Wöchentlich (50 Hours)", "task": "Schaltschrankfilter reinigen, KSS-Konzentration (8%) messen, Not-Halt-Funktion prüfen."},
                    {"interval": "Monatlich (200 Hours)", "task": "Werkzeugwechsler-Greiferklauen fetten, Sperrluftdruck für Maßstäbe (1.5 bar) prüfen."},
                    {"interval": "Halbjährlich (1,000 Hours)", "task": "Kugelgewindetrieb-Umkehrspiel messen, Spannzangen-Einzugskraft ermitteln (> 10.5 kN)."},
                    {"interval": "Jährlich (2,000 Hours)", "task": "Chiller-Kühlgemisch wechseln, Abstreifer erneuern, Maschinengeometrie per Laser vermessen."}
                ]
            },
            "troubleshooting": {
                "section_id": 7,
                "title": "7. Fehlersuchtabelle (Troubleshooting Table)",
                "table": [
                    {
                        "error": "Motor überhitzt (Motor overheating)",
                        "possible_cause": "Übermäßige Schnittlast, Ausfall der Spindelkühlung, Umgebungstemperatur > 38°C oder Lagerschaden (Temperatur > 94°C).",
                        "solution": "Vorschub reduzieren, Chiller-Kreislaufdruck bei 2.5 bar prüfen, Schaltschrankfilter reinigen, Motor abkühlen lassen."
                    },
                    {
                        "error": "Übermäßige Vibrationen (Excessive vibration)",
                        "possible_cause": "Unwucht im Werkzeughalter, Auskraglänge über 3:1, Spindellager verschlissen, Werkstückspannung unzureichend.",
                        "solution": "Halter bei 24,000 RPM auf Wuchtgüte G2.5 wuchten, Auskragung verkürzen, Spanndruck 25 bar kontrollieren."
                    },
                    {
                        "error": "Abnormale Geräusche (Abnormal noise)",
                        "possible_cause": "Schmiermangel am Kugelgewindetrieb, trockene Zahnradpaarung, lose Abdeckbleche, ausgebrochene Schneidkante.",
                        "solution": "Manuelle Zwangsschmierung auslösen (18 bar), Werkzeugschneide prüfen, Befestigungsschrauben nachziehen."
                    },
                    {
                        "error": "Spannungsprobleme (Voltage problems)",
                        "possible_cause": "Phasenunsymmetrie der 400V Netzeinspeisung > 3%, Überspannungsimpuls, durchgebrannte Hauptsicherung.",
                        "solution": "Dreiphasen-Leiterspannungen an den Eingangsklemmen messen (380V - 420V Sollwert). Transformatorabgriff anpassen."
                    },
                    {
                        "error": "Stromprobleme (Current problems)",
                        "possible_cause": "Überstrom im Spindelmotorstator, Achsklemmen/mechanische Blockade, IGBT-Modul im Servoverstärker defekt.",
                        "solution": "Motorleitungen trennen und Wicklungswiderstand messen (symmetrisch auf 0.1 ohm). Mechanische Blockade beseitigen."
                    },
                    {
                        "error": "Sensorausfall (Sensor failure)",
                        "possible_cause": "Betauung auf Glasmaßstab, Metallspäne vor induktivem Näherungsschalter, Bruch des 24V Sensorkabels.",
                        "solution": "Maßstabsglas mit Isopropanol reinigen, Sensorfläche abblasen, 24V DC Versorgungsspannung prüfen."
                    },
                    {
                        "error": "Lagerschaden (Bearing failure)",
                        "possible_cause": "Verlust des Hochgeschwindigkeitsfettes, dynamische Fliehkraftüberlastung bei 24,000 RPM, Kühlmitteleintritt.",
                        "solution": "Spindelschwingungspegel messen; überschreitet der Rundlauffehler 0.005 mm TIR, Spindelkeramiklagersatz erneuern."
                    },
                    {
                        "error": "Stromausfall (Power failure)",
                        "possible_cause": "Hauptleistungsschalter ausgelöst, 24V DC Schaltnetzteil überlastet, Sicherheitsrelais abgefallen.",
                        "solution": "400V Hauptschalter wiedereinschalten, grüne Status-LED am 24V DC Netzteil prüfen, Sicherheitskreis durchmessen."
                    },
                    {
                        "error": "Kommunikationsfehler (Communication failure)",
                        "possible_cause": "EtherCAT Feldbuskabel lose, Knotenadressen-Konflikt am Antrieb, elektromagnetische Störstrahlung (EMI).",
                        "solution": "Geschirmte RJ45-Stecker fest einstecken, Schirmungsmasseband prüfen, Drehschalter für Antriebsadresse kontrollieren."
                    }
                ]
            },
            "emergency_procedures": {
                "section_id": 8,
                "title": "8. Notfallverfahren (Emergency Procedures)",
                "procedures": [
                    {
                        "situation": "Kritischer Hardwareausfall (Critical hardware failure)",
                        "action": "1. Sofort roten Not-Halt-Taster drücken. 2. Achsen nicht manuell bewegen. 3. Elektrischen Hauptschalter auf OFF schalten. 4. Maschine mit 'AUSSER BETRIEB - NICHT SCHALTEN' kennzeichnen und Instandhaltung informieren."
                    },
                    {
                        "situation": "Überhitzung (Spindel oder Kühlmittel > 94°C)",
                        "action": "1. Zerspanungsvorschub sofort abbrechen. 2. Sofern kein Rauch sichtbar ist, Spindel 10 Minuten bei 500 RPM lastfrei drehen lassen, um Kühlmedium zu zirkulieren. 3. Steigt die Temperatur über 105°C, Not-Halt drücken. 4. Chillerpumpe und Füllstand prüfen."
                    },
                    {
                        "situation": "Elektrischer Fehler / Rauch / Funken (Electrical fault)",
                        "action": "1. Umgehend Not-Halt-Taster betätigen. 2. Den 400V Hauptschalterhebel sofort auf OFF umlegen. 3. Bei Brandausbruch CO2- oder Pulverfeuerlöscher für elektrische Anlagen einsetzen. Niemals Wasser verwenden!"
                    },
                    {
                        "situation": "Unerwarteter Maschinenstillstand (Unexpected machine shutdown)",
                        "action": "1. Maschine nicht voreilig wieder einschalten. 2. Fehler-LEDs am Schaltschrank ablesen und angezeigte Störcodes notieren. 3. Versorgungsspannung prüfen. 4. Abdeckungen vor Neustart auf mechanisches Klemmen untersuchen."
                    },
                    {
                        "situation": "Not-Halt-Rückstellung und Wiederanlauf (Emergency stop reset sequence)",
                        "action": "1. Sicherstellen, dass sich niemand im Gefahren- und Verfahrbereich aufhält. 2. Die Ursache des Not-Halts vollständig beseitigen. 3. Not-Halt-Taster durch Rechtsdrehung entriegeln. 4. Blaue Taste 'ALARM RESET' am Pult drücken. 5. Achsen neu referenzieren (HOME REF)."
                    }
                ]
            },
            "specifications": {
                "section_id": 9,
                "title": "9. Technische Spezifikationen (Technical Specifications)",
                "specs": [
                    {"parameter": "Spannung (Voltage)", "value": "400V AC +/- 10% (3-Phase, 50/60 Hz)"},
                    {"parameter": "Strom (Current)", "value": "32A continuous full load (45A peak inrush)"},
                    {"parameter": "Leistung (Power)", "value": "15 kW continuous S1 rating (22 kW S6-40%)"},
                    {"parameter": "Drehzahl (RPM)", "value": "100 - 24,000 RPM (Continuous variable speed)"},
                    {"parameter": "Temperaturbereich (Temperature range)", "value": "Ambient: 18°C - 25°C | Chiller: 20°C +/- 0.5°C | Max Motor Limit: 94°C (Alarm at 115°C)"},
                    {"parameter": "Druck (Pressure)", "value": "Shop Air: 6.5 bar | Central Lube: 18 bar | TSC Coolant: 45 bar - 70 bar"},
                    {"parameter": "Betriebsbedingungen (Operating conditions)", "value": "Clean industrial workshop, 30% - 75% RH non-condensing, foundation vibration < 0.5 mm/s"}
                ]
            }
        }
    }
}


def get_multilingual_manual(lang: str = "en") -> dict:
    """Returns the complete 9-section machine instruction manual for the requested language code."""
    normalized_lang = (lang or "en").lower().strip()
    if normalized_lang.startswith("zh"):
        normalized_lang = "zh"
    elif normalized_lang.startswith("ja"):
        normalized_lang = "ja"
    elif normalized_lang.startswith("de"):
        normalized_lang = "de"
    else:
        normalized_lang = "en"

    return MULTILINGUAL_MANUAL.get(normalized_lang, MULTILINGUAL_MANUAL["en"])


def get_available_languages() -> list:
    """Returns list of supported language metadata for the selector bar."""
    return [
        {"code": "en", "label": "English", "native": "English", "flag": "EN"},
        {"code": "zh", "label": "Simplified Chinese", "native": "中文", "flag": "ZH"},
        {"code": "ja", "label": "Japanese", "native": "日本語", "flag": "JA"},
        {"code": "de", "label": "German", "native": "Deutsch", "flag": "DE"}
    ]
