# yenfam.com

The Yen family photo gallery. It is a static site on GitHub Pages (served from `main`, repo root).

**Everything in this repo is public**, including every photo and its git history. Deleting a photo later does not remove it from history.

## Add photos

```sh
brew install exiftool          # one time
./add-photos.py --album "Summer 2026" ~/Desktop/summer/
git add -A && git commit -m "Add summer photos" && git push
```

The script converts each photo to JPEG, resizes it (2048px full, 600px thumbnail), and strips all metadata, including GPS location. Then it adds the photo to `photos.json`. Never commit original photos directly.

To add a caption, edit `photos.json` and set `"caption"` on that photo. Without `--album`, photos are grouped by the year they were taken.

`robots.txt` and the `noindex` tag ask search engines not to index the site.

## Moving beach picture

The picture at the top of the page is animated with WebGL: the clouds drift and the waves lap the shore, on a 16-second loop. `hero/beach-mask.png` marks which parts move, and `hero/beach-clean.jpg` is the beach with the shore foam painted out, so the foam can wash over it. To rebuild both, run `./hero/make-hero.py hero/beach.jpg hero/beach-mask.png hero/beach-clean.jpg`. It needs numpy and Pillow. The people outline in that script only fits this picture. `hero/og.jpg` is the link-preview image that iMessage and other apps show.
