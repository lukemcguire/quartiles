# Section 02: Design Foundation (Figma + Theme)

## Background

Quartiles is a daily word puzzle game with a distinctive visual identity: "Grain & Gradient / Lo-Fi Organic" aesthetic. Before implementing any UI components, we must establish a solid design foundation that translates into concrete design tokens, component specifications, and a daisyUI theme configuration.

This section ensures that:
1. Visual direction is established through research and mood boards
2. All game screens are fully mocked in Figma before coding begins
3. The daisyUI theme captures the exact colors, typography, and styling
4. Animation specifications are documented for consistent implementation

**Why this matters:** Starting UI implementation without a design foundation leads to inconsistent visuals, repeated refactoring, and a disjointed user experience. By completing design work first, frontend developers have clear specifications to implement.

---

## Dependencies

```yaml
requires:
  - "01"  # Codebase Cleanup - ensures clean slate for new frontend work
blocks:
  - "05"  # Database Models - (indirect, through overall project flow)
  - "06"  # Game API - (indirect, through overall project flow)
  - "07"  # Frontend Game UI - directly needs theme and mockups
```

**Why Section 01 first:** The cleanup phase removes scaffolding code (shadcn/ui components, placeholder routes) that would conflict with the new daisyUI-based design system.

**Why blocks Section 07:** Frontend implementation cannot begin until the design system (colors, components, animations) is defined. Building UI without these specifications results in rework.

---

## Requirements

When this section is complete, the following must be true:

### Design Research Complete
- [ ] Mood board with 10-15 reference images demonstrating "Grain & Gradient / Lo-Fi Organic" aesthetic
- [ ] Documented color palette with hex codes (primary, secondary, accent, backgrounds, semantic colors)
- [ ] Typography selection with rationale (heading font, body font, monospace for letter tiles)
- [ ] Texture/pattern specifications (grain overlays, noise effects, gradient styles)

### Figma Mockups Complete
- [ ] Game Board screen (main gameplay view)
- [ ] Leaderboard screen (today's rankings)
- [ ] Game Complete screen (final results)
- [ ] All component states documented (hover, selected, disabled, success, error)
- [ ] Dark mode variants for all screens
- [ ] Mobile responsive layouts (375px, 768px, 1024px breakpoints)
- [ ] Animation specifications documented (timing, easing, keyframes)

### daisyUI Theme Configured
- [ ] Custom `quartiles` theme defined in `tailwind.config.js`
- [ ] Custom `quartiles-dark` theme defined for dark mode
- [ ] All semantic color tokens mapped from Figma design
- [ ] Custom CSS for grain/texture effects created
- [ ] Theme toggle functionality verified

---

## Implementation Details

### 0.1 Design Research

**Objective:** Establish visual direction for the "Grain & Gradient / Lo-Fi Organic" aesthetic

**Research Tasks:**

1. **Collect Reference Material**
   - Search Dribbble, Behance, Awwwards for "organic UI", "grain texture web", "lo-fi design"
   - Screenshot 10-15 examples that capture the target feel
   - Focus on: color palettes, texture usage, typography, interactive elements

2. **Define Color Palette**
   - Muted, earthy tones (not saturated primary colors)
   - Example direction:
     - Backgrounds: warm off-whites, soft creams, muted grays
     - Primary: desaturated teal, olive, or terracotta
     - Accent: soft coral, dusty pink, or sage green
     - Dark mode: deep charcoals with warm undertones
   - Document all colors with hex codes and usage guidelines

3. **Select Typography**
   - Heading font: organic, slightly rounded (e.g., Fraunces, Lora, or similar)
   - Body font: clean, readable sans-serif (e.g., Inter, Plus Jakarta Sans)
   - Tile letters: bold, distinct letterforms (consider monospace or display font)
   - Document font sizes, weights, and line heights

4. **Document Texture Patterns**
   - Grain/noise overlay specifications (opacity, blend mode)
   - Gradient styles (subtle, directional, color stops)
   - Border radius conventions (organic = larger radii)
   - Shadow styles (soft, diffused, not harsh)

**Deliverables:**
- Figma mood board page with annotated references
- Design tokens document (can be in Figma or separate markdown)

### 0.2 UI Mockups

**Objective:** Complete high-fidelity mockups for all game screens before implementation

#### Screen 1: Game Board (Main Gameplay)

**Layout:**
```
┌─────────────────────────────────────────────┐
│  Score: 45/100          Time: 3:42          │
├─────────────────────────────────────────────┤
│                                             │
│   ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐       │
│   │ QU │ │ AR │ │ TER│ │ LY │ │ ES │       │
│   └────┘ └────┘ └────┘ └────┘ └────┘       │
│   ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐       │
│   │ MA │ │ ST │ │ ER │ │ FUL│ │ LY │       │
│   └────┘ └────┘ └────┘ └────┘ └────┘       │
│   ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐       │
│   │ PRO│ │ PO │ │ SI │ │ TI │ │ ON │       │
│   └────┘ └────┘ └────┘ └────┘ └────┘       │
│   ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐       │
│   │ UN │ │ DE │ │ RS │ │ TA │ │ ND │       │
│   └────┘ └────┘ └────┘ └────┘ └────┘       │
│                                             │
├─────────────────────────────────────────────┤
│  Selected: [ QU ][ AR ][ TER ]              │
│  ┌─────────┐  ┌─────────┐                   │
│  │ Submit  │  │  Clear  │                   │
│  └─────────┘  └─────────┘                   │
├─────────────────────────────────────────────┤
│  ┌─ Hint (+30s) ─┐                          │
│  └───────────────┘                          │
└─────────────────────────────────────────────┘

Sidebar (desktop):
┌─────────────────┐
│ Found Words (12)│
├─────────────────┤
│ 4-tile (1/5)    │
│  • QUARTERLY    │
├─────────────────┤
│ 3-tile (3)      │
│  • MASTER       │
│  • QUARTER      │
│  • POSITION     │
├─────────────────┤
│ 2-tile (5)      │
│  • QU, AR, ...  │
└─────────────────┘
```

**Design Notes:**
- Tiles have subtle grain texture
- Selected tiles glow with primary color ring
- Quartile-found tiles have success background tint
- Gentle floating animation on idle tiles
- Submit button pulses when word is valid

#### Screen 2: Leaderboard

**Layout:**
```
┌─────────────────────────────────────────────┐
│           Today's Leaderboard               │
│              January 27, 2026               │
├─────────────────────────────────────────────┤
│  Rank    Player              Time           │
├─────────────────────────────────────────────┤
│   1      ChubbyPenguin       2:34           │
│   2      SleepyMango         2:51           │
│   3      FluffyNarwhal       3:02           │
│  ...                                        │
│  47 ►    YOU (DapperWalrus)  4:23 ◄         │
│  ...                                        │
└─────────────────────────────────────────────┘
```

**Design Notes:**
- Current player row highlighted with subtle background
- Top 3 may have medal/trophy icons
- Time format: M:SS
- Scrollable list with sticky header

#### Screen 3: Game Complete

**Layout:**
```
┌─────────────────────────────────────────────┐
│                                             │
│           🎉 Puzzle Complete! 🎉            │
│                                             │
│         Your Time: 4:23                     │
│         Final Score: 127 points             │
│         Rank: #47 of 1,234                  │
│                                             │
│         Hints Used: 1 (+30s penalty)        │
│                                             │
│    ┌──────────────────────────────────┐     │
│    │        Share Results 📤         │     │
│    └──────────────────────────────────┘     │
│                                             │
│    ┌──────────────────────────────────┐     │
│    │      Continue Finding Words      │     │
│    └──────────────────────────────────┘     │
│                                             │
└─────────────────────────────────────────────┘
```

**Design Notes:**
- Celebration animation on completion
- Share button generates text summary for clipboard
- "Continue" allows relaxed play without affecting score

#### Component States

Document in Figma for each interactive element:

**Tile Button:**
- Default (idle with float animation)
- Hover (wobble animation, slight scale)
- Selected (primary ring, elevated shadow)
- Quartile Found (success tint background)
- Disabled (reduced opacity)

**Submit Button:**
- Default
- Hover
- Disabled (when no tiles selected)
- Loading (during API call)
- Valid Word Pulse (when current selection forms valid word - optional enhancement)

**Word Feedback:**
- Valid word (green flash, confetti particles)
- Invalid word (red shake animation)
- Already found (yellow/warning indicator)

**Hint Button:**
- Available (shows penalty time)
- Used (shows hint text)
- Exhausted (disabled, all hints used)

#### Animation Specifications

Document timing and easing for consistency:

| Animation | Duration | Easing | Description |
|-----------|----------|--------|-------------|
| Tile float | 3s | ease-in-out | Subtle up/down idle motion |
| Tile hover wobble | 300ms | ease-in-out | ±2deg rotation |
| Invalid shake | 300ms | ease-in-out | ±4px horizontal |
| Selection ring | 200ms | ease-out | Ring appears with scale |
| Word success | 400ms | ease-out | Green flash + fade |
| Score increment | 200ms | ease-out | Number counts up |
| Completion celebration | 1000ms | spring | Confetti + scale |

### 0.3 daisyUI Theme Configuration

**Objective:** Translate Figma design tokens into daisyUI theme

#### Theme Definition

**File:** `frontend/tailwind.config.js`

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      // Custom animations
      animation: {
        'float': 'float 3s ease-in-out infinite',
        'wobble': 'wobble 0.3s ease-in-out',
        'shake': 'shake 0.3s ease-in-out',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-2px)' },
        },
        wobble: {
          '0%, 100%': { transform: 'rotate(0deg)' },
          '25%': { transform: 'rotate(-2deg)' },
          '75%': { transform: 'rotate(2deg)' },
        },
        shake: {
          '0%, 100%': { transform: 'translateX(0)' },
          '25%': { transform: 'translateX(-4px)' },
          '75%': { transform: 'translateX(4px)' },
        },
      },
    },
  },
  plugins: [require('daisyui')],
  daisyui: {
    themes: [
      {
        quartiles: {
          // Primary action color (buttons, selections)
          "primary": "#5B7B6F",          // Sage green (REPLACE with Figma value)
          "primary-content": "#FFFFFF",

          // Secondary actions
          "secondary": "#8B7355",         // Warm brown (REPLACE with Figma value)
          "secondary-content": "#FFFFFF",

          // Accent highlights
          "accent": "#C4A484",            // Soft tan (REPLACE with Figma value)
          "accent-content": "#1F1F1F",

          // Neutral (text, borders)
          "neutral": "#3D3D3D",
          "neutral-content": "#F5F2EB",

          // Base backgrounds
          "base-100": "#FAF8F5",          // Light cream (main bg)
          "base-200": "#F0EDE6",          // Slightly darker
          "base-300": "#E5E0D5",          // Card backgrounds
          "base-content": "#2D2D2D",      // Main text

          // Semantic colors
          "info": "#6B9AC4",
          "success": "#7BAE7F",
          "warning": "#D4A574",
          "error": "#C47B7B",

          // Border radius (organic = rounder)
          "--rounded-box": "1rem",
          "--rounded-btn": "0.75rem",
          "--rounded-badge": "1rem",

          // Animation
          "--animation-btn": "0.2s",
          "--animation-input": "0.2s",

          // Focus ring
          "--btn-focus-scale": "0.98",
        },
        "quartiles-dark": {
          // Dark mode - warm charcoals
          "primary": "#7B9B8F",
          "primary-content": "#1A1A1A",

          "secondary": "#AB9375",
          "secondary-content": "#1A1A1A",

          "accent": "#D4B494",
          "accent-content": "#1A1A1A",

          "neutral": "#9D9D9D",
          "neutral-content": "#1A1A1A",

          "base-100": "#1A1917",          // Deep warm black
          "base-200": "#252420",
          "base-300": "#302E28",
          "base-content": "#E8E4DC",

          "info": "#8BBAE4",
          "success": "#9BCE9F",
          "warning": "#E4C594",
          "error": "#E49B9B",

          "--rounded-box": "1rem",
          "--rounded-btn": "0.75rem",
          "--rounded-badge": "1rem",
          "--animation-btn": "0.2s",
          "--animation-input": "0.2s",
          "--btn-focus-scale": "0.98",
        },
      },
    ],
    darkTheme: "quartiles-dark",
  },
}
```

#### Custom CSS for Grain/Texture

**File:** `frontend/src/styles/theme.css`

```css
/* Grain texture overlay */
.grain-overlay {
  position: relative;
}

.grain-overlay::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  opacity: 0.03;
  pointer-events: none;
  mix-blend-mode: multiply;
}

/* Tile-specific styling */
.tile-button {
  /* Organic shadow */
  box-shadow:
    0 2px 4px rgba(0, 0, 0, 0.05),
    0 4px 8px rgba(0, 0, 0, 0.05);

  /* Subtle grain on tiles */
  background-image:
    linear-gradient(135deg, rgba(255,255,255,0.1) 0%, transparent 50%),
    url("data:image/svg+xml,..."); /* noise pattern */
}

.tile-button:hover {
  box-shadow:
    0 4px 8px rgba(0, 0, 0, 0.08),
    0 8px 16px rgba(0, 0, 0, 0.06);
}

/* Selected tile glow */
.tile-selected {
  box-shadow:
    0 0 0 3px var(--p),
    0 4px 12px rgba(91, 123, 111, 0.3);
}

/* Success state for quartile tiles */
.tile-quartile-found {
  background-color: color-mix(in srgb, var(--su) 15%, var(--b1));
}
```

#### Index CSS Updates

**File:** `frontend/src/index.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Import custom theme styles */
@import './styles/theme.css';
@import './styles/animations.css';

/* Base styling */
html {
  scroll-behavior: smooth;
}

body {
  @apply bg-base-100 text-base-content;
  font-family: 'Inter', system-ui, sans-serif;
}

/* Optional: Add grain to main content area */
#root {
  @apply grain-overlay;
}
```

---

## Files to Create/Modify

### Files to Create

| File | Purpose |
|------|---------|
| `frontend/src/styles/theme.css` | Custom CSS for grain textures, tile styling, organic shadows |
| `frontend/src/styles/animations.css` | Keyframe animations (float, wobble, shake, success) |
| `planning/design/mood-board.md` | Links to Figma, color tokens, typography specs |
| `planning/design/component-specs.md` | Animation timing, state documentation |

### Files to Modify

| File | Changes |
|------|---------|
| `frontend/tailwind.config.js` | Add daisyUI plugin, custom themes, animation keyframes |
| `frontend/src/index.css` | Import new style files, add base styling |
| `frontend/package.json` | Add daisyUI dependency |

### Figma Deliverables (External)

| Page | Contents |
|------|----------|
| Mood Board | 10-15 reference images, annotated |
| Design Tokens | Color palette, typography scale, spacing |
| Game Board | Desktop + mobile layouts, all states |
| Leaderboard | Ranking table, player highlight |
| Game Complete | Results display, share CTA |
| Component Library | Buttons, tiles, cards, inputs |

---

## Acceptance Criteria

### Design Research
- [ ] Mood board created with 10+ reference images
- [ ] Color palette documented (minimum 12 colors: primary, secondary, accent, neutral, base-100/200/300, info, success, warning, error)
- [ ] Typography selected and documented (heading, body, monospace)
- [ ] Texture specifications documented (grain opacity, blend modes)

### Figma Mockups
- [ ] Game Board screen complete (desktop)
- [ ] Game Board screen complete (mobile 375px)
- [ ] Leaderboard screen complete
- [ ] Game Complete screen complete
- [ ] All tile states documented (default, hover, selected, quartile-found, disabled)
- [ ] All button states documented
- [ ] Animation specifications table complete
- [ ] Dark mode variants for all screens

### daisyUI Theme
- [ ] `quartiles` theme defined in tailwind.config.js
- [ ] `quartiles-dark` theme defined in tailwind.config.js
- [ ] daisyUI added to package.json dependencies
- [ ] Custom animations (float, wobble, shake) defined
- [ ] Grain texture CSS created
- [ ] Theme renders correctly in browser (both light and dark)

### Verification Steps
```bash
# 1. Install dependencies
cd frontend && npm install

# 2. Start dev server
npm run dev

# 3. Verify theme loads
# - Open http://localhost:5173
# - Check browser dev tools for daisyUI classes
# - Toggle dark mode (if implemented)

# 4. Run lint checks
npm run lint
```

---

## Notes

### Design-First Principle

This section enforces a design-first workflow. Resist the temptation to "just start coding" - time invested in design pays dividends:
- Fewer revisions during implementation
- Consistent visual language
- Better accessibility (colors checked in Figma)
- Smoother handoff between design and code

### Color Value Placeholders

The color values in the theme configuration above are placeholders. During implementation:
1. Finalize colors in Figma mood board
2. Extract exact hex values
3. Update `tailwind.config.js` with final values
4. Verify contrast ratios meet WCAG AA (4.5:1 for text)

### daisyUI Version

Use daisyUI v4.x. The theme configuration syntax may differ in other versions. Check the [daisyUI documentation](https://daisyui.com/docs/themes/) for your installed version.

### Mobile-First Approach

While the wireframes above show desktop layouts, design mobile screens first in Figma:
- 375px (small phones)
- Then expand to 768px (tablets)
- Then 1024px+ (desktop)

The 4x5 tile grid should remain usable on small screens - consider tile size and touch targets (minimum 44x44px).
