# Generated animation layers

Created 2026-10-22 with the built-in imagegen tool. Each image was generated
separately with `reference.jpg` as input and the prompt constraint
“same lighting, same paper texture, same color palette as reference”.

Prompt set: remove envelope/stamp/central text for the clean background;
isolate the pocket with a transparent V notch; generate a darker inner back;
generate outside and inside triangular flap faces separately; isolate the
eight-point-star wax seal and wooden/brass stamp; generate a paper sheet with
the four verbatim Russian plans and red checks; recompose a vertical night
background with empty center and no text.

PNG masters are normalized to the brief's 2× sizes by
`python tools/prepare_assets.py`; WebP files are delivery assets. The generator
returned different native resolutions, so 2× output dimensions do not imply
every source was natively generated at that resolution. Original generations
remain in the tool's generated_images directory.

The generations are new artwork, not pixel-identical extractions. Final-frame
reference thresholds must be measured after integration and must not be
claimed from the old demo's baseline (all 1.80, envelope 2.91).
