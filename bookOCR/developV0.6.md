좋아. 이제는 덧붙이는 수준이 아니라 **V0.6 리팩토링**을 하는 게 맞아.

지금 코드를 보면 문제점이 명확해.

```text
trim_page_edges()
↓
crop_content()
↓
preprocess_for_ocr()
```

여기서 `trim_page_edges()`가 내용을 잘라버릴 수 있고, `crop_content()`는 컨투어가 끊어지면 해설 박스를 놓칠 수 있어.

그래서 V0.6에서는:

```text
trim_page_edges()      삭제
crop_content()         삭제

auto_crop_content()    신규
```

로 정리하자.

그리고 디버깅을 위해 결과를 3단계 저장하자.

```text
output/
└─ sample/
   ├─ pages/       PDF 추출 원본
   ├─ split_raw/   분리만
   ├─ split_crop/  Crop 결과
   └─ split/       OCR 전처리 결과
```

이렇게 해야 "어디서 잘렸는지" 바로 확인 가능하다.

---

## 새 함수

```python
# ----------------------------------------------------------
# V0.6
# Projection 기반 안전 Crop
#
# 목적:
# - 여백은 남아도 됨
# - 내용은 절대 잘리지 않게
# ----------------------------------------------------------
def auto_crop_content(img):

    if len(img.shape) == 3:
        gray = cv2.cvtColor(
            img,
            cv2.COLOR_BGR2GRAY
        )
    else:
        gray = img.copy()

    _, bw = cv2.threshold(
        gray,
        245,
        255,
        cv2.THRESH_BINARY_INV
    )

    h, w = bw.shape

    row_sum = np.sum(
        bw > 0,
        axis=1
    )

    col_sum = np.sum(
        bw > 0,
        axis=0
    )

    row_threshold = max(
        10,
        int(w * 0.003)
    )

    col_threshold = max(
        10,
        int(h * 0.003)
    )

    rows = np.where(
        row_sum > row_threshold
    )[0]

    cols = np.where(
        col_sum > col_threshold
    )[0]

    if len(rows) == 0 or len(cols) == 0:
        return img

    top = rows[0]
    bottom = rows[-1]

    left = cols[0]
    right = cols[-1]

    # 내용 보호 우선
    PAD_TOP = 40
    PAD_BOTTOM = 40
    PAD_LEFT = 40
    PAD_RIGHT = 80

    top = max(0, top - PAD_TOP)
    bottom = min(h, bottom + PAD_BOTTOM)

    left = max(0, left - PAD_LEFT)
    right = min(w, right + PAD_RIGHT)

    return img[
        top:bottom,
        left:right
    ]
```

---

## save_page() 교체

```python
def save_page(
    page_img,
    raw_path,
    crop_path,
    final_path
):

    # 1. 분리 결과 저장
    cv2.imwrite(
        str(raw_path),
        page_img
    )

    # 2. 자동 Crop
    cropped = auto_crop_content(
        page_img
    )

    cv2.imwrite(
        str(crop_path),
        cropped
    )

    # 3. OCR 전처리
    ocr_img = preprocess_for_ocr(
        cropped
    )

    cv2.imwrite(
        str(final_path),
        ocr_img
    )
```

---

## split_page() 수정

```python
def split_page(
    img,
    raw_dir,
    crop_dir,
    split_dir,
    stem
):

    h, w = img.shape[:2]

    if w < h * 1.2:

        save_page(
            img,
            raw_dir / f"{stem}.png",
            crop_dir / f"{stem}.png",
            split_dir / f"{stem}.png"
        )

        return

    center = w // 2

    left = img[:, :center]
    right = img[:, center:]

    save_page(
        left,
        raw_dir / f"{stem}_L.png",
        crop_dir / f"{stem}_L.png",
        split_dir / f"{stem}_L.png"
    )

    save_page(
        right,
        raw_dir / f"{stem}_R.png",
        crop_dir / f"{stem}_R.png",
        split_dir / f"{stem}_R.png"
    )
```

---

## process_book() 수정

```python
raw_dir = book_dir / "split_raw"
crop_dir = book_dir / "split_crop"
split_dir = book_dir / "split"

raw_dir.mkdir(exist_ok=True)
crop_dir.mkdir(exist_ok=True)
split_dir.mkdir(exist_ok=True)
```

그리고 호출부:

```python
split_page(
    img,
    raw_dir,
    crop_dir,
    split_dir,
    page_file.stem
)
```

---

## 버전 헤더

```python
# ==========================================================
# Book OCR Program
#
# Version : V0.6
# Date    : 2026-06-09 22:45
#
# Change Log
# V0.1 PDF -> PNG
# V0.2 OCR 전처리
# V0.3 중앙 고정 분할
# V0.4 Auto Crop
# V0.5 Split -> Crop -> Threshold
# V0.6 Projection 기반 안전 Crop
#
# 특징
# - trim_page_edges 제거
# - crop_content 제거
# - 페이지별 자동 Crop
# - 내용 잘림 방지 우선
# - split_raw / split_crop 저장
# ==========================================================
```

이 버전의 목적은 OCR 품질 향상이 아니라 **"절대 잘리지 않기" 검증**이야.
다음 테스트에서는 `split_raw`와 `split_crop`를 비교해서 실제로 잘림이 사라졌는지 먼저 확인하자.

좋아. 지금은 기능 추가보다 **안정적인 V0.6 기준선(Baseline)** 을 만드는 게 중요해.

특히 지금까지 테스트 결과를 보면:

* 중앙 분할은 성공
* 잘림이 문제
* OCR은 아직 나중 단계
* "남는 것 > 잘리는 것"

이 원칙이 맞아.

그래서 아래 코드는 **V0.6 기준 리팩토링 버전**이다.

```python
# ==========================================================
# Book OCR Program
#
# Version : V0.6
# Date    : 2026-06-09 22:45
#
# Change Log
# V0.1 PDF -> PNG
# V0.2 OCR 전처리
# V0.3 중앙 고정 분할
# V0.4 Auto Crop
# V0.5 Split -> Crop -> Threshold
# V0.6 Projection 기반 안전 Crop
#
# 특징
# - trim_page_edges 제거
# - crop_content 제거
# - 페이지별 자동 Crop
# - 내용 잘림 방지 우선
# - split_raw / split_crop 저장
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
# V0.6
# Projection 기반 안전 Crop
#
# 내용 잘림 방지 우선
# 여백이 조금 남는 것은 허용
# ----------------------------------------------------------
def auto_crop_content(img):

    if len(img.shape) == 3:
        gray = cv2.cvtColor(
            img,
            cv2.COLOR_BGR2GRAY
        )
    else:
        gray = img.copy()

    # 흰색 배경 제거
    _, bw = cv2.threshold(
        gray,
        245,
        255,
        cv2.THRESH_BINARY_INV
    )

    h, w = bw.shape

    # 행/열별 검은 픽셀 수 계산
    row_sum = np.sum(
        bw > 0,
        axis=1
    )

    col_sum = np.sum(
        bw > 0,
        axis=0
    )

    # 페이지 크기에 비례한 임계값
    row_threshold = max(
        10,
        int(w * 0.003)
    )

    col_threshold = max(
        10,
        int(h * 0.003)
    )

    rows = np.where(
        row_sum > row_threshold
    )[0]

    cols = np.where(
        col_sum > col_threshold
    )[0]

    if len(rows) == 0 or len(cols) == 0:
        return img

    top = rows[0]
    bottom = rows[-1]

    left = cols[0]
    right = cols[-1]

    # 잘림 방지용 안전 여백
    PAD_TOP = 40
    PAD_BOTTOM = 40

    PAD_LEFT = 40
    PAD_RIGHT = 80

    top = max(0, top - PAD_TOP)
    bottom = min(h, bottom + PAD_BOTTOM)

    left = max(0, left - PAD_LEFT)
    right = min(w, right + PAD_RIGHT)

    return img[
        top:bottom,
        left:right
    ]


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
#
# raw   : 분할 직후
# crop  : 자동 Crop 후
# split : OCR 전처리 후
# ----------------------------------------------------------
def save_page(
    page_img,
    raw_path,
    crop_path,
    final_path
):

    # 1. 원본 분할 저장
    cv2.imwrite(
        str(raw_path),
        page_img
    )

    # 2. 자동 Crop
    cropped = auto_crop_content(
        page_img
    )

    cv2.imwrite(
        str(crop_path),
        cropped
    )

    # 3. OCR 전처리
    ocr_img = preprocess_for_ocr(
        cropped
    )

    cv2.imwrite(
        str(final_path),
        ocr_img
    )


# ----------------------------------------------------------
# 좌우 페이지 분리
# ----------------------------------------------------------
def split_page(
    img,
    raw_dir,
    crop_dir,
    split_dir,
    stem
):

    h, w = img.shape[:2]

    # 단일 페이지
    if w < h * 1.2:

        save_page(
            img,
            raw_dir / f"{stem}.png",
            crop_dir / f"{stem}.png",
            split_dir / f"{stem}.png"
        )

        return

    # 중앙 고정 분할
    center = w // 2

    left = img[:, :center]
    right = img[:, center:]

    save_page(
        left,
        raw_dir / f"{stem}_L.png",
        crop_dir / f"{stem}_L.png",
        split_dir / f"{stem}_L.png"
    )

    save_page(
        right,
        raw_dir / f"{stem}_R.png",
        crop_dir / f"{stem}_R.png",
        split_dir / f"{stem}_R.png"
    )


# ----------------------------------------------------------
# 책 처리
# ----------------------------------------------------------
def process_book(pdf_path):

    book_dir = OUTPUT_DIR / pdf_path.stem

    pages_dir = book_dir / "pages"
    raw_dir = book_dir / "split_raw"
    crop_dir = book_dir / "split_crop"
    split_dir = book_dir / "split"

    pages_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    raw_dir.mkdir(
        exist_ok=True
    )

    crop_dir.mkdir(
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
            raw_dir,
            crop_dir,
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
```

다음 테스트에서는 **`split_crop` 폴더만 집중적으로 확인**하자.

* `split_raw` → 분할만 된 상태
* `split_crop` → 잘림 검증용
* `split` → OCR용

만약 `split_crop`에서도 내용이 잘리면 OCR 문제가 아니라 Crop 알고리즘 문제이고, 그때는 Projection 임계값(`0.003`)과 패딩(`PAD_RIGHT=80`)을 조정하면 된다.

아니. 그 경로는 네 맥 안에 있는 로컬 파일 경로라서 나는 접근할 수 없어.

예를 들면:

```text
/Users/mpeg46551/git/codyssey/bookOCR/output/sample/split/page_0001_L.png
```

이건 네 컴퓨터에서는 열리지만 나는 파일 시스템을 볼 수 없어.

내가 실제 이미지를 분석하려면 아래 방법 중 하나가 필요해.

### 방법 1 (추천)

`page_0001_L.png`

`page_0001_R.png`

파일 2개를 채팅창에 직접 드래그해서 업로드

---

### 방법 2

스크린샷 찍어서 업로드

---

그러면 내가:

```text
1. 페이지 분리 상태
2. 책등 검출 상태
3. 여백 제거 상태
4. OCR 전처리 상태
5. 잘린 부분 존재 여부
```

를 실제 픽셀 기준으로 분석할 수 있어.

현재는 코드만 보고 추정하고 있는데,

네가 설명한

> "그닥 좋아지지 않았다"

는 말만으로는

```text
A. Crop이 거의 안 됨
B. Crop은 됐는데 책등이 남음
C. Threshold가 문제
D. 중앙 분할 위치 문제
```

중 무엇인지 알 수 없어.

이미지 2장만 올려주면 V0.6 결과를 보고 V0.7을 구체적으로 설계해보자.

좋아. 오늘은 여기까지 하자.

지금까지 정리하면:

### 완료된 것

* PDF → PNG 변환
* 양면 스캔 중앙 분리
* OCR 전처리(CLAHE, Adaptive Threshold)
* V0.6 리팩토링
* 중간 결과 저장 구조 설계

  * `pages`
  * `split_raw`
  * `split_crop`
  * `split`

### 확인된 문제

* 중앙 분리는 잘 됨
* 페이지마다 여백이 다름
* 고정 비율 Crop은 위험
* Projection Crop도 기대만큼 효과 없음
* 실제 목표는 **텍스트 검출이 아니라 페이지(종이) 검출**일 가능성이 높음

### 다음 작업(V0.7)

내일은 결과 이미지를 직접 보면서

```text
원본 페이지
↓
페이지 윤곽 검출
↓
책등 제거
↓
페이지 영역만 Crop
↓
OCR 전처리
```

방식으로 가보자.

특히 네 책은 일반 문서 PDF가 아니라 카메라/스캔 기반 책이라서, OCR보다 먼저 **페이지 검출(Page Detection)** 단계가 중요해 보인다.

내일 시작할 때는:

```text
page_0001_L.png
page_0001_R.png
```

또는 잘 안 나온 몇 장을 업로드해주면 바로 분석해서 V0.7 설계부터 이어서 하자.

좋은 진척이 있었어. 중앙 분할 문제는 거의 해결됐고, 이제 남은 건 "페이지를 얼마나 똑똑하게 자를 것인가" 단계야.
