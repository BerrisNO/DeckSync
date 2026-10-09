# Changelog

## 0.3.0 — 2026-10-09

First public release.

- Follow mode: a page marker on every page keeps all decks on the same page.
- Actions: Page marker, Page indicator, Page step, Go to page, Page dial, Target.
- Page step keys for decks without a dial; Go to page for all decks or one page per connected deck.
- Page dial for Stream Deck +: turn to pick, press to go, hold and turn to choose the target. The touch strip shows where every deck is.
- Page names and icons are read from the Stream Deck app. Pages without an icon show their number.
- Keys are black with a frame that lights up when the decks are in sync. Accent, frame, background and text colours can be set as hex codes.
- DeckSync keys work on decks without a DeckSync profile, such as a Virtual Stream Deck used as a remote.
- Works with the Stream Deck app's folders: the last known page is kept while a deck is inside one.
- Ready-made profiles for Stream Deck, Mini, XL, Stream Deck + and Neo, installed the first time a deck is seen.

## 0.2.0 — 2026-10-08

- Bundled user-exported profiles, `Profiles` block in the manifest.
- Fixed start-up crash (esbuild ESM bundle needed `createRequire` for `ws`).
- Go to page action with fixed fields for the 15-key deck and Stream Deck +.

## 0.1.0 — 2026-10-08

- Initial Tandem prototype: page marker action and sync logic, simulated only.
