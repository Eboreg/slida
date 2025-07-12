# slida

It's a QT slideshow application written in Python. It only does image slideshows, and it does them pretty much the way I want them.

Some nice (?) features:

* By default, it will try to optimize the screen area usage by tiling multiple images horizontally, because why waste all that precious real estate on thick black bars? (Example below)
* A bunch of cool transitions

![Screenshot_20250628_092430](https://github.com/user-attachments/assets/81663353-2cca-43a1-9162-649b42b47c8c)

## Usage

```shell
$ slida --help
usage: slida [-h] [--interval INTERVAL] [--order {name,created,modified,random}] [--transition-duration TRANSITION_DURATION] [--transitions TRANSITIONS [TRANSITIONS ...]]
             [--exclude-transitions EXCLUDE_TRANSITIONS [EXCLUDE_TRANSITIONS ...]] [--list-transitions] [--print-config] [--auto | --no-auto] [--recursive | --no-recursive] [--reverse | --no-reverse]
             [--tiling | --no-tiling] [--hidden | --no-hidden]
             [path ...]

positional arguments:
  path

options:
  -h, --help            show this help message and exit
  --interval INTERVAL, -i INTERVAL
                        Auto-advance interval, in seconds (default: 20)
  --order {name,created,modified,random}, -o {name,created,modified,random}
                        Default: random
  --transition-duration TRANSITION_DURATION, -td TRANSITION_DURATION
                        In seconds; 0 = no transitions (default: 0.3)
  --transitions TRANSITIONS [TRANSITIONS ...]
                        One or more transitions to use (default: use them all)
  --exclude-transitions EXCLUDE_TRANSITIONS [EXCLUDE_TRANSITIONS ...]
                        One or more transitions NOT to use
  --list-transitions    List available transitions and exit
  --print-config        Also print debug info about the current config
  --auto                Enable auto-advance (default)
  --no-auto             Disable auto-advance
  --recursive, -R       Iterate through subdirectories
  --no-recursive        Do not iterate through subdirectories (default)
  --reverse, -r         Reverse the image order
  --no-reverse          Do not reverse the image order (default)
  --tiling              Tile images horizontally (default)
  --no-tiling           Do not tile images horizontally
  --hidden              Include hidden files and directories
  --no-hidden           Do not include hidden files and directories (default)
```

`--transitions` and `--exclude-transitions` govern which effects will be used for transitioning between images. The full list of transitions is available in `slida.transitions.TRANSITION_PAIRS`. Explicit exclusion overrides explicit inclusion. However, there is one special case: `--transitions all` on the command line overrides all other transition settings and simply includes all of them.

Press `?` in the GUI for keyboard mapping info.

## Configuration files

A file called `slida.yaml` will be looked for in the following locations, in order of priority:

1. Any directory included as `path` on the command line
2. Current working directory
3. `slida` subdirectory of user's config directory (e.g. `~/.config/slida/` on Linux)

If multiple config files are found, they will be merged so that arguments in a higher priority file will overwrite those in lower priority files.

All command line arguments in their long versions (OK, except `path`, `help`, `list-transitions`, and `print-config`) can be used in these files. However, the syntax for transition settings is a little different; instead of two separate settings, it's one `transitions` object with the optional string arrays `include` and `exclude` (see example below).

To see exactly how the CLI arguments and config files are parsed, and how the resultant configuration looks, just add `--print-config`:

```shell
$ slida --no-auto -td 3 --transitions top-left-squares top-squares --print-config
CombinedUserConfig(FINAL)
  auto: False
  hidden: False
  interval: 20
  order: random
  recursive: True
  reverse: False
  tiling: True
  transition-duration: 3.0
  transitions: {'include': ['top-left-squares', 'top-squares']}
= DefaultUserConfig()
    auto: True
    hidden: False
    interval: 20
    order: random
    recursive: False
    reverse: False
    tiling: True
    transition-duration: 0.3
    transitions: {}
+ UserConfig(/home/klaatu/.config/slida/slida.yaml)
    recursive: True
+ UserConfig(CLI)
    auto: False
    transition-duration: 3.0
    transitions: {'include': ['top-left-squares', 'top-squares']}
```

### Example config file

```yaml
recursive: true
transition-duration: 0.2
order: name
transitions:
  include:
    - clockface
    - top-left-squares
    - flip-x
    - radial
  exclude:
    - slide-down
    - slide-right
    - slide-up
    - slide-left
```
(Obviously it makes no sense to both include and exclude transitions, but this is an example.)
