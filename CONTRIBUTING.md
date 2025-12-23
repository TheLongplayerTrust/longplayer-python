# Contributing

## Creating a release

- Copy the Longplayer audio file [20-20.wav](https://longplayer.org/audio/20-20.wav.zip) to the `longplayer/audio` directory
- Increment the version in `setup.py`
- Add a new entry to `CHANGELOG.md`
- Run `git tag vx.y.z`, and `git push --tags`
- Create a new GitHub Release with the contents of the new CHANGELOG entry, attached to the new release tag
- Run `python3 setup.py sdist`
* Run `twine upload dist/longplayer-x.y.z.tar.gz`
