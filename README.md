# Mortal Combat Reborn — Stickman Arena Fighter

An original, code-drawn 2D stickman fighting game built with **Pygame**. Choose an arena, battle a CPU opponent or a second player, and use simple direct controls for punches, kicks, grabs, parries, blocking, dashes, and supers.

> This project uses original stickman fighters, original arenas, and original gameplay code. It does not use characters, art, or audio from another game franchise.

## Download / Play

- **Download the latest Mac or Windows build:** [GitHub Releases](https://github.com/pratyush2027/mortal-combat-stick-figure-/releases)
- **Source code and project updates:** [GitHub repository](https://github.com/pratyush2027/mortal-combat-stick-figure-)
- **Browser build (after GitHub Pages is deployed):** [Play in your browser](https://pratyush2027.github.io/mortal-combat-stick-figure-/)

### Sharing the desktop game

- **macOS:** download the `.app.zip`, unzip it, then right-click the app and choose **Open** the first time.
- **Windows:** download the `.zip`, unzip the whole folder, and open `Mortal Combat Reborn.exe`. Keep every file in the extracted folder together.

## Start Menu

1. Press `1` for **VS CPU**.
2. Press `2` for **Local Two Player**.
3. Choose an arena with `Left` / `Right`, `Up` / `Down`, or number keys `1`–`4`.
4. Press `Enter` or `Space` to begin.
5. Press `Esc` at any time after the title screen to return to the main menu. Press `Esc` at the title screen to exit.

## Keyboard Controls

### Player 1

| Action | Key |
|---|---|
| Move left | `A` |
| Move right | `D` |
| Jump | `W` |
| Crouch | `S` |
| Punch | `F` |
| Kick | `R` |
| Grab / combo breaker | `T` |
| Parry / hold to block | `Q` |
| Super when meter is full | `E` |

### Player 2

| Action | Key |
|---|---|
| Move left | `←` Left Arrow |
| Move right | `→` Right Arrow |
| Jump | `↑` Up Arrow |
| Crouch | `↓` Down Arrow |
| Punch | `P` |
| Kick | `K` |
| Grab / combo breaker | `O` |
| Parry / hold to block | `M` |
| Super when meter is full | `L` |

## Combat Notes

- `F` and `P` always punch.
- `R` and `K` always kick.
- Double-tap left or right to dash.
- Tap the parry key just before an attack hits to counter. Hold it to block and reduce damage.
- Attack inputs are buffered: pressing a punch or kick slightly early will execute it as soon as the current move ends.
- Use grab when standing close to your opponent. If both players grab at nearly the same time, the throw clashes.
- Build the gold meter under the health bar, then press `E` or `L` to use a super.

## Run From Source

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

`pygame-ce` installs under the import name `pygame`.

## Files

```text
main.py           # Game code
requirements.txt  # Pygame dependency
README.md         # Setup, download links, and controls
```
