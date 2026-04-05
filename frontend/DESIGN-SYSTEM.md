# Arkiv Design System — "Quiet Library"

Soft pastel, minimal, cozy. Like a reading nook with warm afternoon light.

---

## Color Palette

### Light Mode

| Role             | Token                | Hex       |
| ---------------- | -------------------- | --------- |
| Background       | `--background`       | `#FAF8F5` |
| Surface (cards)  | `--card`             | `#F3F0EB` |
| Border           | `--border`           | `#E2DDD5` |
| Text muted       | `--muted-foreground` | `#8C8279` |
| Text primary     | `--foreground`       | `#2C2520` |
| Accent (CTA)     | `--primary`          | `#C48B7C` |
| Accent hover     | —                    | `#A8705F` |
| Accent text      | `--primary-foreground` | `#FFFAF8` |
| Success          | —                    | `#7D9E82` |
| Warning          | —                    | `#C9A96E` |
| Error/destructive| `--destructive`      | `#C4645A` |
| Info             | —                    | `#7B9EB5` |

### Dark Mode

| Role             | Hex       |
| ---------------- | --------- |
| Background       | `#1A1614` |
| Surface          | `#252019` |
| Border           | `#3D352C` |
| Text muted       | `#9B8E82` |
| Text primary     | `#E8E2DA` |
| Accent           | `#D4A08F` |
| Accent text      | `#1A1614` |

---

## Typography

| Role           | Font            | Weight  | Notes                     |
| -------------- | --------------- | ------- | ------------------------- |
| Headlines      | Lora (serif)    | 500-700 | Bookish, warm, literary   |
| Body / UI      | Nunito Sans     | 400-600 | Rounded, soft, readable   |

- Scale: 1.25x major third
- Base: 16px (1rem)
- Headlines: tighter tracking (-0.02em)
- Body line-height: 1.5

---

## Spacing

Base unit: 4px. Scale: 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96px.
Generous negative space throughout — the UI should breathe.

---

## Animation

- UI interactions: 200ms ease-out
- State changes: 300ms ease-out
- Page transitions: subtle fades, not slides
- Philosophy: felt, not seen

---

## Key Component Notes

- **Book covers**: hero element, large, warm subtle shadows
- **Rating stars**: filled with dusty rose, unfilled in border color
- **Navbar**: minimal, blends into background
- **Filters**: pill-shaped toggles, soft borders
- **Danger actions**: soft brick text, no fill, requires confirmation
- **Empty states**: warm conversational copy
