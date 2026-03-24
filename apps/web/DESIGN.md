# Design System — GrounDocs

## Product Context
- **What this is:** A B2B SaaS tool that crawls developer documentation, scores it against 20 AI-readiness rules, and delivers the optimized files as a one-time download.
- **Who it's for:** Developers and developer-tools companies who want their docs to surface in AI agent responses (Claude, GPT, Gemini, etc.)
- **Space/industry:** DevTools / Developer Documentation / AI infrastructure
- **Project type:** Marketing landing page + assessment results SPA
- **Reference peers:** Mintlify, GitBook, ReadMe, Stripe Docs, Linear

---

## Aesthetic Direction
- **Direction:** Precise & Approachable
- **Decoration level:** Intentional — subtle warmth, no gradients, no blobs
- **Mood:** Looks like it was made by engineers who read design books. Authoritative but warm. Documentation quality measurement deserves to feel like a real instrument, not a SaaS landing page. The best-designed thing in the devtools space.
- **Anti-patterns to avoid:**
  - Purple/violet gradients
  - 3-column feature grids with icons in colored circles
  - Generic centered-everything layouts with uniform spacing
  - Uniform bubbly border-radius on all elements
  - "Built for X / Designed for Y" marketing copy
  - Decorative SVG blobs

---

## Typography

- **Display/Hero:** `Instrument Serif` — editorial serif for hero headlines and score numbers. Gives GrounDocs a visual voice. Every score result reads like a grade stamped by an authority, not a dashboard widget. Literally no devtools product uses an editorial serif for their primary display face — this is the biggest visual differentiator.
  - Load via Google Fonts: `Instrument+Serif:ital@0;1`
  - Use for: H1, score numbers, section pull quotes, italic emphasis
  - Weight: 400 (regular + italic — the typeface has no bold)

- **Body/UI:** `Plus Jakarta Sans` — humanist geometric with subtly rounded letterforms. Friendlier than Geist, more distinctive than Inter, without sacrificing readability. Clearly professional.
  - Load via Google Fonts: `Plus+Jakarta+Sans:wght@300;400;500;600;700`
  - Use for: navigation, body copy, buttons, form labels, UI text, H2–H6
  - Weights in use: 400 (body), 500 (medium labels), 600 (semibold headings, buttons)

- **Code/Data:** `Berkeley Mono` (production) — industrial, technically beautiful. Makes scoring UI feel like real measurement, not SaaS dashboard theater.
  - **License:** berkeleygraphics.com/typefaces/berkeley-mono/ (~$75 one-time)
  - **Google Fonts fallback for development:** `JetBrains Mono`
  - Use for: ALL rule names, score numbers in detail views, API output, JSON snippets, badges, timestamps, version numbers, hex colors
  - Weights in use: 400, 500, 700

- **Loading strategy:** Google Fonts with `preconnect` for display + body; Berkeley Mono self-hosted as woff2

- **Type scale (8px base):**
  ```
  Display XL:  54px / 1.0 / Instrument Serif / ls: -0.02em
  H1:          38px / 1.15 / Instrument Serif / ls: -0.01em
  H2:          26px / 1.25 / Plus Jakarta Sans / fw: 600
  H3:          20px / 1.35 / Plus Jakarta Sans / fw: 600
  H4:          17px / 1.4  / Plus Jakarta Sans / fw: 600
  Body LG:     18px / 1.65 / Plus Jakarta Sans / fw: 400
  Body:        16px / 1.65 / Plus Jakarta Sans / fw: 400
  Body SM:     14px / 1.55 / Plus Jakarta Sans / fw: 400
  Code:        13px / 1.6  / Berkeley Mono
  Label:       12px / 1.4  / Plus Jakarta Sans / fw: 500
  Caption:     11px / 1.4  / Berkeley Mono / ls: 0.06em / UPPERCASE
  ```

---

## Color

- **Approach:** Restrained — one accent plus warm neutrals. Color is rare and meaningful.

```css
/* Core */
--bg:            #FAFAF8;   /* barely-warm off-white — not clinical white */
--surface:       #F3F3F0;   /* cards, code regions, slightly deeper */
--surface-2:     #EAEAE6;   /* hover states, inset surfaces */
--border:        #E2E2DC;   /* all borders — warm gray */

/* Text */
--text:          #18181B;   /* near-black with warmth, not #000 */
--text-muted:    #71717A;   /* secondary labels, placeholders */
--text-subtle:   #A1A1AA;   /* captions, disabled states */

/* Brand */
--accent:        #1A7A4C;   /* deep forest green — deeper/richer than current emerald */
--accent-hover:  #145E3A;   /* hover/active */
--accent-light:  #D1F0E1;   /* light tint for pass callouts */

/* Semantic */
--pass:          #1A7A4C;   /* same as accent — cohesion */
--pass-light:    #D1F0E1;
--warn:          #B45309;   /* burnt amber */
--warn-light:    #FEF3C7;
--fail:          #B91C1C;   /* dark brick */
--fail-light:    #FEE2E2;
--info:          #1D4ED8;   /* deep blue — for informational callouts */
--info-light:    #DBEAFE;
```

- **Dark mode:** CSS custom properties override on `[data-theme="dark"]`
  ```css
  --bg:          #111110;
  --surface:     #1A1A18;
  --surface-2:   #242422;
  --border:      #2E2E2C;
  --text:        #F5F5F0;
  --text-muted:  #A1A19A;
  --text-subtle: #6B6B64;
  --accent:      #34C678;   /* lighter green for dark bg contrast */
  --accent-hover:#2DB568;
  ```

- **Shadow system** (warm-tinted, not gray blobs):
  ```css
  --shadow-sm: 0 1px 3px rgba(24,24,27,0.06), 0 1px 2px rgba(24,24,27,0.04);
  --shadow-md: 0 4px 12px rgba(24,24,27,0.08), 0 2px 4px rgba(24,24,27,0.04);
  --shadow-lg: 0 12px 40px rgba(24,24,27,0.10), 0 4px 8px rgba(24,24,27,0.05);
  ```

---

## Spacing

- **Base unit:** 8px
- **Density:** Comfortable (generous on marketing pages, moderate in assessment results)
- **Scale:**
  ```
  2xs:  2px    xs:  4px    sm:   8px   md:  16px
  lg:  24px    xl: 32px   2xl:  48px  3xl:  64px  4xl: 96px
  ```
- **Section padding:** 80px top/bottom on marketing pages, 48px on app pages
- **Max content width:** 1100px (marketing), 1200px (dashboard)
- **Content column:** 740px max for reading text

---

## Layout

- **Approach:** Grid-disciplined for marketing, hybrid for app
- **Grid:** 12 columns
  - Desktop (≥1024px): 12 columns, 24px gap
  - Tablet (768–1023px): 8 columns, 20px gap
  - Mobile (<768px): 4 columns, 16px gap, all sections stack
- **Border radius — hierarchical:**
  ```
  --radius-sm:   4px    /* inputs, badges, small elements */
  --radius-md:   8px    /* buttons, cards, form containers */
  --radius-lg:  12px    /* modals, panels, large cards */
  --radius-xl:  16px    /* hero form containers */
  --radius-full: 9999px /* pills, circular avatars */
  ```
- **Rule: border-radius matches visual weight.** Small elements have small radii. Don't apply the same radius to a badge and a modal.

---

## Motion

- **Approach:** Intentional — every animation has a reason
- **Easing:**
  - Enter: `cubic-bezier(0, 0, 0.2, 1)` (ease-out)
  - Exit: `cubic-bezier(0.4, 0, 1, 1)` (ease-in)
  - Move: `cubic-bezier(0.4, 0, 0.2, 1)` (ease-in-out)
- **Duration:**
  ```
  micro:   50–100ms   /* hover color changes, focus rings */
  short:   150–200ms  /* button transitions, badge changes */
  medium:  250–350ms  /* modals, drawers, tooltips */
  long:    400–600ms  /* page transitions, score reveal */
  ```
- **Score reveal:** When the score number first appears, count up from 0 to the final value over 800ms with ease-out. This is the only "theatrical" animation — everything else is functional.
- **Never:** Bouncing, spinning loaders on complete data, scroll-triggered carousels, animations >700ms on interactive elements

---

## Component Patterns

### Semantic callouts (pass/warn/fail/info)
```
border-left: 3px solid [semantic color]
background:  [semantic light variant]
color:       [semantic color]
padding:     12px 16px
border-radius: var(--radius-md)
icon:        ▪ (filled square, Berkeley Mono)
```

### Score number display
```
font-family: Instrument Serif
font-size:   108px (results page), 54px (summary cards)
color:       var(--pass) if ≥70, var(--warn) if 40–69, var(--fail) if <40
```

### Rule list items
```
background: var(--surface)
border: 1px solid var(--border)
border-radius: var(--radius-md)
rule name: Berkeley Mono, 12px
indicator: 8px × 8px, border-radius: 2px, semantic color fill
```

---

## CLAUDE SUBAGENT VOICES (for reference)
The outside voices produced these alternative directions during the design consultation:

**Claude subagent (bolder option):** Full warm parchment (#F5F0E8), Tiempos Headline (requires license), Berkeley Mono. More editorial, more distinctive, riskier. "A research instrument that got good at design." If GrounDocs wants to go bolder in a future iteration, this is the direction.

**Research synthesis:** The devtools space converges entirely on Inter/Geist + white + blue. Typography differentiation has the highest ROI. Micro-interactions matter more than most teams realize. Warm off-white + serif headlines + Berkeley Mono for data is the gap nobody is occupying.

---

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-24 | Instrument Serif for display | No devtools product uses editorial serif — instant visual signature |
| 2026-03-24 | Plus Jakarta Sans for body/UI | More distinctive than Inter/Geist without sacrificing professionalism |
| 2026-03-24 | Berkeley Mono for all data/code | Creates "measurement" visual language competitors lack |
| 2026-03-24 | #FAFAF8 background | Warm off-white separates from every clinical-white Mintlify clone |
| 2026-03-24 | #1A7A4C brand green | Deeper/richer evolution of existing emerald — brand continuity + distinctiveness |
| 2026-03-24 | Score as Instrument Serif number | Reads like authoritative grade, not dashboard widget |
| 2026-03-24 | Intentional motion only | Fast, purposeful animations build developer trust; bouncy/theatrical kills it |
| 2026-03-24 | Created by /design-consultation | Based on competitive research (Mintlify, Vercel, Linear, Stripe, GitBook, ReadMe) + Claude subagent outside voice |
