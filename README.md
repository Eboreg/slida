# slida

It's a QT slideshow application written in Python. It only does image slideshows, and it does them pretty much the way I want them.

Some nice (?) features:

* It will try to optimize the screen area usage by tiling multiple images horizontally, because why waste all that precious real estate on thick black bars?
* A bunch of cool transitions.

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
