# ==========================================================
# Book OCR Program
#
# Version : V0.4
# Date    : 2026-06-09 21:00
#
# Change Log
# V0.1 PDF -> PNG 변환
# V0.2 OCR 전처리(CLAHE, Adaptive Threshold)
# V0.3 중앙 고정 분할
# V0.4 페이지 여백 자동 제거(Auto Crop)
# ==========================================================

from pathlib import Path
import fitz
import cv2
import numpy as np

INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")


# ----------------------------------------------------------
# PDF -> PNG
# ----------------------------------------------------------
def pdf_to_images(pdf_path, pages_dir):

    doc = fitz.open(pdf_path)

    print(f"\n[{pdf_path.name}] pages={len(doc)}")

    for i in range(len(doc)):

        page = doc[i]

        pix = page.get_pixmap(
            matrix=fitz.Matrix(2.5, 2.5),
            alpha=False
        )

        out_file = pages_dir / f"page_{i+1:04d}.png"

        pix.save(out_file)

        print(f"saved : {out_file.name}")


# ----------------------------------------------------------
# OCR 전처리
# ----------------------------------------------------------
def preprocess_image(img):

    gray = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2GRAY
    )

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


# ----------------------------------------------------------
# 페이지 여백 제거
# ----------------------------------------------------------
def crop_margin(img):

    if len(img.shape) == 3:
        gray = cv2.cvtColor(
            img,
            cv2.COLOR_BGR2GRAY
        )
    else:
        gray = img.copy()

    # 검은 영역 찾기
    coords = cv2.findNonZero(
        255 - gray
    )

    if coords is None:
        return img

    x, y, w, h = cv2.boundingRect(coords)

    pad = 20

    x = max(0, x - pad)
    y = max(0, y - pad)

    w = min(
        img.shape[1] - x,
        w + pad * 2
    )

    h = min(
        img.shape[0] - y,
        h + pad * 2
    )

    cropped = img[
        y:y+h,
        x:x+w
    ]

    return cropped


# ----------------------------------------------------------
# 좌우 페이지 분리
# ----------------------------------------------------------
def split_page(img, split_dir, stem):

    h, w = img.shape[:2]

    # 단일 페이지
    if w < h * 1.2:

        cropped = crop_margin(img)

        cv2.imwrite(
            str(split_dir / f"{stem}.png"),
            cropped
        )

        return

    center = w // 2

    left = img[:, :center]
    right = img[:, center:]

    # 여백 제거
    left = crop_margin(left)
    right = crop_margin(right)

    cv2.imwrite(
        str(split_dir / f"{stem}_L.png"),
        left
    )

    cv2.imwrite(
        str(split_dir / f"{stem}_R.png"),
        right
    )


# ----------------------------------------------------------
# 책 처리
# ----------------------------------------------------------
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

    for page_file in sorted(
        pages_dir.glob("*.png")
    ):

        img = cv2.imread(
            str(page_file)
        )

        if img is None:
            continue

        cleaned = preprocess_image(img)

        cv2.imwrite(
            str(clean_dir / page_file.name),
            cleaned
        )

        split_page(
            cleaned,
            split_dir,
            page_file.stem
        )

        print(
            f"processed : {page_file.name}"
        )


# ----------------------------------------------------------
# Main
# ----------------------------------------------------------
def main():

    OUTPUT_DIR.mkdir(
        exist_ok=True
    )

    pdfs = list(
        INPUT_DIR.glob("*.pdf")
    )

    if not pdfs:
        print("input 폴더에 PDF가 없습니다.")
        return

    for pdf in pdfs:
        process_book(pdf)

    print("\n=== 완료 ===")


if __name__ == "__main__":
    main()