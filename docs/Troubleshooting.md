# Troubleshooting

[Home](../README.md) · [Installation](Installation.md) · [Getting started](Getting-started.md) · [Actions](Actions.md) · [Page dial](Page-dial.md) · [Decks without a dial](No-dial.md) · [Virtual Stream Deck](Virtual-Stream-Deck.md) · [Colours](Colours.md) · [Folders](Folders.md) · **Troubleshooting**

---

## Tips and limitations

- Follow mode needs a marker on every page. Delete a marker and that page stops announcing itself.
- A deck is only followed while it shows a DeckSync profile. Switch it to another profile and it simply drops out of the sync until it comes back.
- "Go to page" and follow mode can be combined. After a split jump, the next page turn re-aligns the decks.
- Profiles have 10 pages. Jumping to a page that does not exist in a profile is ignored by the Stream Deck app.
- Updating or reinstalling DeckSync never changes the profiles already installed in your app.

## If something does not work

DeckSync writes a log in the `logs` folder inside its plugin folder (in the Stream Deck app's plugin directory). Every line starts with `DeckSync:`. At start-up it lists each device with its type and the profile it maps to.

If a deck never received its DeckSync profile, remove the plugin and install it again, or press any Go to page key that targets that deck: the app installs the profile on the first switch.

## Common questions

**The other deck does not follow.** Check that both decks show their DeckSync profile, and that the page has a page marker. A deck on another profile is left alone.

**A key shows "Page 3" but no name.** Name the page in the Stream Deck app: right-click the page number in the page bar of the DeckSync profile.

**I want different pages on each deck.** Use a Go to page key with a page per deck, or hold and turn the page dial to pick one deck.

**Can I use my existing profiles?** The Stream Deck app only lets a plugin switch to profiles that came with the plugin, so the sync works inside the DeckSync profiles. Copy your keys into them. DeckSync keys such as Page step and Go to page work on any profile.

---

Questions or a bug? Open an issue: https://github.com/BerrisNO/DeckSync/issues
