# slida

It's a QT slideshow application written in Python. It only does image slideshows, and it does them pretty much the way I want them.

Some nice (?) features:

* It will try to optimize the screen area usage by tiling multiple images horizontally, because why waste all that precious real estate on thick black bars? (Example below)
* A bunch of cool transitions.

![Screenshot_20250628_092430](https://github.com/user-attachments/assets/81663353-2cca-43a1-9162-649b42b47c8c)

## Usage

```shell
$ slida -h
usage: slida [-h] [--recursive] [--no-auto] [--interval INTERVAL] [--order {name,created,modified,random}] [--reverse] [--transition-duration TRANSITION_DURATION] path [path ...]

positional arguments:
  path

options:
  -h, --help            show this help message and exit
  --recursive, -R
  --no-auto             Disables auto-advance.
  --interval INTERVAL, -i INTERVAL
                        Auto-advance interval, in seconds. Default: 20
  --order {name,created,modified,random}, -o {name,created,modified,random}
                        Default: random
  --reverse, -r
  --transition-duration TRANSITION_DURATION, -td TRANSITION_DURATION
                        In seconds. 0 = no transitions. Default: 0.5
```

Press `?` in the GUI for keyboard mapping info.

## Configuration files

A file called `slida.yaml` will be looked for in the following locations, in order of priority:

1. Any directory included as `path` on the command line
2. Current working directory
3. `slida` subdirectory of user's config directory (e.g. `~/.config/slida/` on Linux)

If multiple config files are found, they will be merged so that arguments in a higher priority file will overwrite those in lower priority files.

All command line arguments (in their long versions), except `path` and `help`, can be used in these files.

Also, the argument `transitions` can be included. This is an object that may contain the string arrays `include` and `exclude`, and governs which effects will be used for transitioning between images. If both `include` and `exclude` are defined, `exclude` is ignored. The full list of transitions is available in `slida.transitions.TRANSITION_PAIRS`.

### Example config file

```yaml
recursive: true
transitions:
  exclude:
    - slide_down
    - slide_right
    - slide_up
    - slide_left
```

(I like to exclude the "slide" transitions as they are kind of boring.)
