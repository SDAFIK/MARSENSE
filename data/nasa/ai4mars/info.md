# AI4Mars Merged Dataset

This dataset contains all the images and merged labels gathered by the [AI4Mars project by Zooniverse](https://www.zooniverse.org/projects/hiro-ono/ai4mars) as well as some expert labels gathered by NASA JPL used for creating test sets. Each image in the dataset was labeled by multiple labelers and then merged in post-processing, so while the dataset covers 60K+ images and 300K+ labels, you will only find 60K+ labels. An unmerged label dataset may be made available upon request.

## Acronyms

1. MSL - Mars Science Laboratory (Curiosity Rover)
2. MER - Mars Exploration Rovers (Spirit and Opportunity Rovers)
3. M2020 - Mars 2020 Rover (Perseverance)

## Labels [.png]

Labels are provided as grayscale `.png` images. Data is organized into train and test sets. Unless otherwise noted, distances further than 30 meters and the rover itself are masked; this is done to remove labeled pixels that don't make sense or are poor quality. 

> **NOTE:** Due to the closeness of pixel values, labels viewed as-is in a regular image viewer will look like black and white images. The pixel values for each class are shown below. Viewing labels as colored overlays requires using a library, such as the python library Pillow (PIL) to create a colored view based on this class key.

### Navigation (NAV) pixel value key:

Most labels provided divide terrain into these groups intended to differentiate areas of good or poor traversability/navigation. For more background on how these labels were defined, you can [lookup ai4mars on zooniverse](https://www.zooniverse.org/projects/hiro-ono/ai4mars), and look at the tutorials for labeling any of the non-geology images (attempt to label an image, then click on Tutorial).


- `0` - soil
- `1` - bedrock
- `2` - sand
- `3` - big rock
- `255` - NULL (no label)

### Train

`train` contains a cleaned and merged version of crowdsourced labels with a minimum agreement of 3 labelers and 2/3 agreement for each pixel. If a pixel does not have meet these requirements, it is marked as NULL (unlabeled). A raw version of the dataset with raw labels (without masking or merging) can be made available upon request.

### Test

`test` contains a merged version of expert-gathered labels with 100% agreement required on each pixel. Three different versions of the merge are provided, which specify how many people must agree on each pixel for it to be included in the label. `min3` is the sparsest as it requires all 3 labelers to agree.

------------------------------

## Images

Names of images match names of labels, except for the extension (JPG, PNG) and sometimes an obvious suffix (e.g. `_merged`). The acronyms provided below refer to the acronym included in the middle of the image name. MSL and M2020 MastCam images are in color.

### EDR (MSL), ML (MSL), EFF (MER), Vgnc (M2020), NLF (M2020), ZL0 (M2020) [.JPG]
The actual images of Mars that labels are made for and for which training and inference are run on. As available in this dataset, EDR, EFF, Vgnc, NLF are for NavCams; ML and ZL0 is for the MastCam. Note that these acronyms in filenames do have meaning; more info can be found in the relevant PDS image document (e.g. for MSL, [see here](https://planetarydata.jpl.nasa.gov/img/data/msl/MSLNAV_1XXX/DOCUMENT/MSL_CAMERA_SIS.PDF)). *NOTE:* MastCam does not have rover or range masks applied (they do not exist).

### MXY (MSL), MRL (MER) [.png]
Rover masks used to remove labels/inferences from the rover. Masked regions are set to 1 (binary image).

### RNG-30M, RNL-30M [.png]
Range masks used to mask out distances that are further than 30 meters. Masked regions are set to 1 (binary image). This product is generated from [planetary data system (PDS)](https://pds-imaging.jpl.nasa.gov/volumes/) range image products for many Mars images. Future versions of the dataset will include instructions on downloading and processing those range products.

## M2020 Geology (M2020_GEO) Label Keys (Beta)

bedrock, float rock, and sand each have their own subtypes in this dataset, so these semantic labels are organized by factors of 10, where label number = (10^(base_type) + subtype). For more background on how these labels were defined, it may be helpful to look at the tutorials [on Zooniverse](https://www.zooniverse.org/projects/hiro-ono/ai4mars) for Perseverance Geology (attempt to label an image, then click on Tutorial).

- `0` - bedrock_massive
- `1` - bedrock_layered (angled)
- `2` - bedrock_layered (flat)
- `3` - bedrock_layered (unsure)
- `4` - bedrock_conglomerate
- `5` - bedrock_holey
- `6` - bedrock_unsure
- `10` - float rock(s)_massive
- `11` - float rock(s)_layered (angled)
- `12` - float rock(s)_layered (flat)
- `13` - float rock(s)_layered (unsure)
- `14` - float rock(s)_conglomerate
- `15` - float rock(s)_holey
- `16` - float rock(s)_mixed
- `17` - float rock(s)_unsure
- `20` - sand_dune
- `21` - sand_ripples
- `22` - sand_sand
- `30` - pebbles
- `40` - vein (rare)
- `50` - hill/peak
- `255` - NULL (no label)