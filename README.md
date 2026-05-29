# `compare-notebook-dirs`

[`nbdime`](https://nbdime.readthedocs.io/en/latest/) is great for comparing two jupyter notebooks at a time and showing
the actual differences, but sometimes you just want to know which notebooks differ.

`compare-notebook-dirs` runs `nbdime` over all notebooks with matching names within two directories and reports only _if_
there are differences, not what they are.

**Usage**:

```console
$ compare-notebook-dirs [OPTIONS] PATH1 PATH2
```

**Arguments**:

* `PATH1`: Directory to compare against.  [required]
* `PATH2`: Directory to use for comparison  [required]

**Options**:

* `-e, --ext TEXT`: file extension to search for  [default: ipynb]
* `-r, --rec`: search folders recursively?  [default: True]
* `-v, --verbose`: Turn on logging
* `--help`: Show this message and exit.