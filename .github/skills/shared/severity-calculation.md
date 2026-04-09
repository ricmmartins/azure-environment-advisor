# Severity & Scoring Calculation

Defines how pillar scores are calculated from findings. Referenced by `azea-assess` and `azea-report`.

---

## Pillar Score Formula

For each of the 6 pillars, calculate a score (0–100%):

1. **Start** at 100%
2. **Subtract** points for each finding in that pillar based on its **profile-adjusted** severity:

| Severity | Points Deducted |
|----------|----------------|
| Critical | -20 |
| High | -12 |
| Medium | -6 |
| Low | -3 |

3. **Floor** at 0% (never go negative)

### Example

A pillar with 1 High finding and 2 Medium findings:
- 100% - 12 - 6 - 6 = **76%**

## Score Color Thresholds

| Score Range | Level | Color |
|-------------|-------|-------|
| 0–40% | Critical | `#d13438` (red) |
| 41–60% | High | `#e97548` (orange) |
| 61–75% | Medium | `#eaa300` (yellow) |
| 76–100% | Pass | `#107c10` (green) |

## Finding Severity Colors

| Severity | Color |
|----------|-------|
| Critical | `#d13438` (red) |
| High | `#e97548` (orange) |
| Medium | `#eaa300` (yellow) |
| Low | `#0078d4` (blue) |
| Pass | `#107c10` (green) |

## Important

> Always use the severity from the **profile's severity adjustment table** (e.g., `profiles/startup.md`), NOT the default severity listed in the rule file. A rule that defaults to "Critical" may be "Medium" for startups.

## SVG Circle Formula

For the pillar score circular progress indicator:

```
stroke-dasharray = (score / 100 * 220) 220
```

Where 220 is the circle circumference (radius ≈ 35, circumference = 2πr ≈ 220).
