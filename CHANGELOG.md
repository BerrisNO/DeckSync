# Changelog

## 0.3.0 — 2026-10-08

First public release.

- Renamed from Tandem to DeckSync (`no.berland.decksync`).
- Generated profiles per device type (Stream Deck, Mini, XL, +, Neo) with a page marker on every page, Next/Previous keys and a page dial on Stream Deck +.
- First-run install: each new deck is switched to its DeckSync profile once, one device at a time.
- Actions: Page marker, Page indicator, Go to page, Page dial, Target.
- Custom deck names, shared by all dials and Target keys.
- Page names read from the Stream Deck app's profiles, shown on markers, the dial and in Go to page.
- Page markers rendered as images (page name large, "p3" small); custom touch-strip layout for the dial.
- English user interface; icons and Marketplace images.

## 0.2.0 — 2026-10-08

- Bundled user-exported profiles, `Profiles` block in the manifest.
- Fixed start-up crash (esbuild ESM bundle needed `createRequire` for `ws`).
- Go to page action with fixed fields for the 15-key deck and Stream Deck +.

## 0.1.0 — 2026-10-08

- Initial Tandem prototype: page marker action and sync logic, simulated only.
