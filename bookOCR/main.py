# ==========================================================
# Book OCR Program
#
# Version : V0.5
# Date    : 2026-06-09 21:30
#
# Change Log
# V0.1 PDF -> PNG 변환
# V0.2 OCR 전처리(CLAHE, Adaptive Threshold)
# V0.3 중앙 고정 분할
# V0.4 페이지 여백 자동 제거(Auto Crop)
# V0.5 전처리 순서 변경
#      Split -> Crop -> Threshold
#      페이지 외곽 제거 추가
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
# 페이지 외곽 제거
# ----------------------------------------------------------
def trim_page_edges(img):

    h, w = img.shape[:2]

    left = int(w * 0.03)
    right = int(w * 0.03)

    top = int(h * 0.02)
    bottom = int(h * 0.05)

    return img[
        top:h-bottom,
        left:w-right
    ]


# ----------------------------------------------------------
# 본문 영역 찾기
# ----------------------------------------------------------
def crop_content(img):

    if len(img.shape) == 3:
        gray = cv2.cvtColor(
            img,
            cv2.COLOR_BGR2GRAY
        )
    else:
        gray = img.copy()

    blur = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    _, mask = cv2.threshold(
        blur,
        220,
        255,
        cv2.THRESH_BINARY_INV
    )

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (15, 15)
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel
    )

    coords = cv2.findNonZero(mask)

    if coords is None:
        return img

    x, y, w, h = cv2.boundingRect(coords)

    pad = 20

    x = max(0, x - pad)
    y = max(0, y - pad)

    w = min(
        gray.shape[1] - x,
        w + pad * 2
    )

    h = min(
        gray.shape[0] - y,
        h + pad * 2
    )

    return img[y:y+h, x:x+w]


# ----------------------------------------------------------
# OCR 전처리
# ----------------------------------------------------------
def preprocess_for_ocr(img):

    if len(img.shape) == 3:
        gray = cv2.cvtColor(
            img,
            cv2.COLOR_BGR2GRAY
        )
    else:
        gray = img.copy()

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    gray = clahe.apply(gray)

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
# 페이지 저장
# ----------------------------------------------------------
def save_page(page_img, out_path):

    page_img = trim_page_edges(page_img)

    page_img = crop_content(page_img)

    ocr_img = preprocess_for_ocr(page_img)

    cv2.imwrite(
        str(out_path),
        ocr_img
    )


# ----------------------------------------------------------
# 좌우 분리
# ----------------------------------------------------------
def split_page(img, split_dir, stem):

    h, w = img.shape[:2]

    if w < h * 1.2:

        save_page(
            img,
            split_dir / f"{stem}.png"
        )

        return

    center = w // 2

    left = img[:, :center]
    right = img[:, center:]

    save_page(
        left,
        split_dir / f"{stem}_L.png"
    )

    save_page(
        right,
        split_dir / f"{stem}_R.png"
    )


# ----------------------------------------------------------
# 책 처리
# ----------------------------------------------------------
def process_book(pdf_path):

    book_dir = OUTPUT_DIR / pdf_path.stem

    pages_dir = book_dir / "pages"
    split_dir = book_dir / "split"

    pages_dir.mkdir(
        parents=True,
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

        split_page(
            img,
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