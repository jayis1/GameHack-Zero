# GameHack Zero handheld customization

Inspired by Momentum Firmware's customization workflows:
https://github.com/Next-Flip/Momentum-Firmware

This is an original Linux/Pygame implementation. No Momentum code, logos,
animations, fonts, or binary asset packs are bundled. Momentum firmware targets
Flipper Zero and cannot be flashed onto an R36XX. Native Flipper asset packs
are not supported by this implementation.

## Controls

The home screen uses a 3x3 category grid. D-pad moves between tiles; R2/A opens
the highlighted category. Inside a category, up/down selects a tool and
left/right (or L1/R1) changes category. L2/B returns home. The sidebar retains
category context, and the lower panel describes the selected action.

L2/B is back/cancel and R2/A is confirm throughout dialogs and the controller
keyboard. In Freedoom, L2 opens/goes back through menus and R2 confirms;
L2+R2 exits the game. These replace the earlier trigger page-scroll bindings.

- A: open/confirm; B: back
- Y on the main menu: toggle a favorite (marked `*`)
- X: dashboard; L1/R1: category
- QUICK: Favorites, Recent Actions, Appearance, About
- INFRARED: status, learn, send saved raw signal, library, format guide
- FILES: bounded case-insensitive filename search

Preferences persist in `/data/gamehack-zero/settings.json`.
Available themes: Momentum-inspired amber (default), GameHack cyan, high-contrast mono.

## Portable color packs

Create `/data/gamehack-zero/asset_packs/MyPack/theme.json`:

```json
{
  "name": "MyPack",
  "colors": {
    "bg": [18, 14, 8],
    "panel": [37, 28, 14],
    "active": [67, 44, 15],
    "accent": [255, 164, 36],
    "focus": [255, 211, 103],
    "text": [255, 240, 211],
    "muted": [185, 155, 109],
    "error": [255, 96, 83]
  }
}
```

Select QUICK > Appearance to reload and choose the pack. Every color must be
three integer RGB values in 0..255. Invalid packs are ignored.

## Boundaries

No NFC or Sub-GHz integration. No BLE spam or automatic keyboard payloads.
The IR adapter needs USB host mode; USB maintenance Ethernet needs gadget mode.
On-device graphics, radio and IR capture/transmission still require hardware testing.
