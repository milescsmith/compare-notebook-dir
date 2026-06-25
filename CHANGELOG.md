# [0.6.1] - 202606-25

## Fixed
- Moved the reset table row reset string into the beginning of the loop so it actually resets the string

# [0.6.0] - 2026-06-25

## Added
- View diffs on the command line, though this is awkward and the display needs refinement
- Option to delete one of the files after diff review

## Changed
- Changed the argument to view diffs via browser to `--web_view`

# [0.5.0] - 2026-06-01

## Added
- Handling of JSON decode errors - ignore bad files, continue comparisons
- An optional final report of matched, mismatched, and missing notebooks

# [0.4.0] - 2026-06-01

## Fixed
- Actualy impolemented the `--no-checkpoints` argument

# [0.3.0] - 2026-06-01

## Added
- Added an option where, if a difference is found, a prompt asks the user if they would like to examine the 
difference.

# [0.2.0] - 2026-05-29

## Added
- A `--version` argument to... well, show the version

## Changed
- If a notebook is missing, the error now prints properly to the progress console

# [0.1.0] - 2026-05-29

## Added
- Everything

[0.6.1]: https://github.com/milescsmith/compare-notebook-dir/releases/releases/compare/0.6.0..0.6.1
[0.6.0]: https://github.com/milescsmith/compare-notebook-dir/releases/releases/compare/0.5.0..0.6.0
[0.5.0]: https://github.com/milescsmith/compare-notebook-dir/releases/releases/compare/0.4.0..0.5.0
[0.4.0]: https://github.com/milescsmith/compare-notebook-dir/releases/releases/compare/0.3.0..0.4.0
[0.3.0]: https://github.com/milescsmith/compare-notebook-dir/releases/releases/compare/0.2.0..0.3.0
[0.2.0]: https://github.com/milescsmith/compare-notebook-dir/releases/releases/compare/0.1.0..0.2.0
[0.1.0]: https://github.com/milescsmith/compare-notebook-dir/releases/tag/v0.1.0