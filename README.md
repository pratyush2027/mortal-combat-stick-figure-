# Mortal Combat Reborn — Stickman Controls Update

An original, code-drawn 2D arena fighting prototype built with **Pygame**. This version uses simple stick fighters with clear punch, kick, block, parry, grab, super, and dash animations.

## What Changed

- Replaced the human-like fighters with simple, readable stickman fighters.
- Made **Punch** and **Kick** inputs consistent and easier to see:
  - `F` / `P` always performs a punch.
  - `R` / `K` always performs a kick.
  - Inputs can be buffered, so a quick second press is performed as soon as the current move ends.
- Enlarged basic attack ranges and active hit frames so close-range punches register more reliably.
- Kept the four selectable arenas and the `Esc` return-to-main-menu option.

## Install and Run

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

`pygame-ce` installs under the import name `pygame`.

## Menu Flow

1. Press `1` for **VS CPU** or `2` for **Local Two Player**.
2. Choose an arena using `Left` / `Right`, `Up` / `Down`, or number keys `1`–`4`.
3. Press `Enter` or `Space` to begin.
4. Press `Esc` anytime after the title screen to return to the main menu.
5. Press `Esc` from the main menu to exit the game.

## Player 1 Controls

| Action | Key |
|---|---|
| Move left / right | `A` / `D` |
| Jump | `W` |
| Crouch | `S` |
| Punch | `F` |
| Kick | `R` |
| Parry / block | `Q` |
| Grab / combo breaker | `T` |
| Super | `E` when meter is full |

## Player 2 Controls

| Action | Key |
|---|---|
| Move left / right | `Left` / `Right` arrows |
| Jump | `Up` arrow |
| Crouch | `Down` arrow |
| Punch | `P` |
| Kick | `K` |
| Parry / block | `M` |
| Grab / combo breaker | `O` |
| Super | `L` when meter is full |

## Notes

- Punch and kick controls are now direct: there are no direction-based special-move sequences to accidentally override them.
- Tap the parry key just before an attack lands for a parry. Hold it to block.
- Double-tap a movement direction to dash.
- At the end of a match, press `Enter` or `R` to return to the menu.
