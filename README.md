# Auto DAT file generator

![Daily Rebuild Status](https://github.com/dragredsim/auto-datfile-generator/actions/workflows/daily-rebuild.yml/badge.svg)

WWW profiles to use in clrmamepro for the standard No-Intro and Redump sets.
Refreshes once every 24h automatically.

Note that URL sources marked with a ⬇️ have alternate feeds available, which will download the DAT files directly from their hosts, instead of from a compiled ZIP archive hosted on this repository. They may be more up-to-date by up to 24 hours, but no guarantees are offered in regards to their compatibility or availability.

## URLs

### No-Intro

`https://github.com/dragredsim/auto-datfile-generator/releases/latest/download/no-intro.xml`

### No-Intro (parent-clone)

`https://github.com/dragredsim/auto-datfile-generator/releases/latest/download/no-intro_parent-clone.xml`

### Redump ⬇️

`https://github.com/dragredsim/auto-datfile-generator/releases/latest/download/redump.xml`

Source feed: `https://github.com/dragredsim/auto-datfile-generator/releases/latest/download/redump-source.xml`

### En-ROMs (from Archive.org) ⬇️

`https://github.com/dragredsim/auto-datfile-generator/releases/latest/download/translated-en.xml`

Source feed: `https://github.com/dragredsim/auto-datfile-generator/releases/latest/download/translated-en-source.xml`

NOTE: due to how the versions are stored in the DAT files provided from this source, updated DAT files may show up in the CLRMamePro profiler as being "old" versions. This is because the version in the DAT is stored in a DD-MM-YYYY format, which is sorted as a pure text string; so an update on the 3rd of March will appear "older" than an update on the 27th February. Only the latest available file is available via the profiler. In the future, a mangled version of the `translated-en.xml` file will be available, which will correct this automatically; because it involves changing the values in the DAT files (which CLRMamePro uses as the comparison basis to determine new/old), it will not be available as a source pack.

### FinalBurn Neo ⬇️

`https://github.com/dragredsim/auto-datfile-generator/releases/latest/download/fbneo.xml`

Source feed: `https://github.com/dragredsim/auto-datfile-generator/releases/latest/download/fbneo-source.xml`

### FinalBurn Neo - Specialty

`https://github.com/dragredsim/auto-datfile-generator/releases/latest/download/fbneo-specialty.xml`

This is a feed created on-the-fly by extracting parts of the full FBNeo Arcade DAT, in order to produce a few system-specific DATs. Currently this offers DATs for the individual CPS arcade systems produced by Capcom, as some emulator frontends allow these to be their own categories. This will allow you to DAT just those systems out.

<!--- currently disabled

### Hardware Target Game Database

`https://github.com/hugo19941994/auto-datfile-generator/releases/latest/download/smdb.xml`

### Custom dats.site

`https://github.com/hugo19941994/auto-datfile-generator/releases/latest/download/dats-site.xml`

--->

![clrmamepro screenshot](./img/clrmamepro.png)

Project inspired by [redump-xml-updater](https://github.com/bilakispa/redump-xml-updater)

## Header support

Some No-Intro dats require an extra XML file to detect headers.

![clrmamepro header warning screenshot](./img/headers.png)

Download the following zips, extract them and place the XML files in clrmamepro's `headers` folder:

- [Atari Jaguar](https://datomatic.no-intro.org/stuff/header_a7800.zip)
- [Atari Lynx](https://datomatic.no-intro.org/stuff/header_lynx.zip)
- [Nintendo FDS](https://datomatic.no-intro.org/stuff/header_fds.zip)
- [Nintendo NES](https://datomatic.no-intro.org/stuff/header_nes.zip)
