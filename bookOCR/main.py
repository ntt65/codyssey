from pathlib import Path
import fitz

INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")


def pdf_to_images(pdf_path):
    book_dir = OUTPUT_DIR / pdf_path.stem
    pages_dir = book_dir / "pages"

    pages_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)

    print(f"{pdf_path.name} : {len(doc)} pages")

    for page_num in range(len(doc)):
        page = doc[page_num]

        pix = page.get_pixmap(
            matrix=fitz.Matrix(2, 2),
            alpha=False
        )

        outfile = pages_dir / f"page_{page_num+1:04d}.png"

        pix.save(outfile)

        print(f"saved {outfile.name}")


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    pdfs = list(INPUT_DIR.glob("*.pdf"))

    if not pdfs:
        print("input 폴더에 PDF가 없습니다.")
        return

    for pdf in pdfs:
        pdf_to_images(pdf)


if __name__ == "__main__":
    main()