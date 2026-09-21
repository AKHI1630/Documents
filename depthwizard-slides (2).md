# DepthWizard — SIH 26175 Slide Text

---

## SLIDE 1 — PROBLEM STATEMENT

**Title:** A satellite photo records colour, not height

**The gap**
- From directly overhead, a 10-storey building and a painted rectangle look identical
- Flood modelling, landslide risk and evacuation routing all need elevation
- Disaster response needs it in **hours**, not weeks

**Why existing methods fail the timeline**

| Method | Blocker |
|---|---|
| Airborne LiDAR | Aircraft + crew + scheduled flight — days to weeks |
| Stereo pairs | Satellite must be tasked for two angles |
| InSAR | Specialised radar, slow interferometric processing |

**The requirement**
Extract metric height from imagery that **already exists**, with no second acquisition.

---

## SLIDE 2 — PROPOSED SOLUTION

**Title:** Measured height, not inferred height

**One line**
Single optical image → metric DSM + navigable LOD1 3D city model. **37 s on CPU**, no GPU, works offline.

**Pipeline**
```
satellite image + solar metadata
  → SAM instance segmentation
  → classify: building | tree | road | ground
  → shadow detection & matching
  → h = L × tan(θ_sun)
  → multi-cue fusion
  → LOD1 prism extrusion + imagery draped
  → metric GeoTIFF + 3D flythrough
```

**How it addresses the problem**
- Height is **measured by geometry**, not guessed by a model
- Shadow length + solar angle = photogrammetry, the same method used before LiDAR existed
- Runs on archive imagery — no tasking, no aircraft, no second pass
- 37 seconds per scene on a standard laptop

**Output**
Standard GeoTIFF (float32, source CRS, EGM96) — drops straight into QGIS / ArcGIS with no workflow change.

---

## SLIDE 3 — INNOVATION & UNIQUENESS

**Title:** Five things no competing submission has

**1 · We reject the obvious approach — with evidence**
Every rival uses monocular depth. We built it and measured **calibration R² = 0.099**. Our system auto-rejects it. Nadir geometry removes the perspective cues those models need (confirmed: arXiv:2604.02009).

**2 · LOD1 prisms, not a heightfield**
A heightfield interpolates between grid cells and is *mathematically incapable* of a vertical wall. We extrude each footprint separately — flat roofs and sharp edges by construction.

**3 · Five fused height cues**
Shadow · facade visibility · relief displacement · depth-calibrated ordering · neighbourhood prior. Inverse-variance weighted. Disagreement beyond combined uncertainty → flagged, never silently averaged.

**4 · Self-diagnosing gates**
- No georeferencing → rDSM, units explicitly null
- Two-tier admission: **R ≥ 0.5 AND azimuth Δ ≤ 20°**
- **Mosaic detection** — public basemaps composite multiple acquisitions, so solar geometry is undefined. Measured R = 0.02–0.36 proves it.
- Coverage as measured / inferred / failed — **never "100%"**

**5 · Quantified operating envelope**
**h_min = min_offset_px × GSD × tan(θ)**
Derived from first principles, then correctly predicted which acquisition would work.

| Site | Sun | GSD | h_min |
|---|---|---|---|
| Antakya | 28.1° | 0.305 m | **0.82 m** ✓ |
| Kathmandu | 74.0° | 0.500 m | **28 m** ✗ |

**The line to say out loud**
*We validate our own solar geometry against the shadows in the image, and decline to certify metric height when they disagree.*

---

## SLIDE 4 — TECHNICAL APPROACH

**Title:** Stack and performance

**Stack**
Segment Anything (ViT-B) · Depth Anything V2 Small · rasterio/GDAL · pysolar · scikit-learn (RANSAC, Huber) · scikit-image, OpenCV · FastAPI + SSE · Three.js WebGL · Docker

**Solar geometry priority chain**
1. Product metadata (.IMD / .XML / .MTL / EXIF) — exact
2. Computed from acquisition datetime + scene lat/lon via pysolar — exact orbital geometry
3. Azimuth measured from the image's own shadows — **validation cross-check**
4. User slider — labelled "estimated"

Source is always displayed in the UI.

**Performance: 536 s → 37 s (14× faster)**

| Stage | Time |
|---|---|
| SAM segmentation | 20.7 s |
| Depth inference | 2.1 s |
| Shadow + height | 1.0 s |
| **Total** | **37 s** |

CPU only · 4 GB RAM · no GPU · precomputed demos render **< 2 s**

**Deliberate decision:** no neural rendering. NeRF and Gaussian splatting evaluated and rejected — the problem statement names raster engines, and rasterisation meets it at a fraction of the compute cost.

---

## SLIDE 5 — RESULTS & VALIDATION

**Title:** Measured on real single-acquisition imagery

Antakya, Turkey · WorldView pre-earthquake · 0.305 m GSD · 28.1° sun · Vantor Open Data (CC-BY 4.0)

| Scene | Buildings | With heights | R | Verdict |
|---|---|---|---|---|
| Antakya crop2 | 24 | 23 | **0.624** | relative |
| Antakya crop1 | 14 | 12 | 0.387 | borderline, p=0.006 |
| Kathmandu | 9 | 2 | 0.196 | rejected, 7 failed |

**47 buildings · 37 with heights · 79% coverage**
Height range **1.8 – 14.7 m**, median 2.8 m — consistent with Antakya's known 1–2 storey Ottoman stone housing

**Model comparison**

| | MiDaS | DAv2 | Shadow |
|---|---|---|---|
| Brightness/height correlation | 0.17 | 0.64 | physics-derived |
| Building/road separation | 8.5 m | 55.8 m | per-building measured |
| Calibration R² | — | **0.099 → rejected** | n/a |

**Solar validation**
Measured azimuth 177° vs reference 141.6° → **Δ 35.8°** → exceeds the 20° gate → heights reported as relative, **not certified metric**.
No acquisition timestamp was available for this tile. With ISRO product metadata this check resolves definitively.

**Limitations — stated, not hidden**
- **No RMSE yet** — no reference DSM existed for the validation sites. GAMUS harness built, 5 sanity tests passing, awaiting paired tiles.
- **Footprint boundaries** — 96% centroid recall but 9.4% mask IoU. Buildings located, boundaries imprecise in dense fabric.
- **Height bias** — median low due to shadow truncation: shadows falling on neighbouring rooftops are masked out, shortening measured length.
- **OSM validation failed** — 0 of 324 mapped buildings carried a height tag.

For context: the strongest competing submission reports MAE 4.40 m, RMSE 5.86 m, R² 0.23 — self-described as "honestly poor".

---

## SLIDE 6 — FEASIBILITY, SCALABILITY & IMPACT

**Feasibility**
- Working pipeline today — 37 s, 4 GB RAM, no GPU
- Fully open-source, permissively licensed — **zero licence cost**
- ISRO products (Cartosat, Resourcesat) already carry the required solar metadata
- Containerised with health checks and precomputed demo scenes
- Offline after install — matters when disaster disrupts connectivity

**Challenges → mitigations**

| Challenge | Mitigation |
|---|---|
| Shadows occluded in dense rows | Multi-cue fusion; honest coverage reporting |
| Sun elevation error is multiplicative (tan θ) | Priority chain prefers metadata; uncertainty propagated to every error bar |
| Overcast / near-overhead sun | Feasibility pre-check warns before processing |
| Composite mosaics | Coherence gate detects and reports |

**Scalability**
- **No region-specific training** — shadow geometry is universal physics, doesn't degrade across geographies
- Tiling with feathered blending → arbitrary scene size, bounded memory
- Per-tile inference embarrassingly parallel
- Cloud Optimized GeoTIFF streaming from object storage
- Marginal cost per scene = CPU time → a national building-height layer from archive Cartosat imagery is tractable

**Impact**
- **Flood module:** per building — submerged depth, freeboard, status (dry / partial / fully submerged); affected counts and inundated area exportable to CSV
- **Damage assessment:** pre/post-event height differencing
- **Hours instead of weeks** — no aircraft, no tasked acquisition, no LiDAR survey
- Self-diagnosing gates mean an operator **cannot unknowingly act on unreliable output**

---

## SLIDE 7 — RESEARCH & REFERENCES

**Shadow-based height estimation**
- Liasis & Stavrou (2016), *Satellite images analysis for shadow detection and building height estimation*, ISPRS J. Photogramm. Remote Sens. 119:437–450
- Qureshi et al. (2024), *Building Height Estimation Using Shadow Length in Satellite Imagery*, arXiv:2411.09411
- Byrnside (2022), Missouri State University thesis
- Hao et al. (2021), *Building height estimation via satellite metadata and shadow instance detection*

**Monocular depth and its limits on nadir imagery**
- Yang et al. (2024), *Depth Anything V2*, arXiv:2406.09414
- *Test-Time Adaptation for Height Completion*, arXiv:2604.02009 — near-orthographic geometry eliminates perspective cues, forcing reliance on shadows; illumination variation causes height errors exceeding 30%
- *Depth2Elevation*, TechRxiv — up to 42% relative improvement on GAMUS

**Datasets**
- ISPRS 2D Semantic Labeling — Potsdam (38 patches, 5 cm GSD, TOP + DSM + nDSM)
- GAMUS — huggingface.co/datasets/earthflow/GAMUS
- Vantor / Maxar Open Data — 30–50 cm single-acquisition, CC-BY 4.0
- SAC reference — github.com/IMG-PROCESS-SAC/SIH2026/

**Literature accuracy for shadow methods**
±4.66 m vs LiDAR (Warsaw, several hundred thousand objects) · 4.08 m MAE (Shanghai, 15,966 buildings)
Short buildings are systematically over-estimated, tall ones under-estimated — so we report error by height band.

---

## JURY Q&A PREP

**Why not a depth model like everyone else?**
We built it, measured calibration R² = 0.099, and the system rejects it automatically. Nadir geometry removes the cues those models need.

**What's your dominant error source?**
Sun elevation. Height scales with tan(θ), so it's multiplicative and affects every building equally. Propagated into every error bar.

**Why is mask IoU only 9.4%?**
Centroid recall is 96% — we locate nearly every building. The gap is boundary precision in dense fabric. Polygon regularisation is the fix.

**Why is the median height low?**
Shadow truncation — shadows falling on neighbouring rooftops are masked out, shortening measured length. Identified and documented.

**What's your vertical datum?**
EGM96, declared explicitly in the exported GeoTIFF.

**Where does it fail?**
Dense low-rise settlements, overcast scenes, near-overhead sun, composite mosaics. All four detected and reported.
