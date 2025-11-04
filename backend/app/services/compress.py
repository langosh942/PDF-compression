from __future__ import annotations

import io
import shutil
from pathlib import Path
from typing import Optional

import pikepdf
from PIL import Image


class CompressionResult:
    def __init__(self, output_path: Path, size_bytes: int):
        self.output_path = output_path
        self.size_bytes = size_bytes


def _recompress_images(pdf: pikepdf.Pdf, quality: int) -> None:
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

            buffer = io.BytesIO()
            try:
                pil_image.save(buffer, format="JPEG", optimize=True, quality=quality)
            except OSError:
                # Some images cannot be optimized; skip them
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
    target_bytes = int(target_size_mb * 1024 * 1024)
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

    for iteration in range(1, max_iterations + 1):
        quality = max(min_quality, min(max_quality, (low + high) // 2))
        iteration_path = target_path.with_name(f"{target_path.stem}.tmp.{iteration}{target_path.suffix}")

        with pikepdf.open(source_path) as pdf:
            try:
                _recompress_images(pdf, quality)
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
        diff = abs(target_bytes - compressed_size)

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

        tolerance = int(target_bytes * 0.05)
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

    if final_size > original_size:
        shutil.copyfile(source_path, target_path)
        final_size = original_size

    return CompressionResult(best_output, final_size)
