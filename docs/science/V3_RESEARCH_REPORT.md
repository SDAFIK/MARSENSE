# MARSENSE v3 terrain research candidate — November 14, 2026

Research-only, not approved for mission classification.

- Exact training commit: e3a19f284a85012b44f3358ce31ed43987049464
- [Executed research workflow](https://github.com/SDAFIK/MARSENSE/actions/runs/43575334860)
- Architecture: DeepLabV3 MobileNetV3, general-image pretrained; 4 CPU training epochs, 96 optimization steps.
- Genuine AI4Mars subset: train 48, validation 16, held-out MSL test 16, Perseverance transfer 8; 55 independent rover/site groups and 88 unique images. One proportionally resized image/label pair passed aspect check. All bytes were verified against the manifest.
- TorchScript SHA-256: 91ba983fa0e3af8da68ce57cfdcee32d27f1accf9139c8bbfa85856380bf922d

| Split | Pixel accuracy | Mean IoU |
|---|---:|---:|
| Validation | 0.8008 | 0.4431 |
| Held-out MSL | 0.8510 | 0.5296 |
| Perseverance transfer | 0.3133 | 0.1306 |

Held-out MSL rock recall was zero; Perseverance rock recall was 0.0181. The transfer mIoU is below the 0.35 engineering screening threshold. The model therefore fails the research screen and is disabled for mission terrain classification. The workflow succeeded as a training experiment, not as model approval.

The next experiment needs a larger representative training corpus, more rare-rock labels, cross-rover training data isolated from fresh test groups, calibration and independent validation. Report class-specific failure, not just pixel accuracy. No operational safety claim follows from these metrics.
