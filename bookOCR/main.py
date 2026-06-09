from pathlib import Path
import fitz
import cv2
import numpy as np

INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")


def pdf_to_images(pdf_path, pages_dir):
    doc = fitz.open(pdf_path)

    print(f"\n[{pdf_path.name}] {len(doc)} pages")

    for i in range(len(doc)):
        page = doc[i]

        pix = page.get_pixmap(
            matrix=fitz.Matrix(2.5, 2.5),
            alpha=False
        )

        outfile = pages_dir / f"page_{i+1:04d}.png"
        pix.save(outfile)

        print(f"saved: {outfile.name}")


def preprocess_image(img):

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    gray = clahe.apply(gray)

    gray = cv2.GaussianBlur(
        gray,
        (3, 3),
        0
    )

    bw = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        25,
        15
    )

    return bw


def find_gutter(img):

    if len(img.shape) == 3:
        gray = cv2.cvtColor(
            img,
            cv2.COLOR_BGR2GRAY
        )
    else:
        gray = img

    h, w = gray.shape

    center = w // 2

    search_width = int(w * 0.2)

    start = max(0, center - search_width)
    end = min(w, center + search_width)

    roi = gray[:, start:end]

    vertical_hist = np.mean(
        roi,
        axis=0
    )

    gutter = np.argmin(vertical_hist)

    return start + gutter


def split_book_page(img, split_dir, stem):

    h, w = img.shape[:2]

    if w < h * 1.2:
        cv2.imwrite(
            str(split_dir / f"{stem}.png"),
            img
        )
        return

    gutter = find_gutter(img)

    left = img[:, :gutter]
    right = img[:, gutter:]

    cv2.imwrite(
        str(split_dir / f"{stem}_L.png"),
        left
    )

    cv2.imwrite(
        str(split_dir / f"{stem}_R.png"),
        right
    )


def process_book(pdf_path):

    book_dir = OUTPUT_DIR / pdf_path.stem

    pages_dir = book_dir / "pages"
    clean_dir = book_dir / "clean"
    split_dir = book_dir / "split"

    pages_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    clean_dir.mkdir(
        exist_ok=True
    )

    split_dir.mkdir(
        exist_ok=True
    )

    pdf_to_images(
        pdf_path,
        pages_dir
    )

    page_files = sorted(
        pages_dir.glob("*.png")
    )

    for page in page_files:

        img = cv2.imread(
            str(page)
        )

        cleaned = preprocess_image(
            img
        )

        clean_file = (
            clean_dir /
            page.name
        )

        cv2.imwrite(
            str(clean_file),
            cleaned
        )

        split_book_page(
            cleaned,
            split_dir,
            page.stem
        )

        print(
            f"processed: {page.name}"
        )


def main():

    OUTPUT_DIR.mkdir(
        exist_ok=True
    )

    pdfs = list(
        INPUT_DIR.glob("*.pdf")
    )

    if not pdfs:
        print(
            "input 폴더에 PDF가 없습니다."
        )
        return

    for pdf in pdfs:
        process_book(pdf)

    print("\n완료")


if __name__ == "__main__":
    main()