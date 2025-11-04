from __future__ import annotations

import io
import math
import shutil
from pathlib import Path
from typing import Optional

import pikepdf
from PIL import Image


class CompressionResult:
    def __init__(self, output_path: Path, size_bytes: int):
        self.output_path = output_path
        self.size_bytes = size_bytes


def _calculate_base_downscale(original_size: int, target_bytes: int) -> float:
    if original_size <= 0 or target_bytes <= 0:
        return 1.0

    ratio = min(1.0, target_bytes / original_size)
    if ratio >= 0.98:
        return 1.0

    return max(0.3, math.sqrt(ratio))


def _calculate_iteration_downscale(
    quality: int,
    min_quality: int,
    max_quality: int,
    base_downscale: float,
) -> float:
    if base_downscale >= 0.999:
        return 1.0

    if max_quality <= min_quality:
        return base_downscale

    span = max_quality - min_quality
    quality_ratio = (quality - min_quality) / span
    quality_ratio = max(0.0, min(1.0, quality_ratio))

    downscale = base_downscale + (1.0 - base_downscale) * quality_ratio
    return max(0.3, min(1.0, downscale))


def _recompress_images(pdf: pikepdf.Pdf, quality: int, *, downscale_factor: float = 1.0) -> None:
    for page in pdf.pages:
        images = page.images
        for name, raw_image in images.items():
            pdf_image = pikepdf.PdfImage(raw_image)
            try:
                pil_image = pdf_image.as_pil_image()
            except (NotImplementedError, ValueError):
                continue

            if pil_image.mode in ("RGBA", "LA"):
                background = Image.new("RGB", pil_image.size, (255, 255, 255))
                background.paste(pil_image, mask=pil_image.split()[-1])
                pil_image = background
            elif pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")

            if downscale_factor < 0.999:
                new_width = max(1, int(pil_image.width * downscale_factor))
                new_height = max(1, int(pil_image.height * downscale_factor))
                if (new_width, new_height) != pil_image.size:
                    pil_image = pil_image.resize((new_width, new_height), Image.LANCZOS)

            buffer = io.BytesIO()
            try:
                pil_image.save(buffer, format="JPEG", optimize=True, quality=quality)
            except OSError:
                continue

            image_bytes = buffer.getvalue()
            replace_stream = getattr(pdf_image, "replace_stream", None)
            if callable(replace_stream):
                replace_stream(image_bytes, pikepdf.Name("/DCTDecode"))
            else:
                try:
                    pdf_image.replace(image_bytes, pikepdf.Name("/DCTDecode"))
                except AttributeError:
                    continue


def compress_pdf(
    source_path: Path,
    target_path: Path,
    target_size_mb: float,
    *,
    min_quality: int = 20,
    max_quality: int = 95,
    max_iterations: int = 6,
    preserve_metadata: bool = False,
) -> CompressionResult:
    target_bytes = max(int(target_size_mb * 1024 * 1024), 0)
    original_size = source_path.stat().st_size

    if target_bytes > 0 and original_size <= target_bytes:
        shutil.copyfile(source_path, target_path)
        return CompressionResult(target_path, original_size)

    best_output: Optional[Path] = None
    best_diff = float("inf")
    best_size = original_size

    best_under_target_bytes: Optional[bytes] = None
    best_under_target_size: Optional[int] = None
    best_under_target_diff: Optional[int] = None

    low, high = min_quality, max_quality
    base_downscale = _calculate_base_downscale(original_size, target_bytes)

    for iteration in range(1, max_iterations + 1):
        quality = max(min_quality, min(max_quality, (low + high) // 2))
        iteration_path = target_path.with_name(f"{target_path.stem}.tmp.{iteration}{target_path.suffix}")

        downscale_factor = _calculate_iteration_downscale(quality, min_quality, max_quality, base_downscale)

        with pikepdf.open(source_path) as pdf:
            try:
                _recompress_images(pdf, quality, downscale_factor=downscale_factor)
            except Exception:
                pass

            if not preserve_metadata:
                try:
                    pdf.docinfo.clear()
                except (AttributeError, ValueError):
                    pass

            pdf.save(
                iteration_path,
                linearize=True,
                compress_streams=True,
                object_stream_mode=pikepdf.ObjectStreamMode.generate,
            )

        compressed_size = iteration_path.stat().st_size
        diff = abs(target_bytes - compressed_size) if target_bytes > 0 else compressed_size

        if diff < best_diff:
            shutil.copyfile(iteration_path, target_path)
            best_output = target_path
            best_diff = diff
            best_size = compressed_size

        if target_bytes > 0 and compressed_size <= target_bytes:
            under_diff = target_bytes - compressed_size
            if best_under_target_diff is None or under_diff < best_under_target_diff:
                best_under_target_bytes = iteration_path.read_bytes()
                best_under_target_size = compressed_size
                best_under_target_diff = under_diff

        if target_bytes == 0:
            iteration_path.unlink(missing_ok=True)
            continue

        if compressed_size > target_bytes:
            high = quality - 1
        else:
            low = quality + 1

        tolerance = int(target_bytes * 0.10)
        should_break = False
        if best_under_target_diff is not None:
            if best_under_target_diff <= tolerance or iteration == max_iterations:
                should_break = True

        iteration_path.unlink(missing_ok=True)

        if low > high or should_break:
            break

    final_size = original_size

    if best_under_target_bytes is not None and best_under_target_size is not None:
        with open(target_path, "wb") as f:
            f.write(best_under_target_bytes)
        best_output = target_path
        final_size = best_under_target_size
    elif best_output is not None and target_path.exists():
        final_size = best_size
    else:
        shutil.copyfile(source_path, target_path)
        best_output = target_path
        final_size = original_size

    if target_bytes > 0 and final_size > target_bytes:
        fallback_scale = base_downscale
        previous_scale = None
        attempt = 0

        while final_size > target_bytes:
            attempt += 1
            if previous_scale is None:
                fallback_scale = max(0.3, min(0.95, fallback_scale * 0.85 if fallback_scale > 0 else 0.85))
            else:
                fallback_scale = max(0.3, fallback_scale * 0.85)

            if previous_scale is not None and math.isclose(previous_scale, fallback_scale, rel_tol=1e-3):
                break

            previous_scale = fallback_scale

            if fallback_scale >= 0.999:
                break

            fallback_path = target_path.with_name(
                f"{target_path.stem}.fallback.{attempt}{target_path.suffix}"
            )

            with pikepdf.open(source_path) as pdf:
                try:
                    _recompress_images(pdf, min_quality, downscale_factor=fallback_scale)
                except Exception:
                    pass

                if not preserve_metadata:
                    try:
                        pdf.docinfo.clear()
                    except (AttributeError, ValueError):
                        pass

                pdf.save(
                    fallback_path,
                    linearize=True,
                    compress_streams=True,
                    object_stream_mode=pikepdf.ObjectStreamMode.generate,
                )

            fallback_size = fallback_path.stat().st_size
            fallback_diff = abs(target_bytes - fallback_size)

            if fallback_diff < best_diff:
                shutil.copyfile(fallback_path, target_path)
                best_output = target_path
                best_diff = fallback_diff
                best_size = fallback_size
                final_size = fallback_size

            if fallback_size <= target_bytes:
                under_diff = target_bytes - fallback_size
                if best_under_target_diff is None or under_diff < best_under_target_diff:
                    best_under_target_bytes = fallback_path.read_bytes()
                    best_under_target_size = fallback_size
                    best_under_target_diff = under_diff

            fallback_path.unlink(missing_ok=True)

            if fallback_size <= target_bytes or math.isclose(fallback_scale, 0.3, abs_tol=1e-3):
                break

        if best_under_target_bytes is not None and best_under_target_size is not None:
            with open(target_path, "wb") as f:
                f.write(best_under_target_bytes)
            best_output = target_path
            final_size = best_under_target_size
        elif best_output is not None and target_path.exists():
            final_size = best_size

    if final_size > original_size:
        shutil.copyfile(source_path, target_path)
        final_size = original_size

    return CompressionResult(best_output, final_size)
