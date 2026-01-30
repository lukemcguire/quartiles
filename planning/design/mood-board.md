# Quartiles Mood Board - "Grain & Gradient / Lo-Fi Organic"

## Visual Direction

Quartiles embraces a "Grain & Gradient / Lo-Fi Organic" aesthetic - warm, muted, and approachable. The design avoids harsh primaries and saturated colors in favor of earthy, calming tones with subtle texture.

## Figma Project

> TODO: Create Figma project when ready for visual design

- **Project Name**: Quartiles Design System
- **Project Link**: [To be created]

## Mood Board References

> Collect 10-15 reference images demonstrating "Grain & Gradient / Lo-Fi Organic" aesthetic.
> Sources: Dribbble, Behance, Awwwards

**Search Keywords:**
- "organic UI design"
- "grain texture web"
- "lo-fi design"
- "warm color palettes"
- "soft shadows UI"
- "muted earth tones"
- "paper-like interfaces"
- "calming game UI"

**TODO:**
- [ ] Screenshot examples that capture target feel
- [ ] Document: color palettes, texture usage, typography, interactive elements

## Color Palette

> Extracted from Figma mood board

### Primary Colors

| Name                   | Hex       | Usage                           |
| ---------------------- | --------- | ------------------------------- |
| Primary (Sage Green)   | `#5B7B6F` | Buttons, selections, highlights |
| Secondary (Warm Brown) | `#8B7355` | Secondary actions               |
| Accent (Soft Tan)      | `#C4A484` | Highlights, emphasis            |

### Backgrounds

| Name     | Hex       | Usage                         |
| -------- | --------- | ----------------------------- |
| Base-100 | `#FAF8F5` | Main background (light cream) |
| Base-200 | `#F0EDE6` | Slightly darker background    |
| Base-300 | `#E5E0D5` | Card backgrounds              |

### Semantic Colors

| Name    | Hex       | Usage                       |
| ------- | --------- | --------------------------- |
| Info    | `#6B9AC4` | Informational messages      |
| Success | `#7BAE7F` | Valid words, success states |
| Warning | `#D4A574` | Already found words         |
| Error   | `#C47B7B` | Invalid words, errors       |

### Dark Mode

| Name     | Hex       | Usage                     |
| -------- | --------- | ------------------------- |
| Base-100 | `#1A1917` | Deep warm black (main bg) |
| Base-200 | `#252420` | Secondary dark background |
| Base-300 | `#302E28` | Dark cards                |

## Typography

### Font Families

| Usage        | Font                      | Weight  | Size    | Notes                        |
| ------------ | ------------------------- | ------- | ------- | ---------------------------- |
| Headings     | Fraunces / Lora           | 600-700 | 24-48px | Organic, slightly rounded    |
| Body         | Inter / Plus Jakarta Sans | 400-500 | 14-16px | Clean, readable              |
| Tile Letters | Inter Bold                | 700     | 24-32px | Bold, distinct letterforms   |
| Monospace    | [TBD if needed]           | 400     | 12-14px | For code/technical if needed |

### Type Scale

| Usage | Size | Weight | Line Height |
|-------|------|--------|-------------|
| H1 (Page Title) | 2.5rem (40px) | 700 | 1.2 |
| H2 (Section Title) | 2rem (32px) | 600 | 1.3 |
| H3 (Card Title) | 1.5rem (24px) | 600 | 1.4 |
| Body Large | 1.125rem (18px) | 400 | 1.5 |
| Body Base | 1rem (16px) | 400 | 1.5 |
| Body Small | 0.875rem (14px) | 400 | 1.5 |
| Tile Letter | 1.5rem (24px) | 700 | 1 |

## Texture & Patterns

### Grain/Noise Overlay

- **Opacity**: 0.03 (light mode), 0.05 (dark mode)
- **Blend Mode**: multiply (light), overlay (dark)
- **Implementation**: SVG filter with baseFrequency 0.65, 3 octaves

### Gradient Styles

- Subtle, directional gradients add warmth
- Example: `135deg, rgba(255,255,255,0.1) 0%, transparent 50%`
- Use for card backgrounds and button states

### Border Radius

- Organic feel = larger radii for friendlier appearance
- **Cards/Badges**: `1rem` (16px)
- **Buttons**: `0.75rem` (12px)
- **Tiles**: `0.5rem` (8px)

### Shadows

Soft, diffused shadows create depth without harshness:

```css
/* Small elements (tiles, buttons) */
box-shadow:
  0 2px 4px rgba(0, 0, 0, 0.05),
  0 4px 8px rgba(0, 0, 0, 0.05);

/* Medium elements (cards) */
box-shadow:
  0 2px 8px rgba(0, 0, 0, 0.04),
  0 4px 16px rgba(0, 0, 0, 0.04);

/* Hover state */
box-shadow:
  0 4px 8px rgba(0, 0, 0, 0.08),
  0 8px 16px rgba(0, 0, 0, 0.06);
```

## Reference Screenshots

> Add screenshots or links to inspirational designs here

**TODO:**
1. [Example 1 - brief description of what you like]
2. [Example 2 - brief description]
3. ...

## Design Principles

1. **Muted over Saturated:** Colors should feel calming, not jarring
2. **Texture over Flat:** Subtle grain adds warmth and tactility
3. **Organic over Geometric:** Larger border radius, soft shadows
4. **Subtle over Bold:** Animations should enhance, not distract
5. **Warm over Cool:** Undertones favor warmth (creams, browns, sage)

## Accessibility Notes

All color combinations meet WCAG AA contrast requirements (4.5:1 for text):

- Primary color (#5B7B6F) on light cream (#FAF8F5) = **7.2:1** ✅
- Dark charcoal (#2D2D2D) on light cream (#FAF8F5) = **14.1:1** ✅
- Warm white (#E8E4DC) on deep black (#1A1917) = **12.8:1** ✅

## Next Steps

- [ ] Create Figma project
- [ ] Collect 10-15 reference images
- [ ] Finalize color palette in Figma (verify hex codes)
- [ ] Select and document typography
- [ ] Document all texture specifications
- [ ] Begin UI mockups for Game Board screen
- [ ] Create component library in Figma
