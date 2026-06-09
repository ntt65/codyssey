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


def split_page(img_path, out_dir):
    img = cv2.imread(str(img_path))

    h, w = img.shape[:2]

    # 가로가 세로보다 훨씬 크면 펼침면으로 판단
    if w > h * 1.2:

        center = w // 2

        left = img[:, :center]
        right = img[:, center:]

        cv2.imwrite(
            str(out_dir / f"{img_path.stem}_L.png"),
            left
        )

        cv2.imwrite(
            str(out_dir / f"{img_path.stem}_R.png"),
            right
        )

        print(f"split: {img_path.name}")

    else:
        cv2.imwrite(
            str(out_dir / img_path.name),
            img
        )

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    pdfs = list(INPUT_DIR.glob("*.pdf"))
    split_dir = book_dir / "split"
    split_dir.mkdir(exist_ok=True)

    if not pdfs:
        print("input 폴더에 PDF가 없습니다.")
        return

    for pdf in pdfs:
        pdf_to_images(pdf)


if __name__ == "__main__":
    main()