# 1942 Flat Top Unit Data Specification

## 1. Purpose

This document defines the aircraft, ship, carrier, base, and combat data required by the digital game. It is derived from `flattop/operations_chart_models.py`, the scenario setup in `main.py`, and the combat rules.

This is the data contract for a web rules engine, AI, UI, save format, and scenario loader. It separates:

- values currently implemented in the prototype
- rules that interpret those values
- data inconsistencies requiring confirmation

The prototype's Python classes are evidence for the current data model, not a requirement for the web implementation language or architecture.

## 2. Data Authority

The intended precedence is:

1. confirmed rulebook value
2. scenario-specific value
3. validated unit data table
4. prototype factory default

A prototype default must not silently override a confirmed scenario or rule value. Every unit record should include a source reference and a version.

## 3. Aircraft Schema

Every aircraft type must have a data record with these fields:

| Field | Meaning |
|---|---|
| `id` | Stable machine identifier |
| `display_name` | Player-facing name |
| `side` | Allied, Japanese, or scenario-neutral |
| `movement_factor` | Hexes available for movement under normal rules |
| `range_factor` | Flight endurance at takeoff |
| `range_remaining` | Current endurance; initialized from range factor and reduced by flight/combat |
| `mission_roles` | Interceptor, escort, bomber, or combinations |
| `armament_options` | GP, AP, Torpedo, Unarmed where legal |
| `altitude_rules` | High/low restrictions and changes |
| `air_to_air_bht` | Basic Hit Table value for air combat |
| `bombing_bht` | BHT values by altitude, target, and payload |
| `torpedo_bht` | Ship torpedo attack BHT, if applicable |
| `replacement_category` | Land-based or sea-based for replacement accounting |
| `can_attack_unarmed` | Whether the aircraft can initiate an attack without armament |

`range_factor` is the prototype's endurance value. The rules engine must define whether the web implementation displays it as turns, hours, or a scenario time-unit; the source code currently describes it inconsistently as hours while combat logic reduces it per turn.

## 4. Aircraft Combat Data Mapping

The aircraft combat record contains these BHT fields:

| Field | Target and attack |
|---|---|
| `air_to_air` | Air-to-air combat |
| `level_bombing_high_base_gp` | High-level GP bombing against a base |
| `level_bombing_high_base_ap` | High-level AP bombing against a base |
| `level_bombing_low_base_gp` | Low-level GP bombing against a base |
| `level_bombing_low_base_ap` | Low-level AP bombing against a base |
| `dive_bombing_base_gp` | Dive GP bombing against a base |
| `dive_bombing_base_ap` | Dive AP bombing against a base |
| `level_bombing_high_ship_gp` | High-level GP bombing against ships |
| `level_bombing_high_ship_ap` | High-level AP bombing against ships |
| `level_bombing_low_ship_gp` | Low-level GP bombing against ships |
| `level_bombing_low_ship_ap` | Low-level AP bombing against ships |
| `dive_bombing_ship_gp` | Dive GP bombing against ships |
| `dive_bombing_ship_ap` | Dive AP bombing against ships |
| `torpedo_bombing_ship` | Torpedo attack against ships |

Zero values mean the attack is unavailable or has no modeled effectiveness. They must not be interpreted as missing data without checking the rules.

## 5. Current Aircraft Values

The following values are implemented by `AircraftFactory`. BHT columns are shown as `A2A / H-base-GP / H-base-AP / L-base-GP / L-base-AP / D-base-GP / D-base-AP / H-ship-GP / H-ship-AP / L-ship-GP / L-ship-AP / D-ship-GP / D-ship-AP / Torpedo-ship`.

| Type | Movement | Range | Combat BHT values |
|---|---:|---:|---|
| A-20 | 9 | 6 | 3 / 5 / 2 / 8 / 3 / 0 / 0 / 0 / 1 / 2 / 5 / 0 / 0 / 0 |
| Avenger | 7 | 8 | 3 / 4 / 2 / 6 / 2 / 0 / 0 / 0 / 1 / 2 / 5 / 0 / 0 / 6 |
| Beaufighter | 9 | 6 | 6 / 0 / 0 / 5 / 0 / 0 / 0 / 0 / 0 / 1 / 3 / 0 / 0 / 0 |
| Beaufort | 7 | 8 | 3 / 0 / 0 / 0 / 0 / 0 / 0 / 0 / 0 / 0 / 0 / 0 / 0 / 0* |
| B-17 | 8 | 12 | 8 / 13 / 5 / 0 / 0 / 0 / 0 / 0 / 2 / 0 / 0 / 0 / 0 / 0 |
| B-25 | 9 | 7 | 4 / 8 / 3 / 11 / 5 / 0 / 0 / 0 / 1 / 3 / 7 / 0 / 0 / 0 |
| B-26 | 10 | 6 | 4 / 6 / 2 / 10 / 4 / 0 / 0 / 0 / 1 / 2 / 5 / 0 / 0 / 5 |
| Catalina | 6 | 20 | 4 / 6 / 2 / 9 / 3 / 0 / 0 / 0 / 1 / 2 / 7 / 0 / 0 / 10 |
| Dauntless | 9 | 6 | 3 / 3 / 1 / 5 / 1 / 6 / 2 / 0 / 0 / 2 / 5 / 2 / 7 / 0 |
| Devastator | 6 | 5 | 2 / 3 / 1 / 5 / 2 / 0 / 0 / 0 / 0 / 1 / 5 / 0 / 0 / 6 |
| Hudson | 7 | 10 | 3 / 3 / 1 / 6 / 2 / 0 / 0 / 0 / 1 / 1 / 4 / 0 / 0 / 0 |
| P-38 | 12 | 5 | 7 / 0 / 0 / 5 / 0 / 0 / 0 / 0 / 0 / 1 / 0 / 0 / 0 / 0 |
| P-39 | 11 | 5 | 6 / 0 / 0 / 5 / 0 / 0 / 0 / 0 / 0 / 1 / 0 / 0 / 0 / 0 |
| P-40 | 11 | 5 | 7 / 0 / 0 / 4 / 0 / 0 / 0 / 0 / 0 / 1 / 0 / 0 / 0 / 0 |
| Wildcat | 8 | 6 | 9 / 0 / 0 / 4 / 0 / 0 / 0 / 0 / 0 / 1 / 0 / 0 / 0 / 0 |
| Betty | 9 | 10 | 3 / 4 / 2 / 6 / 2 / 0 / 0 / 0 / 1 / 2 / 5 / 0 / 0 / 9 |
| Dave | 4 | 6 | 1 / 0 / 0 / 1 / 0 / 0 / 0 / 0 / 0 / 0 / 0 / 0 / 0 / 0 |
| Emily | 9 | 24 | 6 / 8 / 3 / 9 / 4 / 0 / 0 / 0 / 1 / 3 / 7 / 0 / 0 / 15 |
| Judy | 11 | 6 | 3 / 2 / 1 / 3 / 1 / 4 / 2 / 0 / 0 / 1 / 5 / 2 / 7 / 0 |
| Jake | 5 | 9 | 1 / 0 / 0 / 1 / 0 / 0 / 0 / 0 / 0 / 0 / 0 / 0 / 0 / 0 |
| Kate | 7 | 7 | 2 / 4 / 2 / 6 / 2 / 0 / 0 / 0 / 1 / 2 / 6 / 0 / 0 / 10 |
| Mavis | 8 | 23 | 5 / 6 / 2 / 7 / 3 / 0 / 0 / 0 / 1 / 2 / 6 / 0 / 0 / 15 |
| Nell | 8 | 8 | 3 / 4 / 2 / 6 / 2 / 0 / 0 / 0 / 1 / 2 / 4 / 0 / 0 / 9 |
| Pete | 4 | 6 | 1 / 0 / 0 / 1 / 0 / 0 / 0 / 0 / 0 / 0 / 0 / 0 / 0 / 0 |
| Rufe | 9 | 6 | 6 / 0 / 0 / 3 / 0 / 0 / 0 / 0 / 0 / 1 / 0 / 0 / 0 / 0 |
| Val | 9 | 7 | 2 / 2 / 1 / 3 / 1 / 4 / 2 / 0 / 0 / 1 / 5 / 2 / 7 / 0 |
| Zero | 10 | 8 | 9 / 0 / 0 / 3 / 0 / 0 / 0 / 0 / 0 / 1 / 0 / 0 / 0 / 0 |

`*` Beaufort is constructed without the explicit `AircraftCombatData` object in the current factory branch, so its combat values fall back to class defaults. This is a data defect requiring correction or confirmation.

## 6. Aircraft Mission Roles and Armament

The rules and current classifier imply:

| Role rule | Aircraft |
|---|---|
| Interceptor-capable | Zero, P-38, P-39, P-40, Beaufighter, Wildcat; classifier also treats armed aircraft as bombers |
| Interceptor/escort but not bomber by type | Dave, Jake, Pete |
| Bomber-only by type | Avenger, Dauntless, Judy, Val, B-17, B-25, B-26, Kate, Nell, Mavis, Emily, Beaufort, Hudson, A-20, Devastator |
| Armament override | Any aircraft armed at takeoff is treated as a bomber until landing |

This table requires a rules review because the classifier's implementation and the source rule's “all other planes” wording do not perfectly align. The web implementation must use an explicit mission-role data field rather than infer roles from incomplete type sets.

Armament options currently exposed by the desktop UI are:

- `GP`
- `AP`
- `Torpedo`
- unarmed (`None`)

## 7. Ship Schema

Every ship record must include:

| Field | Meaning |
|---|---|
| `id` and `name` | Stable identity and display name |
| `class` | CV, CVL, AV, CAV, BB, CA, CL, DD, PG, AO, AP, APD, SS, etc. |
| `status` | Operational, anchored, crippled, sunk, screened, or scenario-specific status |
| `gunnery_factor` | Surface gunnery strength; called `attack_factor` in the prototype |
| `anti_air_factor` | AA contribution against attacking bombers |
| `torpedo_factor` | Torpedo attack strength |
| `torpedo_factor_used` | Whether the one-use torpedo supply is expended |
| `movement_factor` | Ship movement allowance |
| `damage_factor` | Hits required to sink |
| `damage` | Current accumulated hits |
| `ammunition_factor` | Remaining gunnery ammunition |
| `surface_combat_exhausted` | Whether one-use surface ammunition is exhausted |
| `launch_factor` | For plane-carrying ships |
| `maximum_capacity` | For plane-carrying ships |
| `readying_factor` | For plane-carrying ships |
| `plane_handling_type` | Aircraft handling restriction |
| `radar` | Detection capability |

Damage must derive effective values without destroying the original values. The source rules require damage to reduce movement, gunnery, AA, and launch capability while torpedo capacity is not reduced.

## 8. Ship Factory Data

The factory currently defines named ship records by grouped cases. The data specification must preserve the groups but materialize them into individual records in scenario data.

### 8.1 Japanese named groups

| Names or group | Class | Gunnery | AA | MF | Damage |
|---|---|---:|---:|---:|---:|
| Akagi, Kaga | CV | 1 | 4 | 2 | 6 |
| Soryu, Hiryu | CV | 1 | 4 | 2 | 5 |
| Zuikaku, Shokaku | CV | 1 | 5 | 2 | 6 |
| Hiyo, Junyo | CV | 1 | 4 | 1 | 5 |
| Ryujo, Zuiho | CV | 1 | 3 | 2 | 4 |
| Shoho, Hosho | CV | 1 | 2 | 2 | 3 |
| Yamato, Musashi | BB | 28 | 4 | 2 | 18 |
| Kirishima, Hiei, Haruna, Kongo, Fuso | BB | 12 | 3 | 2 | 10 |
| Hyuga, Ise, Yamashiro | BB | 15 | 3 | 1 | 11 |
| Nagato, Mutsu | BB | 18 | 3 | 1 | 12 |
| Myoko, Haguro, Takao, Atago, Maya, Chokai, Kumano, Suzuya, Nachi | CA | 6 | 2 | 2 | 6 |
| Kinugasa, Furutaka, Yubari, Tenryu, Aoba, Kako, Ashigara, Mikuma | CA/CL by factory branch | 4 or 2 | 2 or 1 | 2 | 5 or 4 |
| Chikuma, Tatsuta, Tone | CAV | 3 | 2 | 2 | 6 |
| Kamikawa, Chitose | AV | 1 | 2 | 2 | 3 |

### 8.2 Allied named groups

| Names or group | Class | Gunnery | AA | MF | Damage |
|---|---|---:|---:|---:|---:|
| Lexington | CV | 1 | 4 | 2 | 6 |
| Yorktown | CV | 1 | 4 | 2 | 5 |
| Enterprise | CV | 1 | 7 | 2 | 7 |
| Hornet | CV | 1 | 5 | 2 | 7 |
| Saratoga | CV | 1 | 5 | 2 | 8 |
| Wasp | CV | 1 | 5 | 2 | 6 |
| Ranger | CVL | 1 | 3 | 2 | 4 |
| N. Carolina, Washington | BB | 25 | 7 | 2 | 15 |
| S. Dakota, Indiana | BB | 25 | 9 or 7 | 2 | 15 |
| Colorado, Idaho, Maryland, Mississippi, Tennessee, New Mexico | BB | 20 | 3 | 1 | 11 |
| Arizona, Nevada, Oklahoma, Pennsylvania | BB | 18 | 3 | 1 | 10 |
| W. Virgina | BB | 22 | 3 | 1 | 15 |
| Vincennes, Houston, Quincy, Louisville, Portland, Astoria, Chicago, Northampton, New Orleans, Chester, Nashville | CA | 4 | 2 | 2 | 5 |
| Pensacola, Indianapolis, Minneapolis, San Francisco | CA | 3 | 2 | 2 | 3 |
| Helena, Nashville, Honolulu, St. Louis | CL | 4 | 2 | 2 | 5 |
| Hobart | CL | 3 | 1 | 2 | 4 |
| San Diego, San Juan, Juneau, Atlanta | CL | 2 | 3 | 2 | 4 |
| Detroit, Raleigh | CL | 2 | 1 | 2 | 4 |
| Australia | CA | 4 | 1 | 2 | 5 |
| Salt Lake City | CA | 5 | 2 | 2 | 5 |

The factory source contains duplicate names and overlapping match branches. For example, `Nashville` appears in more than one branch. The production unit table must resolve these conflicts explicitly and add automated duplicate-name validation.

## 9. Carrier and Base Air Operations Data

Plane-carrying units require a separate operations record:

| Field | Meaning |
|---|---|
| `maximum_capacity` | Maximum aircraft factors present |
| `launch_factor_min` | Minimum-launch capacity |
| `launch_factor_normal` | Normal-launch capacity |
| `launch_factor_max` | Maximum-launch capacity |
| `readying_factor` | Factors that can change readiness each turn |
| `plane_handling_type` | CV, LP, or other aircraft handling restriction |
| `anti_air_factor` | Defensive AA |
| `damage` | Current carrier/base damage |
| `aircraft_by_status` | In Flight, Just Landed, Readying, Ready |

Current carrier examples from the factory include:

| Carrier | Capacity | LF min / normal / max | Readying | MF | Damage |
|---|---:|---:|---:|---:|---:|
| Lexington | 30 | 3 / 12 / 24 | 8 | 2 | 6 |
| Yorktown | 30 | 3 / 11 / 22 | 9 | 2 | 5 |
| Enterprise | 33 | 3 / 11 / 22 | 9 | 2 | 7 |
| Hornet | 33 | 3 / 11 / 22 | 9 | 2 | 7 |
| Saratoga | 32 | 3 / 12 / 24 | 8 | 2 | 8 |
| Wasp | 28 | 3 / 10 / 20 | 7 | 2 | 6 |
| Shokaku / Zuikaku | 28 | 3 / 10 / 20 | 8 | 2 | 6 |
| Hiyo / Junyo | 18 | 3 / 7 / 14 | 6 | 1 | 5 |
| Ryujo / Zuiho | 16 | 2 / 5 / 10 | 4 | 2 | 4 |
| Shoho / Hosho | 10 | 2 / 4 / 8 | 4 | 2 | 3 |

## 10. Damage-Derived Effective Values

The data model must retain original and effective values. At minimum:

- ship MF reduces at half Damage Factor
- ships one hit below sinking may become crippled and immobile
- ship gunnery and AA reduce by hits
- carrier/base LF reduces according to class-specific rules
- base LF, AA, AAF, and SF can reach zero or negative values where rules permit
- torpedo capacity is not reduced by ordinary damage
- base and carrier aircraft losses follow readiness order

The web API should return both original and effective values so the UI can explain damage effects.

## 11. Required Validation

Before production data is accepted, automated validation must verify:

1. Every aircraft type has movement, range, mission roles, armament options, and combat data.
2. Every ship name is unique within a side and maps to one class.
3. Every carrier has capacity, launch factors, readying factor, and handling type.
4. Every scenario-referenced unit exists in the unit catalog.
5. No aircraft has a weapon option unsupported by its combat data.
6. No unit has a negative movement or capacity value.
7. Duplicate or unreachable factory branches are reported.
8. Unit data can be serialized and loaded without losing combat attributes.
9. Combat BHT fields map exactly to the names used by the combat resolver.

## 12. Known Source Data Issues

The current prototype contains issues that must be resolved before treating it as a production data source:

- Beaufort is created without explicit combat data in its factory branch.
- Several ship factory match branches contain duplicate or overlapping names.
- `attack_factor` is the prototype name for ship gunnery factor; the web schema should use an unambiguous field name.
- Aircraft range is described as hours in one place and reduced per turn in another.
- Mission-role classification is partly inferred from aircraft type and partly overridden by armament.
- Some scenario setup aircraft are placed directly into Ready or Readying without a recorded armament policy.

Each issue needs a decision recorded in a versioned unit-data change log before implementation begins.

## 13. Web Implementation Contract

The frontend must never hard-code unit statistics. It receives unit projections containing:

- identity and display name
- type and side
- original and effective movement/range/combat values
- legal armament options
- current armament
- readiness state
- launch and capacity state
- damage state
- legal actions

The server/rules engine owns all validation and derived values. The UI may display previews but cannot create combat values or infer missing weapon capability.
