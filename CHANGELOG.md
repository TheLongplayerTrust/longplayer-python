# Changelog

## [v0.1.3](https://github.com/TheLongplayerTrust/longplayer-python/tree/v0.1.3) (2024-11-18)

- Fixed off-by-one error in resampler
- Added `--buffer-size` command-line argument
- Restored missing `numpy` dependency, needed for `soundfile`

## [v0.1.2](https://github.com/TheLongplayerTrust/longplayer-python/tree/v0.1.2) (2024-11-18)

- Use `entry_points` mechanism to declare scripts, so that Longplayer can be run with `python3 -m longplayer` when the install does not update paths correctly

## [v0.1.1](https://github.com/TheLongplayerTrust/longplayer-python/tree/v0.1.1) (2024-11-18)

- Removed dependencies on `libsamplerate` and `numpy`

## [v0.1.0](https://github.com/TheLongplayerTrust/longplayer-python/tree/v0.1.0) (2024-11-17)

- Initial release of `longplayer-python`
