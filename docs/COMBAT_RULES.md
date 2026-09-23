# 1942 Flattop Combat Rules Reference

## 1. Purpose

This document explains how combat is resolved in the digital game. It is intended for players, UI designers, rules-engine implementers, AI designers, and testers. It defines the meaning of BHT, how the Combat Results Table produces hits, the order of combat, the modifiers, and how hits become damage or losses.

The rules below preserve the source rules while expressing them in a form suitable for a digital implementation. The engine must record each step so the UI can explain the result without exposing hidden information prematurely.

## 2. Combat Eligibility

Combat requires units to occupy the same hex and be legally observed, subject to the specific combat type:

- Air-to-air combat may occur within two hexes of a plane-carrying ship or base, or in any hex containing a ship, and only between observed air units.
- Anti-aircraft and air attack combat require ships or a base in the hex and observed participating units.
- Surface attack combat may occur in sea or partial-land hexes between observed opposing naval units.
- No combat of any kind occurs in a storm hex.
- Combat in separate hexes is resolved separately; all combat in one hex is one battle.
- Combat is generally optional to initiate, but once a combat sequence is initiated, required steps and attacks cannot be avoided.

## 3. Basic Hit Table (BHT)

### 3.1 Meaning of BHT

BHT means Basic Hit Table. It is the combat effectiveness column used to resolve one declared attack. A BHT is selected from the applicable combat table using the attacker's factors, target type, weapon or combat mode, and any rule modifiers.

BHT is not the number of hits. It is the table column used with the number of attacking factors and one die roll to determine hits.

### 3.2 Calculating modified BHT

Start with the base BHT for the attack. Add or subtract every applicable modifier. Modifiers are cumulative.

The modified BHT is bounded as follows:

- If modifiers reduce it below 1, use BHT 1.
- If modifiers increase it above 15, resolve it as BHT 15.

The combat record must show:

1. base BHT
2. each modifier and its reason
3. final modified BHT
4. attacking factor count
5. die result
6. result number and final hits

### 3.3 Common BHT modifiers

The exact modifier depends on the combat table and attack type. The rules include these recurring effects:

- Clouds reduce air-to-air BHT by 1.
- Night reduces air-to-air BHT by 2.
- Certain armed fighter types have a -6 air-to-air BHT modifier.
- An interceptor or escort that does not expend an RF for air-to-air combat suffers a -6 BHT modifier.
- Air attack against a crippled ship receives +2 BHT.
- Air attack against an anchored ship receives +2 BHT.
- Clouds reduce air attack BHT by 2.
- Night reduces air attack BHT by 4.
- Surface attack against a crippled ship receives +1 BHT.
- Surface attack against an anchored ship receives +1 BHT.

The engine must use the modifier set belonging to the specific combat step. A modifier from one step must not leak into another step unless the rule explicitly says so.

## 4. Converting a Die Roll into Hits

For each declared attack, cross-index the final BHT with the number of attacking factors to obtain a Result Number from the Combat Results Table. Then roll one six-sided die.

### 4.1 Combat Results Table structure

The Combat Results Table has 15 BHT rows and exactly 14 attack-factor columns. It is a 15-row by 14-column lookup table:

- rows are BHT values 1 through 15
- columns are attack-factor ranges
- each cell contains a Result Number, zero, or no result

The attack-factor columns currently represented by the rule data are:

`[(1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (11, 12), (13, 15), (16, 20), (21, 24), (25, 30), (31, 35), (36, 40), (41, 45), (46, 999)]`

| Column | Attack-factor range |
|---:|---:|
| 1 | 1-2 |
| 2 | 3-4 |
| 3 | 5-6 |
| 4 | 7-8 |
| 5 | 9-10 |
| 6 | 11-12 |
| 7 | 13-15 |
| 8 | 16-20 |
| 9 | 21-24 |
| 10 | 25-30 |
| 11 | 31-35 |
| 12 | 36-40 |
| 13 | 41-45 |
| 14 | 46 or more |

The lookup algorithm is:

1. Validate that the final BHT is an integer from 1 through 15.
2. Sum the attacking factors for the declared attack. Do not sum unrelated formations or plane names.
3. Find the one attack-factor range containing that sum.
4. Use the BHT row and range column to retrieve the Result Number.
5. If the table cell is empty or no range matches, the attack produces no Result Number and therefore no hits.
6. Apply the die conversion to the retrieved Result Number.

Attack-factor totals are now contiguous through these columns: 24 belongs to the 21-24 range, and 25 belongs to the 25-30 range. There is no unmapped 24-25 edge case.

The table values and range definitions are rule data, not UI behavior. They must be versioned, testable, and shared by air-to-air, anti-aircraft, air attack, and any other combat mode that uses the Combat Results Table.

Apply the die adjustment to the Result Number:

| Die | Hit result |
|---|---|
| 1 | Result Number minus 2 |
| 2 | Result Number minus 1 |
| 3 or 4 | Result Number |
| 5 | Result Number plus 1 |
| 6 | Result Number plus 2 |

A negative hit result is treated as zero hits. If the table result is `*`, a die roll of 6 produces one hit and rolls 1 through 5 produce no hits.

The result is an integer number of hits. Excess hits are not transferred to another target and are not saved for a later attack unless a specific rule says otherwise.

## 5. Battle Sequence

Each battle is resolved in this order:

1. Air-to-air combat step
2. Anti-aircraft combat step
3. Air attack combat step
4. Surface attack combat step

Skip a step only when its participating units or conditions do not exist. Resolve all applicable attacks within a step before applying the step's simultaneous losses where the rules require simultaneity.

Only one round of each applicable combat type is allowed in a hex during a turn. A later turn may begin a new combat sequence if opposing units remain.

## 6. Air-to-Air Combat

### 6.1 Roles

- Interceptors are unarmed aircraft able to initiate air-to-air combat.
- Escorts accompany bombers and protect them.
- Bombers are armed aircraft conducting or capable of conducting an attack.

Only interceptors initiate ordinary air-to-air combat. Special interception can occur during movement or shadowing when the interception rules are satisfied.

Only aircraft at the same altitude can intercept or be intercepted. High- and low-altitude combat are resolved as separate combats.

### 6.2 Interceptor versus escort

1. The interceptor player designates interceptors attacking escorts.
2. The defender identifies eligible escorts at the same altitude.
3. Each plane name declares its target plane name.
4. Each side calculates its BHT and resolves its attack.
5. Losses are simultaneous and are removed after all attacks in the exchange.

Interceptors and escorts may expend one RF for the turn to avoid the -6 BHT penalty. Bombers do not expend RF for air-to-air combat.

### 6.3 Interceptor versus bomber

After interceptor-versus-escort combat:

- If surviving interceptors designated against escorts have at least a 2:1 ratio over surviving escorts, they may join attacks against bombers.
- If surviving escorts have at least a 2:1 ratio over the interceptors designated against escorts, no interceptor-versus-bomber combat occurs.
- Otherwise, only interceptors originally designated against bombers may attack bombers.

The interceptor player is not required to attack bombers merely because an attack is available.

## 7. Anti-Aircraft Combat

AA combat occurs only when bombers attack a task force or base. Interceptors and escorts are not targets of AA fire.

Before AA combat, the attacking player must declare which bombers attack which targets. AA losses are applied before the declared air attacks resolve. Surviving bombers cannot change their target allocation or cancel the declared attack because of AA losses.

## 8. Air Attack Combat

Each plane name's attack is resolved separately unless an explicit table rule combines it.

### 8.1 Dive bombing

Dive bombers begin the combat phase at high altitude, dive to low altitude for the attack, and expend one RF per attacking air factor.

### 8.2 Torpedo bombing

Torpedo attacks require low altitude and a plane type carrying torpedoes. Each attacking air factor expends one RF.

### 8.3 Level bombing

Level bombing may occur from high or low altitude. Low-altitude level bombing expends one RF per attacking air factor. High-altitude level bombing does not expend RF.

### 8.4 Air attack damage

Air attack hits are applied to the declared target. If a plane-carrying ship or base has aircraft in the affected readiness boxes, applicable bombing hits may be doubled under the damage rules. Air attack combat does not remove additional attacking planes after AA has resolved.

Bases cannot be directly attacked by air attack combat under the source rules; bases may be affected by bombardment and other scenario-defined effects.

## 9. Surface Attack Combat

### 9.1 Hidden ship assignments

At the start of surface combat, each side privately assigns every participating ship to one of:

- Gunnery Attack
- Torpedo Attack
- Screen

Crippled and anchored ships must be placed in Screen. Screened ships cannot attack or be attacked during the initial combat exchange.

Each side also secretly selects a die face. Reveal both ship assignments and dice before resolving combat. Add the two dice to determine the round's surface-combat BHT.

### 9.2 Gunnery combat

1. Total gunnery factors in Gunnery Attack positions.
2. Allocate those factors against legal enemy targets.
3. Resolve both sides' gunnery attacks using the shared BHT.
4. Treat gunnery as simultaneous: sunk or damaged ships still contribute their factors for the current exchange.
5. Remove sunk ships and record damage after both sides have attacked.

Ammunition is expended according to the BHT used. A ship with no ammunition cannot use gunnery; insufficient remaining ammunition halves its gunnery factor for that round and exhausts the remainder.

### 9.3 Torpedo combat

Surviving ships assigned to Torpedo Attack may attack after gunnery combat. Torpedo attacks are allowed only when the shared BHT reaches the required day or night threshold. Torpedoes are expended even if the threshold prevents hits.

Japanese and Allied torpedo attacks use their side-specific torpedo BHT values. Torpedo combat is simultaneous.

### 9.4 Breakthrough combat

After gunnery and torpedo combat, compare surviving attacking factors. A side with a 3:1 ratio may initiate breakthrough combat. The breakthrough attacker may use surviving gunnery factors from Gunnery Attack and Torpedo Attack positions. The defender uses only surviving Screen gunnery factors. Breakthrough uses the preceding gunnery BHT and does not permit torpedo attacks.

### 9.5 Bombardment

Bombardment is optional and occurs against an enemy base from a qualifying ship group. A ship participating in another surface combat role cannot also bombard unless it was screened and remains eligible. Bombardment uses its own BHT and ammunition expenditure and may trigger the base's defensive Surface Factor under the applicable conditions.

## 10. Damage Application and Persistence

The combat result is not complete when the hit count is calculated. The authoritative state transition must apply the hits, emit the resulting damage and loss events, update Victory Points, and persist the transition in the game event history so it can be reviewed, replayed, or restored by save/load.

## 11. Applying Hits

### 10.1 Aircraft

Each hit on aircraft eliminates one air factor. Excess hits are lost. Dispersed aircraft require two hits per eliminated air factor.

### 10.2 Ships

Record hits on the target ship. If hits reach the ship's Damage Factor, sink and remove the ship. Excess hits are lost.

Before continuing, update:

- Movement Factor
- Gunnery Factor
- AA Factor
- Launch Factor
- crippled status
- aircraft carried by the ship

### 10.3 Bases

Record base hits separately. Each hit reduces the base's applicable LF, AA, and SF. Base values may become negative where the rules allow. A base with LF zero or less cannot launch aircraft and scores the applicable Victory Points for each affected turn.

### 10.4 Aircraft on ships and bases

When a plane-carrying ship or base takes hits, eliminate aircraft according to the combat context and readiness order:

1. Ready
2. Just Landed
3. Readying
4. Dispersed, at one aircraft per two hits

The attacker chooses the plane name for qualifying daytime low-altitude bombing hits. The defender chooses in the other specified cases. The UI must present only the choices the rules permit.

## 12. Combat Event Record

A complete combat record must include:

- battle location and weather
- participants known to each side
- combat step
- declared targets
- base BHT
- modifiers and reasons
- final BHT
- attacker count
- die result
- Result Number
- hits
- losses and damage
- RF and ammunition expenditure
- Victory Points awarded

This record is the source for the combat log, replay, debugging, and AI evaluation. It must be filtered through each side's knowledge state before being shown to a player.

## 13. Worked BHT Example

Suppose an attack has a base BHT of 8 and 14 attacking factors. The Combat Results Table returns a Result Number of 4. If the die roll is:

- 1, the attack scores 2 hits
- 2, the attack scores 3 hits
- 3 or 4, the attack scores 4 hits
- 5, the attack scores 5 hits
- 6, the attack scores 6 hits

If clouds impose a -2 modifier, the final BHT is 6 before looking up the Result Number. The die adjustment is still applied after the Result Number is retrieved.

## 14. Implementation and UI Implications

The combat engine must expose intermediate calculations rather than returning only a final winner. The UI should show the BHT breakdown before the die result when the information is legal, then reveal the die result, Result Number, hits, and consequences in order.

The AI must evaluate expected results using the same tables, modifiers, and information constraints. Difficulty may change search and judgment, but it must not change BHTs, dice, or hidden information.

## 15. Combat Test Requirements

The combat test suite must verify:

- BHT is interpreted as a table column rather than a hit count
- BHT values are bounded from 1 through 15
- Result Number lookup uses BHT and attacker count
- die results apply the correct -2, -1, 0, 0, +1, and +2 conversion
- `*` results produce a hit only on a 6
- air-to-air, anti-aircraft, air attack, and surface combat sequencing
- damage application to aircraft, ships, bases, and carried aircraft
- RF, ammunition, and torpedo expenditure
- persistence and replay of the combat event record
