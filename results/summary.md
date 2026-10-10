# Blender AI Race: results

Runs: 1, 2, 3 · scenes: 30 (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30) · attempts logged: 385 · total spend: $13.7661

Each cell is the mean across runs, with the min to max range in parentheses when runs differ.

## Overall

| condition | final pass rate | first attempt pass rate | avg attempts | total cost per run | total cost (all runs) | cost per working scene | avg time per scene |
|---|---|---|---|---|---|---|---|
| Opus 5.5 bare | 90% | 90% | 1.00 | $1.84 ($1.77–$1.88) | $5.5184 | $0.0681 ($0.0657–$0.0698) | 24.9s (24.0s–25.5s) |
| Opus 5.5 + harness | 100% | 99% (97%–100%) | 1.01 (1.00–1.03) | $2.50 ($2.46–$2.57) | $7.5029 | $0.0834 ($0.0818–$0.0856) | 26.2s (25.9s–26.7s) |
| Haiku 5.5 bare | 69% (63%–80%) | 69% (63%–80%) | 1.00 | $0.0918 ($0.0888–$0.0934) | $0.2754 | $0.0045 ($0.0037–$0.0049) | 26.1s (25.4s–26.6s) |
| Haiku 5.5 + harness | 100% | 77% | 1.27 (1.23–1.30) | $0.1565 ($0.1531–$0.1602) | $0.4694 | $0.0052 ($0.0051–$0.0053) | 37.2s (36.5s–37.7s) |

## Final pass rate by category

| condition | basic | materials | world | compositor | anim | gn |
|---|---|---|---|---|---|---|
| Opus 5.5 bare | 100% | 100% | 100% | 100% | 100% | 0% |
| Opus 5.5 + harness | 100% | 100% | 100% | 100% | 100% | 100% |
| Haiku 5.5 bare | 90% (80%–100%) | 83% (75%–100%) | 67% (33%–100%) | 11% (0%–33%) | 86% (71%–100%) | 0% |
| Haiku 5.5 + harness | 100% | 100% | 100% | 100% | 100% | 100% |

## Top 5 error messages per condition (all failed attempts, normalized)

### Opus 5.5 bare

| count | error |
|---|---|
| 9 | `TypeError: bpy_struct[key] = val: id properties not supported for this type` |

### Opus 5.5 + harness

| count | error |
|---|---|
| 1 | `[unsafe_code] Unsafe code rejected by the static check: line N: use of '__import__' is not allowed` |

### Haiku 5.5 bare

| count | error |
|---|---|
| 6 | `TypeError: bpy_struct[key] = val: id properties not supported for this type` |
| 4 | `RuntimeError: Error: Object <name> already in collection <name>` |
| 3 | `KeyError: bpy_prop_collection[key]: key "W" not found` |
| 2 | `RuntimeError: Error: Node type CompositorNodeMixRGB undefined` |
| 2 | `TypeError: bpy_struct: item.attr = val: enum "NISHITA" not found in ('SINGLE_SCATTERING', 'MULTIPLE_SCATTERING', 'PREETHAM', 'HOSEK_WILKIE')` |

### Haiku 5.5 + harness

| count | error |
|---|---|
| 3 | `AttributeError: 'Collection' object has no attribute 'link'` |
| 3 | `RuntimeError: Error: Object <name> already in collection <name>` |
| 3 | `[no_code] No ```python code block (or unlabeled ``` code block) was found in the reply. The reply was cut off at the max_tokens limit (N).` |
| 2 | `TypeError: bpy_struct: item.attr = val: enum "NISHITA" not found in ('SINGLE_SCATTERING', 'MULTIPLE_SCATTERING', 'PREETHAM', 'HOSEK_WILKIE')` |
| 2 | `KeyError: bpy_prop_collection[key]: key "W" not found` |

