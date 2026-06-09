from pathlib import Path
import fitz
import cv2
import numpy as np

INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")


# -------------------------
# PDF -> 이미지
# -------------------------
def pdf_to_images(pdf_path, pages_dir):
    doc = fitz.open(pdf_path)

    print(f"\n[{pdf_path.name}] pages: {len(doc)}")

    for i in range(len(doc)):
        page = doc[i]

        pix = page.get_pixmap(
            matrix=fitz.Matrix(2.5, 2.5),
            alpha=False
        )

        out = pages_dir / f"page_{i+1:04d}.png"
        pix.save(out)

        print(f"saved {out.name}")


# -------------------------
# 전처리
# -------------------------
def preprocess_image(img):

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    gray = clahe.apply(gray)

    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    bw = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        25,
        15
    )

    return bw


# -------------------------
# 중앙 골(gutter) 찾기
# -------------------------
def find_gutter(img):

    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    h, w = gray.shape
    center = w // 2

    search = int(w * 0.2)

    start = max(0, center - search)
    end = min(w, center + search)

    roi = gray[:, start:end]

    hist = np.mean(roi, axis=0)

    gutter = np.argmin(hist)

    return start + gutter


# -------------------------
# 좌우 분리
# -------------------------
def split_page(img, split_dir, stem):

    h, w = img.shape[:2]

    # 단일 페이지
    if w < h * 1.2:
        cv2.imwrite(str(split_dir / f"{stem}.png"), img)
        return

    gutter = find_gutter(img)

    left = img[:, :gutter]
    right = img[:, gutter:]

    cv2.imwrite(str(split_dir / f"{stem}_L.png"), left)
    cv2.imwrite(str(split_dir / f"{stem}_R.png"), right)


# -------------------------
# 책 처리
# -------------------------
def process_book(pdf_path):

    book_dir = OUTPUT_DIR / pdf_path.stem

    pages_dir = book_dir / "pages"
    clean_dir = book_dir / "clean"
    split_dir = book_dir / "split"

    pages_dir.mkdir(parents=True, exist_ok=True)
    clean_dir.mkdir(exist_ok=True)
    split_dir.mkdir(exist_ok=True)

    pdf_to_images(pdf_path, pages_dir)

    for page_file in sorted(pages_dir.glob("*.png")):

        img = cv2.imread(str(page_file))

        cleaned = preprocess_image(img)

        cv2.imwrite(str(clean_dir / page_file.name), cleaned)

        split_page(cleaned, split_dir, page_file.stem)

        print(f"processed {page_file.name}")


# -------------------------
# main
# -------------------------
def main():

    OUTPUT_DIR.mkdir(exist_ok=True)

    pdfs = list(INPUT_DIR.glob("*.pdf"))

    if not pdfs:
        print("input 폴더에 PDF 없음")
        return

    for pdf in pdfs:
        process_book(pdf)

    print("\n완료")


if __name__ == "__main__":
    main()