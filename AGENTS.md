# AGENTS.md

## Local Machine Configuration

- Date recorded: 2026-07-26
- Workspace: `D:\AI\seeThrough`
- Repository: `https://github.com/shitagaki-lab/see-through`
- Computer name: `DESKTOP-RKVJN3F`
- OS: Microsoft Windows 10 Pro, version `10.0.19045`, 64-bit
- CPU: Intel Core i7-7700K CPU @ 4.20GHz
- Logical processors: 8
- RAM: 15.96 GB
- GPU: NVIDIA GeForce GTX 1070
- GPU VRAM: 8192 MiB
- NVIDIA driver: 582.28
- CUDA compute capability: 6.1

## Local Tooling Detected

- Git: `D:\Program Files\Git\cmd\git.exe`, version `2.54.0.windows.1`
- System Python: `D:\Python\Python314\python.exe`, version `3.14.5`
- Python launcher: `C:\Windows\py.exe`, defaulting to Python `3.14.5`
- Conda: not installed
- Node.js: `D:\nvm4w\nodejs\node.exe`, version `v24.15.0`
- npm: `D:\nvm4w\nodejs\npm.ps1`
- `nvidia-smi`: available
- CUDA Toolkit / `nvcc`: not installed

## See-through Installation Notes For This Machine

- The project README asks for Python 3.12. Do not use the system Python 3.14 environment for this project.
- Because conda is not installed, this install uses the local virtual environment at `D:\AI\seeThrough\.venv`.
- The GTX 1070 has 8 GB VRAM. Prefer the low-VRAM inference entry points from the README:
  - `inference/scripts/inference_psd_quantized.py`
  - `inference/scripts/inference_psd_blockswap.py`
- The default full-precision pipeline is documented as requiring roughly 12-16 GB VRAM at 1280 resolution, so it is not a good default for this machine.
- The PyTorch CUDA wheel includes its own CUDA runtime; a local CUDA Toolkit is not required for normal inference. Native extension builds may still require compiler/CUDA tooling.
- Always run project commands from the repository root: `D:\AI\seeThrough`.
- The root-level `assets` path must point to `common/assets` for UI and examples.

## Installed Environment

- Python 3.12.10 installed via `winget`.
- Local venv: `D:\AI\seeThrough\.venv`.
- PyTorch installed: `torch==2.8.0+cu128`, `torchvision==0.23.0+cu128`, `torchaudio==2.8.0+cu128`.
- CUDA validation passed in PyTorch:
  - `torch.cuda.is_available() == True`
  - GPU: `NVIDIA GeForce GTX 1070`
  - VRAM visible to PyTorch: 8.0 GB
- Project dependencies installed from `requirements.txt`.
- Windows UI dependency `pywin32==312` installed because UI imports require `win32api`.
- Low-VRAM NF4 dependency `bitsandbytes==0.49.2` installed from `requirements-inference-bnb.txt`.
- `assets` is a Windows junction pointing to `D:\AI\seeThrough\common\assets`.

## Verified Commands

Run these from `D:\AI\seeThrough`.

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe ui\test_tier_a_imports.py
.\.venv\Scripts\python.exe ui\ui\launch.py --help
.\.venv\Scripts\python.exe inference\scripts\inference_psd_quantized.py --help
.\.venv\Scripts\python.exe inference\scripts\inference_psd_blockswap.py --help
```

## Suggested Run Commands

UI:

```powershell
cd D:\AI\seeThrough
.\.venv\Scripts\python.exe ui\ui\launch.py
```

Low-VRAM PSD inference:

```powershell
cd D:\AI\seeThrough
.\.venv\Scripts\python.exe inference\scripts\inference_psd_quantized.py --srcp assets\test_image.png --save_to_psd --tblr_split --resolution 1024
.\.venv\Scripts\python.exe inference\scripts\inference_psd_quantized.py --srcp assets\test_image.png --save_to_psd --tblr_split --resolution 768 --resolution_depth 512 --no_cpu_offload --no_group_offload
```

On this GTX 1070 machine, `inference/scripts/inference_psd_quantized.py` has a local compatibility patch:

- Automatically sets `BNB_CUDA_VERSION=126` for Pascal GPUs with PyTorch CUDA 12.8, because the default bitsandbytes CUDA 12.8 backend fails with `named symbol not found` in NF4 kernels.
- Automatically enables CPU offload for NF4 inference on Pascal GPUs.
- Caches LayerDiff text embeddings before enabling CPU offload to avoid CPU/GPU token device mismatch.
- Keeps VAE encode/decode tensors on the actual offload execution device and temporarily moves the transparent VAE decoder to GPU for decoding; otherwise it can spend a very long time in CPU convolution after the denoising progress bar reaches 100%.
- Moves LayerDiff `GroupEmbedding` modules to the input tensor device during forward; CPU offload can leave these small embedding modules on CPU while UNet hidden states are on GPU.
- Uses the pipeline's actual offload execution device (`cuda:0`) instead of `unet.device` (`cpu` while offloaded) for denoising tensors.
- Normalizes all nested UNet condition tensors onto the active execution device at the start of each forward pass; this covers timestep, class, SDXL addition, attention, and residual inputs instead of patching device mismatches one layer at a time.
- Computes Marigold's one-time empty CLIP embedding on CPU and caches it at `workspace/empty_text_tensor.safetensors`; Pascal CUDA can fail in the quantized CLIP SDPA path.
- Uses Marigold's actual group-offload execution device for VAE encoding/decoding, conditioning latents, noise, and UNet inputs.
- Supports `--skip_layerdiff` to resume from existing layer PNG files after a successful LayerDiff stage.
- Disables Diffusers group offload for the NF4 Marigold UNet. Its generic tensor transfer is incompatible with bitsandbytes `Params4bit` on Pascal and can cause an illegal CUDA memory access.
- Runs NF4 Marigold in FP16 on Pascal and updates every bitsandbytes `Linear4bit.compute_dtype` accordingly. BF16 SDPA falls back to the memory-heavy math backend on GTX 1070, while FP16 can use memory-efficient attention.

If inference still runs out of memory at 1024 resolution, retry with `--resolution 768`.

## Not Installed / Not Downloaded

- Optional `mmdet`, `sam2`, and `detectron2` annotator tiers were not installed. They are optional in the README and can require native build tooling or additional large downloads.

## Downloaded Model Cache

The low-VRAM NF4 inference models are cached under `C:\Users\98799\.cache\huggingface\hub`.

- `24yearsold/seethroughv0.0.2_layerdiff3d_nf4`: complete, required files total about 3.51 GB.
- `24yearsold/seethroughv0.0.1_marigold_nf4`: complete, required files total about 1.80 GB.
- `frankjoshua/juggernautXL_version6Rundiffusion` scheduler config: present.

Offline local loading was verified for:

- `TransparentVAE.from_pretrained("24yearsold/seethroughv0.0.2_layerdiff3d_nf4", subfolder="trans_vae", local_files_only=True)`
- `UNetFrameConditionModel.from_pretrained("24yearsold/seethroughv0.0.2_layerdiff3d_nf4", subfolder="unet", local_files_only=True)`
- `MarigoldDepthPipeline.from_pretrained("24yearsold/seethroughv0.0.1_marigold_nf4", local_files_only=True)`

The first real inference run should not need to re-download these NF4 model weights.
