# AI4Mars Merged Dataset Changelog

## Version 0.6

- **Fix:** merged MER labels

## Version 0.5

Current data cleaning ranking: MSL NavCam > MER > MSL MastCam > M2020 NAV > M2020 Geology

- **M2020 NavCam and MastCam images and labels added**
  - M2020 data includes semantic labels intended to aid with geology
  - Added `label_keys.json` to aid with label decoding
  - Divided mastcam from navcam (mcam / ncam) data
  - Added merged training labels
  - **[NOTE]** there are no expert test sets available for M2020 at this time

---

## Version 0.4

- **MSL MastCam images and labels added**
  - **[NOTE]** Mast images do not have expert labeled test sets available at this time
  - **[NOTE]** Mast images do not have rover or range masks as these data products are not available for this image type.

---

## Version 0.3

- **MER Data Fixes:**
  - Added missing images
  - Removed training labels which overlap with test labels
  - Added merged training labels
    - Merges that resulted in empty labels removed
    - **[NOTE]** Merges currently unmasked (range mask not applied)

---

## Version 0.2

- **MER Data Added:**
  - Includes image products
  - **[NOTE]** 30-meter range and rover mask products not yet provided
  - **[NOTE]** Includes some bad/useless images
  - Includes unmasked+merged labels
  - Includes raw (unmasked, not merged, some bad labels) labels
  - Masked+merged+cleaned labels not yet provided

---

## Version 0.1

- **Contains Curiosity (MSL) Data:**
  - Includes 30-meter range, rover mask, and image products
  - Includes masked+merged+cleaned (bad labels removed) labels
- **WIP**: MER data has not yet been processed/packaged
