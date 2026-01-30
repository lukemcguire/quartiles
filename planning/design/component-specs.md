# Quartiles Component Specifications

## Animation Timing & Easing

All animations use consistent timing and easing functions for a cohesive feel.

| Animation | Duration | Easing | Description | CSS Class |
|-----------|----------|--------|-------------|-----------|
| Tile float | 3s | ease-in-out | Subtle up/down idle motion | `animate-float` |
| Tile hover wobble | 300ms | ease-in-out | ±2deg rotation | `animate-wobble` |
| Invalid shake | 300ms | ease-in-out | ±4px horizontal | `animate-shake` |
| Selection ring | 200ms | ease-out | Ring appears with scale | `animate-selection-ring` |
| Word success | 400ms | ease-out | Green flash + fade | `animate-success` |
| Score increment | 200ms | ease-out | Number counts up | `animate-count-up` |
| Completion celebration | 1000ms | spring | Confetti + scale | `animate-scale-up` |
| Pulse glow | 1.5s | ease-in-out infinite | For valid word indication | `animate-pulse-glow` |
| Fade in | 300ms | ease-out | Content appears | `animate-fade-in` |
| Slide up | 400ms | cubic-bezier(0.34, 1.56, 0.64, 1) | Content slides from below | `animate-slide-up` |

## Component States

### Tile Button

The primary interactive element in the game.

**States:**
1. **Default** - Idle with subtle float animation
2. **Hover** - Wobble animation, slight scale increase, elevated shadow
3. **Selected** - Primary color ring (3px), elevated shadow
4. **Quartile Found** - Success tint background (15% success color mixed with base)
5. **Disabled** - Reduced opacity, no pointer events

**Classes:**
- Default: `tile-button animate-float`
- Hover: `tile-button hover:animate-wobble`
- Selected: `tile-button tile-selected`
- Quartile Found: `tile-button tile-quartile-found`
- Disabled: `tile-button opacity-50 pointer-events-none`

**Transitions:** All state changes use 200ms ease-out transition

### Submit Button

Primary action button for submitting word combinations.

**States:**
1. **Default** - Secondary color background, white text
2. **Hover** - Slightly elevated shadow
3. **Disabled** - Muted background, reduced opacity (when no tiles selected)
4. **Loading** - Spinner animation, during API call
5. **Valid Word Pulse** - Optional: pulses when current selection forms valid word

**Classes:**
- Default: `btn btn-secondary`
- Hover: `btn btn-secondary hover:shadow-lg`
- Disabled: `btn btn-secondary btn-disabled`
- Loading: `btn btn-secondary loading`
- Valid Pulse: `btn btn-secondary animate-pulse-glow`

**Validation:** Disable when 0 tiles selected, enable when 1-4 tiles selected

### Clear Button

Secondary action to reset tile selection.

**States:**
1. **Default** - Ghost/outline style
2. **Hover** - Background tint
3. **Disabled** - Hidden when no tiles selected

**Classes:**
- Default: `btn btn-ghost`
- Hover: `btn btn-ghost hover:bg-base-200`
- Disabled: Hidden via conditional rendering

### Hint Button

Triggers hint display with time penalty.

**States:**
1. **Available** - Shows penalty time (+30s)
2. **Active** - Displays hint text
3. **Exhausted** - Disabled when all hints used

**Classes:**
- Available: `btn btn-accent`
- Active: `btn btn-accent btn-active`
- Exhausted: `btn btn-accent btn-disabled`

**Behavior:** Each use adds 30 seconds to completion time

## Word Feedback

### Valid Word

**Visual:**
- Green flash animation (400ms)
- Optional: Confetti particle effects
- Word added to "Found Words" list

**Classes:**
- Animation: `animate-success`
- Background: `bg-success/20`

**Audio:** Subtle success chime (optional)

### Invalid Word

**Visual:**
- Red shake animation (300ms)
- Error message display

**Classes:**
- Animation: `animate-shake`
- Border: `border-error`

**Audio:** Soft error buzz (optional)

### Already Found

**Visual:**
- Yellow/warning indicator
- Message: "Already found!"

**Classes:**
- Background: `bg-warning/20`
- Text: `text-warning`

## Layout Components

### Game Board

Main gameplay area containing the 4x5 tile grid.

**Structure:**
- Header: Score (X/100), Time (M:SS)
- Grid: 4 rows × 5 columns
- Selection Area: Selected tiles display
- Action Buttons: Submit, Clear
- Hint Button: With penalty indicator

**Responsive Breakpoints:**
- Mobile (375px): Full width, stacked layout
- Tablet (768px): Side panel for found words
- Desktop (1024px+): Side panel, larger tiles

**Classes:**
- Container: `container mx-auto px-4`
- Grid: `grid grid-cols-5 gap-2`

### Found Words Panel

Sidebar showing discovered words grouped by tile count.

**Structure:**
```
Found Words (12)
├─ 4-tile (1/5)
│  └─ • QUARTERLY
├─ 3-tile (3)
│  └─ • MASTER
│  └─ • QUARTER
│  └─ • POSITION
└─ 2-tile (5)
   └─ • QU, AR, ...
```

**Classes:**
- Panel: `bg-base-200 rounded-box p-4`
- Section: `mb-4`
- Word: `text-base-content flex items-center gap-2`

### Leaderboard Table

Displays daily rankings with player highlighting.

**Structure:**
- Header: Date, Title
- Table: Rank, Player, Time
- Highlighted Row: Current player

**Classes:**
- Container: `overflow-x-auto`
- Table: `table table-zebra`
- Highlight: `bg-primary/10 row-current`

**States:**
- Top 3: Medal/trophy icons
- Current player: Highlighted row with arrows (◄ YOU ►)

### Game Complete Modal

Results display after reaching 100 points.

**Structure:**
- Celebration animation
- Stats: Time, Score, Rank
- Hints Used: With penalty breakdown
- CTAs: Share Results, Continue Finding

**Classes:**
- Modal: `modal modal-open`
- Content: `modal-box`
- Celebration: `animate-scale-up`

**Buttons:**
- Share: `btn btn-primary`
- Continue: `btn btn-secondary`

## Dark Mode

All components support dark mode via `.dark` class or system preference.

**Key Differences:**
- Backgrounds: Dark charcoal tones
- Text: Warm cream/white
- Primary color: Lightened sage green
- Shadows: Increased opacity
- Grain: Overlay blend mode changes to multiply → overlay

## Accessibility

### Keyboard Navigation

- **Arrow Keys:** Navigate tile grid (up, down, left, right)
- **Vim Keys:** Alternative navigation (h, j, k, l)
- **Space/Enter:** Select/deselect tile
- **Escape:** Clear selection
- **Tab:** Navigate between controls

**Implementation:**
- All interactive elements are focusable
- Visible focus indicators (2px primary ring)
- Logical tab order
- No keyboard traps

### Screen Reader Support

- Tiles: Announce letter content, selection state
- Found words: Announce count, tile count groups
- Score: Announces current/total
- Time: Live region for updates
- Feedback: Aria live regions for word validation

**Aria Labels:**
- Tiles: `aria-label="Tile {letter}, {selected/not selected}"`
- Submit: `aria-label="Submit word, {current selection}"`
- Feedback: `aria-live="polite"` for validation messages

### Focus Management

- Modal opens: Focus trapped in modal
- Modal closes: Focus returns to trigger
- Game complete: Focus on "Share Results" button
- Error messages: Focus on first error

## Responsive Design

### Breakpoints

- **Small:** 375px (mobile phones)
- **Medium:** 768px (tablets)
- **Large:** 1024px (desktop)
- **XL:** 1280px (large desktop)

### Mobile Adaptations

- Tile grid: Maintains 4×5, smaller tiles
- Found words: Moves below grid or to drawer
- Leaderboard: Full width, horizontal scroll
- Time display: Always visible in header

### Touch Targets

- Minimum size: 44×44px (WCAG AA)
- Tiles: Scale to fit, maintain spacing
- Buttons: Full height, adequate padding

## Performance Considerations

### Animation Performance

- Use `transform` and `opacity` only (GPU accelerated)
- Avoid animating `width`, `height`, `margin`, `padding`
- Will-change hint for complex animations
- Respect `prefers-reduced-motion`

### Loading States

- Skeleton screens for slow connections
- Progressive image loading
- Code splitting for routes
- Lazy load leaderboard data

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile Safari: iOS 14+
- Chrome Mobile: Android 10+

Feature detection and fallbacks for older browsers.
