# Pipbloom

Landing page and waitlist for Pipbloom, a habit tracker for ADHD brains. A single static page, served by GitHub Pages.

## Edit the page

`index.html`, `og.png` and `favicon.svg` are generated. Change `tools/index.template.html` or `tools/build.py`, then rebuild:

```
python3 tools/build.py
```

The build needs Python 3 and Pillow (`pip3 install pillow`), which is used only for `og.png`.

## Before publishing

The waitlist button in `tools/index.template.html` points at `TALLY_FORM_URL`. Replace it with the real form link, rebuild, and check that the button opens the form.

```
grep -n "TALLY_FORM_URL" index.html   # must print nothing
```

## Publishing

In the repository settings, set Pages to deploy from the `main` branch, root folder.
