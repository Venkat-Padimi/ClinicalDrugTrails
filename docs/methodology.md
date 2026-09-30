# Methodology & Mathematical Formulations

This document provides complete transparency into the deterministic equations and decision rules implemented across the platform.

---

## 1. Patient Eligibility Evaluation Logic

For each candidate patient $p$ and trial protocol $T$:
- Each **Inclusion Criterion** $C_{\text{inc}} \in T_{\text{inc}}$ is evaluated.
  - If a mandatory field $f$ is absent or null in $p$, criterion is marked `MISSING`.
  - If field is present but condition is unmet, criterion is marked `FAILED`.
- Each **Exclusion Criterion** $C_{\text{exc}} \in T_{\text{exc}}$ is evaluated.
  - If condition is met (e.g. prohibited co-medication present), exclusion is `TRIGGERED`.

### Decision Matrix:
$$\text{Status}(p) = \begin{cases} 
\text{INELIGIBLE}, & \text{if } |C_{\text{triggered}}| > 0 \text{ or } |C_{\text{failed}}| > 0 \\
\text{UNCERTAIN}, & \text{if } |C_{\text{missing}}| > 0 \text{ and } |C_{\text{triggered}}| = 0 \text{ and } |C_{\text{failed}}| = 0 \\
\text{ELIGIBLE}, & \text{otherwise}
\end{cases}$$

---

## 2. Site Operational Intelligence Scoring

All operational dimensions are normalized to $[0, 100]$:

1. **Enrollment Velocity Score**:
   $$S_{\text{vel}} = \min\left(100, \frac{\text{Average Monthly Enrollment}}{5.0} \times 100\right)$$

2. **Experience Score**:
   $$S_{\text{exp}} = 0.5 \times \min\left(100, \frac{\text{TA Exp Yrs}}{15.0} \times 100\right) + 0.5 \times \min\left(100, \frac{\text{Investigator Exp Yrs}}{18.0} \times 100\right)$$

3. **Compliance Score**:
   $$S_{\text{comp}} = \max\left(0, \min\left(100, 100 - (\text{Protocol Deviation Rate} \times 30.0)\right)\right)$$

4. **Data Quality Score**:
   $$S_{\text{dq}} = \max\left(0, \min\left(100, 100 - \frac{\text{Query Rate} - 0.5}{2.5} \times 60.0\right)\right)$$

5. **Operational Efficiency Score**:
   $$S_{\text{ops}} = 0.35 \times S_{\text{screen\_fail}} + 0.35 \times S_{\text{dropout}} + 0.30 \times S_{\text{activation}}$$

6. **Capacity Score**:
   $$S_{\text{cap}} = 0.5 \times \min\left(100, \frac{\text{Staff}}{10} \times 100\right) + 0.5 \times \min\left(100, \frac{\text{Patient Pool}}{500} \times 100\right)$$

---

## 3. Site Multi-Dimensional Risk Assessment

Evaluates 6 specific risk dimensions:
1. **Recruitment Risk** ($R_{\text{rec}}$)
2. **Compliance Risk** ($R_{\text{comp}}$)
3. **Data Quality Risk** ($R_{\text{dq}}$)
4. **Investigator Experience Risk** ($R_{\text{exp}}$)
5. **Operational Risk** ($R_{\text{ops}}$)
6. **Capacity & Activation Risk** ($R_{\text{cap\_act}}$)

### Overall Risk Formula:
$$\text{Overall Risk} = w_1 R_{\text{rec}} + w_2 R_{\text{comp}} + w_3 R_{\text{dq}} + w_4 R_{\text{exp}} + w_5 R_{\text{ops}} + w_6 R_{\text{cap\_act}}$$

Default weights:
- $w_1 = 0.25$ (Recruitment)
- $w_2 = 0.20$ (Compliance)
- $w_3 = 0.15$ (Data Quality)
- $w_4 = 0.15$ (Experience)
- $w_5 = 0.15$ (Operational)
- $w_6 = 0.10$ (Capacity/Activation)

Risk Classification:
- $\text{Overall Risk} < 28.0$: `LOW`
- $28.0 \le \text{Overall Risk} < 48.0$: `MEDIUM`
- $48.0 \le \text{Overall Risk} < 65.0$: `HIGH` (Escalated to Human Review)
- $\text{Overall Risk} \ge 65.0$ or $\ge 2$ Critical Deviations: `CRITICAL` (Mandatory Escalate)

---

## 4. Multi-Criteria Site Prioritization (MCDA)

$$S_{\text{base}} = 0.30 S_{\text{vel}} + 0.20 S_{\text{ops}} + 0.20 S_{\text{exp}} + 0.15 S_{\text{dq}} + 0.15 S_{\text{comp}}$$

$$\text{Risk Penalty} = \left(\frac{\text{Overall Risk}}{100.0}\right) \times 25.0$$

$$\text{Priority Score} = \max(0.0, \min(100.0, S_{\text{base}} - \text{Risk Penalty}))$$

Sites are sorted in descending order of Priority Score and assigned sequential ranks $1, \dots, N$.

---

## 5. Recruitment Forecasting & Uncertainty Bounds

Accounting for friction from screen failures and patient dropout:
$$\text{Effective Target} = \frac{\text{Target Enrollment}}{1 - \text{Average Dropout Rate}}$$
$$\text{Expected Monthly} = \left(\sum_{s} \text{Velocity}_s\right) \times (1.0 - 0.5 \times \text{Average Screen Failure Rate})$$

$$\text{P50 Time (Months)} = \frac{\text{Effective Target}}{\text{Expected Monthly}}$$
$$\text{P10 Time (Optimistic)} = \text{P50} \times 0.75$$
$$\text{P90 Time (Conservative)} = \text{P50} \times 1.35$$
