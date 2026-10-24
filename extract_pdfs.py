
import json
import re
import sys
from pathlib import Path

import pymupdf


BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "portuguese-original-pdf"
OUTPUT_DIR = BASE_DIR / "extracted"


def safe_name(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    return name.strip(" .") or "unnamed"


def json_dump(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def extract_pdf(pdf_path: Path) -> None:
    book_name = safe_name(pdf_path.stem)
    book_dir = OUTPUT_DIR / book_name
    pages_dir = book_dir / "pages"
    images_dir = book_dir / "images"

    pages_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

    markdown_parts = []
    metadata = {
        "source_file": pdf_path.name,
        "page_count": 0,
        "metadata": {},
        "toc": [],
        "fonts": [],
        "pages": [],
    }

    font_registry = {}
    extracted_images = {}

    print(f"Processing: {pdf_path.name}")

    with pymupdf.open(pdf_path) as doc:
        metadata["page_count"] = len(doc)
        metadata["metadata"] = doc.metadata or {}
        metadata["toc"] = doc.get_toc()

        for page_index, page in enumerate(doc):
            page_number = page_index + 1
            page_dict = page.get_text("dict", sort=True)
            page_blocks = []
            markdown_page = [
                f"<!-- Original PDF page: {page_number} -->",
                f"# Page {page_number}",
                "",
            ]

            for block_index, block in enumerate(page_dict["blocks"]):
                if block.get("type") == 1:
                    image_bytes = block.get("image")
                    if not image_bytes:
                        continue

                    image_ext = block.get("ext", "bin").lower()
                    image_key = (
                        page_number,
                        block_index,
                        block.get("bbox"),
                    )
                    image_name = (
                        f"page-{page_number:04d}-"
                        f"block-{block_index:03d}.{image_ext}"
                    )
                    image_path = images_dir / image_name

                    image_path.write_bytes(image_bytes)
                    extracted_images[str(image_key)] = image_name

                    page_blocks.append({
                        "type": "image",
                        "bbox": block.get("bbox"),
                        "file": f"images/{image_name}",
                        "width": block.get("width"),
                        "height": block.get("height"),
                    })
                    markdown_page.append(
                        f"![Image on page {page_number}]"
                        f"(images/{image_name})"
                    )
                    markdown_page.append("")
                    continue

                if block.get("type") != 0:
                    continue

                lines = []
                block_spans = []

                for line in block.get("lines", []):
                    line_text = "".join(
                        span.get("text", "")
                        for span in line.get("spans", [])
                    )
                    if line_text:
                        lines.append(line_text)

                    for span in line.get("spans", []):
                        if not span.get("text", "").strip():
                            continue

                        font_name = span.get("font", "unknown")
                        font_registry[font_name] = {
                            "name": font_name,
                            "size": span.get("size"),
                            "flags": span.get("flags"),
                            "color": span.get("color"),
                        }

                        block_spans.append({
                            "text": span.get("text", ""),
                            "font": font_name,
                            "size": span.get("size"),
                            "flags": span.get("flags"),
                            "color": span.get("color"),
                            "bbox": span.get("bbox"),
                            "origin": span.get("origin"),
                        })

                text = "\n".join(lines).strip()
                if not text:
                    continue

                page_blocks.append({
                    "type": "text",
                    "bbox": block.get("bbox"),
                    "text": text,
                    "spans": block_spans,
                })

                markdown_page.append(text)
                markdown_page.append("")

            page_json = {
                "page_number": page_number,
                "width": page.rect.width,
                "height": page.rect.height,
                "rotation": page.rotation,
                "blocks": page_blocks,
            }

            json_dump(
                pages_dir / f"page-{page_number:04d}.json",
                page_json,
            )

            markdown_parts.append("\n".join(markdown_page))

            metadata["pages"].append({
                "page_number": page_number,
                "width": page.rect.width,
                "height": page.rect.height,
                "rotation": page.rotation,
                "block_count": len(page_blocks),
            })

        metadata["fonts"] = list(font_registry.values())

    (book_dir / "document.md").write_text(
        "\n\n".join(markdown_parts),
        encoding="utf-8",
    )
    json_dump(book_dir / "metadata.json", metadata)

    print(f"Finished: {pdf_path.name} -> {book_dir}")


def main() -> None:
    if not INPUT_DIR.is_dir():
        print(f"Input directory not found: {INPUT_DIR}")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(
        path for path in INPUT_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() == ".pdf"
    )

    if not pdf_files:
        print(f"No PDF files found in {INPUT_DIR}")
        return

    for pdf_path in pdf_files:
        try:
            extract_pdf(pdf_path)
        except Exception as exc:
            print(f"ERROR processing {pdf_path}: {exc}")

    print("Extraction completed.")


if __name__ == "__main__":
    main()
