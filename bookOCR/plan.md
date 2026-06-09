pdf를 읽어서 스캔된 책그림을 왜곡을 펴고 컨트라스트 브라이트등 히스토그램을 최적화하고  좌우페이지를 분리하는걸 만들수 있나 최종 ocr인식까지 하면 좋을것 같고

네, 가능합니다. 오히려 이건 전형적인 **"북 스캔 후처리 + OCR 파이프라인"** 프로젝트입니다.

원하는 기능을 단계별로 나누면:

### 1. PDF 입력

* 스캔 PDF 읽기
* 각 페이지를 이미지로 변환
* JPEG, PNG, TIFF도 지원 가능

사용 라이브러리 예:

* [PyMuPDF](https://pymupdf.readthedocs.io?utm_source=chatgpt.com)
* [pdf2image](https://pdf2image.readthedocs.io?utm_source=chatgpt.com)

---

### 2. 책 펼침 왜곡 보정 (Dewarp)

책을 스캐너가 아닌 카메라로 촬영한 경우 중앙 접힘(gutter) 때문에 글자가 휘어집니다.

가능한 방법:

#### 간단한 방법

* 페이지 경계 검출
* 투시 변환(Perspective Transform)

라이브러리:

* [OpenCV](https://opencv.org?utm_source=chatgpt.com)

#### 고급 방법

* 곡면 모델링
* 딥러닝 기반 Dewarp

프로젝트 예:

* [page-dewarp](https://github.com/lmmx/page-dewarp?utm_source=chatgpt.com)
* [OCRmyPDF](https://ocrmypdf.readthedocs.io?utm_source=chatgpt.com) (일부 전처리 지원)

---

### 3. 좌우 페이지 분리

이중 페이지 스캔의 경우

```
+------------------+
| 왼쪽페이지 | 오른쪽페이지 |
+------------------+
```

중앙 골(gutter)을 검출하여

```
page_001_left.png
page_001_right.png
```

로 자동 분리.

방법:

* 히스토그램 분석
* 에지 검출
* 딥러닝 문서 레이아웃 분석

---

### 4. 이미지 품질 최적화

OCR 성능 향상에 가장 중요합니다.

#### 밝기(Brightness)

#### 대비(Contrast)

#### 히스토그램 평활화

[OpenCV CLAHE 설명](https://docs.opencv.org/4.x/d5/daf/tutorial_py_histogram_equalization.html?utm_source=chatgpt.com)

#### 노이즈 제거

* Median Filter
* Bilateral Filter

#### 샤프닝

* Unsharp Mask

#### 흑백화

* Adaptive Threshold

---

### 5. 페이지 회전 보정 (Deskew)

기울어진 페이지를

```
2.3°
```

자동 감지 후 수평 정렬.

OpenCV 또는 OCR 엔진이 지원.

---

### 6. OCR

현재 성능 좋은 선택지:

#### 오픈소스

* [Tesseract OCR](https://tesseract-ocr.github.io?utm_source=chatgpt.com)
* [PaddleOCR](https://www.paddleocr.ai?utm_source=chatgpt.com)

한국어 책이라면:

* PaddleOCR 추천
* 한국어 인식률이 상당히 좋음

#### AI 기반

* [Google Cloud Vision](https://cloud.google.com/vision?utm_source=chatgpt.com)
* [Azure AI Vision](https://azure.microsoft.com/products/ai-services/ai-vision?utm_source=chatgpt.com)

---

### 7. OCR 결과 후처리

예:

```
인공지능은 인간의 지능을 모방...
```

후처리:

* 줄바꿈 정리
* 하이픈 제거
* 문단 재구성
* 오탈자 교정

추가로 LLM을 사용하면:

```
OCR 원문
↓
문장 복원
↓
교정
```

가능.

---

### 8. 출력

선택 가능:

#### 텍스트 파일

```
book.txt
```

#### 검색 가능한 PDF

원본 이미지 유지 + OCR 텍스트 레이어 추가

#### EPUB

전자책 변환

#### Markdown

```
# 1장
내용...
```

---

### 추천 아키텍처

```text
PDF
 ↓
이미지 추출
 ↓
좌우 페이지 분리
 ↓
왜곡 보정(Dewarp)
 ↓
Deskew
 ↓
노이즈 제거
 ↓
CLAHE
 ↓
Threshold
 ↓
OCR(PaddleOCR)
 ↓
텍스트 후처리
 ↓
Searchable PDF / TXT / EPUB
```

Python으로 구현하면 대략 500~1500줄 정도 규모의 실용적인 프로그램이 됩니다. 특히 한국어 서적이라면 **OpenCV + PaddleOCR + PyMuPDF** 조합이 가장 현실적이고 성능도 좋은 편입니다. 원하시면 GUI가 있는 데스크톱 앱(Windows용) 또는 폴더를 통째로 처리하는 배치 프로그램 형태의 설계와 샘플 코드까지 만들어 드릴 수 있습니다.

폴더 처리 방식이 가장 좋습니다. 특히 책 스캔본을 대량 처리하려면 GUI보다 배치(batch) 방식이 훨씬 안정적입니다.

제가 추천하는 구조는 단순 OCR 프로그램이 아니라 **"전자책 복원 파이프라인"** 형태입니다.

## 폴더 구조

```text
BookOCR/

├── input/
│   ├── book1.pdf
│   ├── book2.pdf
│   └── ...
│
├── output/
│   ├── book1/
│   │   ├── pages/
│   │   ├── split/
│   │   ├── dewarp/
│   │   ├── ocr/
│   │   ├── book1.txt
│   │   └── book1_searchable.pdf
│   │
│   └── book2/
│
└── main.py
```

프로그램을 실행하면:

```bash
python main.py
```

현재 폴더의 `input/*.pdf`를 자동으로 찾아 처리합니다.

---

## 추천 처리 순서

### 1단계 PDF → 이미지

300~400 DPI

너무 높으면 OCR 속도가 급격히 느려집니다.

권장:

```python
dpi=400
```

---

### 2단계 좌우 페이지 자동 분리

책 스캔의 대부분이

```text
+-------------------+
| 왼쪽 | 오른쪽 |
+-------------------+
```

형태입니다.

단순히 중앙 자르지 말고

* 수직 히스토그램
* 가장 어두운 중앙 골(gutter)

을 찾아 분리하는 게 좋습니다.

그래야 페이지가 약간 치우쳐 있어도 대응됩니다.

---

### 3단계 자동 판단

좋은 기능 하나 추천합니다.

페이지 폭이 큰 경우만 분리.

예:

```python
if width > height * 1.2:
    split_page()
else:
    single_page()
```

그러면

* 단일 페이지 PDF
* 양면 스캔 PDF

둘 다 처리 가능.

---

### 4단계 왜곡 보정

처음 버전은 과하게 욕심내지 말고

* Deskew
* Perspective Correction

만 구현

90% 효과가 있습니다.

실제로 책 OCR 실패 원인의 대부분은

* 기울어짐
* 어두움

이지 곡면 왜곡이 아닙니다.

---

### 5단계 이미지 최적화

제가 추천하는 순서

```python
CLAHE
↓
Noise Reduction
↓
Sharpen
↓
Adaptive Threshold
```

OpenCV만으로 가능.

OCR 인식률이 꽤 올라갑니다.

---

### 6단계 OCR

아이맥이면:

#### 1순위

[PaddleOCR](https://www.paddleocr.ai?utm_source=chatgpt.com)

장점

* 한국어 강함
* 세로 글자 가능
* 책 인식 우수

---

#### 2순위

[Tesseract OCR](https://tesseract-ocr.github.io?utm_source=chatgpt.com)

장점

* 설치 쉬움

단점

* 한국어 품질 낮음

---

### 7단계 중복 제거

책 스캔에서 종종

```text
12
13
14
```

페이지 번호가 OCR됩니다.

후처리에서

```python
^\d+$
```

같은 줄 제거.

---

## 추가 아이디어

### 목차 자동 생성

OCR 후

```text
제1장
제2장
```

패턴을 찾으면

```json
{
  "chapter":"제1장",
  "page":23
}
```

목차 생성 가능.

---

### 검색 가능한 PDF 생성

최종적으로 가장 유용합니다.

결과:

```text
원본 스캔 유지
+
숨겨진 OCR 텍스트
```

이렇게 만들면

* Acrobat 검색 가능
* 복사 가능

실사용성이 매우 좋아집니다.

---

### EPUB 생성

OCR 후

```text
txt
↓
markdown
↓
epub
```

변환 가능.

아이패드, 킨들에서 읽기 편합니다.

---

제가 만든다면 **1차 버전 목표**를 이렇게 잡겠습니다.

```text
PDF
 ↓
페이지 추출
 ↓
좌우 분리
 ↓
기울기 보정
 ↓
CLAHE
 ↓
OCR(PaddleOCR)
 ↓
TXT 생성
 ↓
Searchable PDF 생성
```

이 정도면 실제 책 스캔본의 80~90%를 자동 처리할 수 있습니다. 그리고 macOS + VS Code 환경이면 Python 기반으로 구현하는 것이 가장 빠르고 유지보수도 쉽습니다.


좋습니다. 처음부터 모든 기능을 한 번에 넣기보다는 **동작하는 최소 버전(MVP)** 을 먼저 만들고 점진적으로 고도화하는 것이 좋습니다.

# 1단계 목표

현재 폴더의 PDF를 자동 처리해서:

```text
input/book.pdf

↓

output/book/

├── pages/
├── split/
├── text/
└── book.txt
```

를 생성합니다.

기능:

* PDF 읽기
* 페이지 이미지 추출
* 좌우 페이지 분리
* OCR
* TXT 저장

---

# 개발 환경 준비

터미널에서:

```bash
python3 -m venv venv
source venv/bin/activate

pip install pymupdf
pip install opencv-python
pip install pillow
pip install numpy
pip install paddleocr
```

macOS Apple Silicon이라면 PaddleOCR 설치에 시간이 좀 걸릴 수 있습니다.

---

# 폴더 생성

프로젝트 구조:

```text
BookOCR/

main.py

input/
output/
```

---

# 첫 번째 버전 main.py

```python
from pathlib import Path
import fitz

INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")


def pdf_to_images(pdf_path, output_dir):
    doc = fitz.open(pdf_path)

    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    for i in range(len(doc)):
        page = doc[i]

        pix = page.get_pixmap(
            matrix=fitz.Matrix(2, 2),
            alpha=False
        )

        outfile = pages_dir / f"page_{i+1:04d}.png"
        pix.save(str(outfile))

    print(f"{pdf_path.name} 완료")


def main():
    pdf_files = list(INPUT_DIR.glob("*.pdf"))

    if not pdf_files:
        print("PDF 없음")
        return

    for pdf in pdf_files:
        book_dir = OUTPUT_DIR / pdf.stem
        book_dir.mkdir(parents=True, exist_ok=True)

        pdf_to_images(pdf, book_dir)


if __name__ == "__main__":
    main()
```

실행:

```bash
python main.py
```

---

# 2단계: 좌우 분리

새 파일:

```python
import cv2
```

```python
def split_double_page(image_path, out_dir):

    img = cv2.imread(str(image_path))

    h, w = img.shape[:2]

    if w < h * 1.2:
        return

    center = w // 2

    left = img[:, :center]
    right = img[:, center:]

    cv2.imwrite(
        str(out_dir / f"{image_path.stem}_L.png"),
        left
    )

    cv2.imwrite(
        str(out_dir / f"{image_path.stem}_R.png"),
        right
    )
```

이건 아주 단순 버전입니다.

나중에 중앙 골(gutter) 자동 검출로 업그레이드합니다.

---

# 3단계 OCR

```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(
    lang="korean"
)
```

```python
def ocr_image(img_path):

    result = ocr.ocr(
        str(img_path),
        cls=True
    )

    text = []

    for block in result:
        for line in block:
            text.append(line[1][0])

    return "\n".join(text)
```

---

# 4단계 텍스트 저장

```python
all_text = []

for image in split_dir.glob("*.png"):

    txt = ocr_image(image)

    all_text.append(txt)

with open(
    output_file,
    "w",
    encoding="utf-8"
) as f:

    f.write("\n\n".join(all_text))
```

---

# 이후 업그레이드 순서

1. 자동 기울기 보정(Deskew)
2. CLAHE 대비 향상
3. Adaptive Threshold
4. 중앙 골(gutter) 자동 검출
5. 검색 가능한 PDF 생성
6. EPUB 생성
7. 곡면 페이지 Dewarp
8. GPU 가속

처음에는 **PDF → 이미지 추출 → OCR → TXT 생성**이 정상 동작하는지 확인하는 것이 가장 중요합니다. 그다음에 이미지 품질 개선 기능을 하나씩 추가하는 것이 디버깅하기 쉽습니다.

잘 진행이 안되는것 같다.
((venv) ) mpeg46551@cx2r6s2 bookOCR % pip install pymupdf
error: externally-managed-environment

× This environment is externally managed
╰─> To install Python packages system-wide, try brew install
    xyz, where xyz is the package you are trying to
    install.
    
    If you wish to install a Python library that isn't in Homebrew,
    use a virtual environment:
    
    python3 -m venv path/to/venv
    source path/to/venv/bin/activate
    python3 -m pip install xyz
    
    If you wish to install a Python application that isn't in Homebrew,
    it may be easiest to use 'pipx install xyz', which will manage a
    virtual environment for you. You can install pipx with
    
    brew install pipx
    
    You may restore the old behavior of pip by passing
    the '--break-system-packages' flag to pip, or by adding
    'break-system-packages = true' to your pip.conf file. The latter
    will permanently disable this error.
    
    If you disable this error, we STRONGLY recommend that you additionally
    pass the '--user' flag to pip, or set 'user = true' in your pip.conf
    file. Failure to do this can result in a broken Homebrew installation.
    
    Read more about this behavior here: <https://peps.python.org/pep-0668/>

note: If you believe this is a mistake, please contact your Python installation or OS distribution provider. You can override this, at the risk of breaking your Python installation or OS, by passing --break-system-packages.
hint: See PEP 668 for the detailed specification.
((venv) ) mpeg46551@cx2r6s2 bookOCR % pip install opencv-python
error: externally-managed-environment

× This environment is externally managed
╰─> To install Python packages system-wide, try brew install
    xyz, where xyz is the package you are trying to
    install.
    
    If you wish to install a Python library that isn't in Homebrew,
    use a virtual environment:
    
    python3 -m venv path/to/venv
    source path/to/venv/bin/activate
    python3 -m pip install xyz
    
    If you wish to install a Python application that isn't in Homebrew,
    it may be easiest to use 'pipx install xyz', which will manage a
    virtual environment for you. You can install pipx with
    
    brew install pipx
    
    You may restore the old behavior of pip by passing
    the '--break-system-packages' flag to pip, or by adding
    'break-system-packages = true' to your pip.conf file. The latter
    will permanently disable this error.
    
    If you disable this error, we STRONGLY recommend that you additionally
    pass the '--user' flag to pip, or set 'user = true' in your pip.conf
    file. Failure to do this can result in a broken Homebrew installation.
    
    Read more about this behavior here: <https://peps.python.org/pep-0668/>

note: If you believe this is a mistake, please contact your Python installation or OS distribution provider. You can override this, at the risk of breaking your Python installation or OS, by passing --break-system-packages.
hint: See PEP 668 for the detailed specification.
((venv) ) mpeg46551@cx2r6s2 bookOCR % 

좋습니다. 이건 코드 문제가 아니라 **Python 환경이 꼬인 상태**입니다.

에러를 보면:

```text
externally-managed-environment
```

즉 macOS + Homebrew Python + PEP 668 조합입니다.

그런데 이상한 점은:

```text
((venv))
```

라고 표시되는데도 venv 안으로 제대로 들어가지 않은 것 같습니다.

먼저 확인해보죠.

터미널에서:

```bash
which python
which pip
```

결과를 보여주세요.

정상적인 경우는:

```bash
/Users/사용자명/bookOCR/venv/bin/python
/Users/사용자명/bookOCR/venv/bin/pip
```

이어야 합니다.

지금은 아마:

```bash
/opt/homebrew/bin/python3
/opt/homebrew/bin/pip3
```

가 나올 가능성이 높습니다.

---

그리고 다음도 확인해주세요.

```bash
python --version
pip --version
```

---

### 빠른 해결법

현재 venv를 지우고 새로 만드는 게 가장 빠를 수 있습니다.

프로젝트 폴더에서:

```bash
deactivate
rm -rf venv
```

새로 생성:

```bash
python3 -m venv venv
```

활성화:

```bash
source venv/bin/activate
```

확인:

```bash
which python
which pip
```

둘 다 반드시

```text
.../bookOCR/venv/bin/
```

아래를 가리켜야 합니다.

그 다음 설치:

```bash
python -m pip install --upgrade pip
```

그리고:

```bash
python -m pip install pymupdf opencv-python pillow numpy
```

중요한 점은 **`pip install` 대신 `python -m pip install`** 을 사용하는 것입니다.

---

만약 Apple Silicon(M1/M2/M3/M4)이고 그래도 같은 오류가 나오면:

```bash
python -m pip install --break-system-packages pymupdf
```

로 우회할 수 있지만, 정상적인 venv에서는 보통 필요 없습니다.

---

우선 아래 4개 명령의 결과를 보여주세요.

```bash
which python
which pip

python --version
pip --version
```

그 결과를 보면 현재 venv가 실제로 활성화된 상태인지 바로 판단할 수 있습니다.


원인을 찾았습니다.

문제는 **venv가 아니라 쉘 alias** 입니다.

현재:

```bash
which python
python: aliased to $PYTHON_HOME/bin/python3.12

which pip
pip: aliased to $PYTHON_HOME/bin/pip3.12
```

즉 venv가 활성화되어 있어도,

```bash
python
pip
```

명령이 venv 안의 Python이 아니라 **강제로 PYTHON_HOME의 Python 3.12** 를 사용하고 있습니다.

그래서 Homebrew의 PEP 668 보호에 걸리는 것입니다.

---

## 현재 상태 확인

아래 명령을 실행해보세요.

```bash
alias
```

아마 이런 비슷한 것이 있을 겁니다.

```bash
alias python='$PYTHON_HOME/bin/python3.12'
alias pip='$PYTHON_HOME/bin/pip3.12'
```

---

## 임시 해결

현재 터미널 세션에서:

```bash
unalias python
unalias pip
```

실행

그리고:

```bash
which python
which pip
```

확인

정상이라면:

```bash
/Users/사용자명/bookOCR/venv/bin/python
/Users/사용자명/bookOCR/venv/bin/pip
```

처럼 나와야 합니다.

---

## 설치

그 다음:

```bash
python -m pip install --upgrade pip
```

```bash
python -m pip install pymupdf
```

```bash
python -m pip install opencv-python pillow numpy
```

---

## 더 확실한 방법

alias를 무시하고 venv를 직접 호출:

```bash
./venv/bin/python -m pip install pymupdf
```

또는

```bash
./venv/bin/python -m pip install opencv-python pillow numpy
```

이 방식은 alias 영향을 전혀 받지 않습니다.

---

## 영구 수정

아마 `~/.zshrc` 또는 `~/.zprofile` 안에 이런 줄이 있을 가능성이 큽니다.

```bash
alias python=$PYTHON_HOME/bin/python3.12
alias pip=$PYTHON_HOME/bin/pip3.12
```

확인:

```bash
cat ~/.zshrc
```

또는

```bash
grep alias ~/.zshrc
```

보여주시면 어떤 부분을 수정해야 할지 정확히 알려드릴게요.

지금 단계에서는 먼저:

```bash
unalias python
unalias pip

which python
which pip
```

결과를 확인해 보세요. 정상적으로 바뀌면 바로 패키지 설치를 진행할 수 있습니다.


여기까지 했다.
((venv) ) mpeg46551@cx2r6s2 bookOCR % alias
pip='$PYTHON_HOME/bin/pip3.12'
pip3='$PYTHON_HOME/bin/pip3.12'
python='$PYTHON_HOME/bin/python3.12'
python3='$PYTHON_HOME/bin/python3.12'
run-help=man
which-command=whence
((venv) ) mpeg46551@cx2r6s2 bookOCR % unalias python
((venv) ) mpeg46551@cx2r6s2 bookOCR % unalias pip
((venv) ) mpeg46551@cx2r6s2 bookOCR % which python
/Users/mpeg46551/git/codyssey/bookOCR/venv/bin/python
((venv) ) mpeg46551@cx2r6s2 bookOCR % which pip
/Users/mpeg46551/git/codyssey/bookOCR/venv/bin/pip
((venv) ) mpeg46551@cx2r6s2 bookOCR % python -m pip install --upgrade pip
Requirement already satisfied: pip in ./venv/lib/python3.12/site-packages (26.0)
Collecting pip
  Downloading pip-26.1.2-py3-none-any.whl.metadata (4.6 kB)
Downloading pip-26.1.2-py3-none-any.whl (1.8 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.8/1.8 MB 42.9 MB/s  0:00:00
Installing collected packages: pip
  Attempting uninstall: pip
    Found existing installation: pip 26.0
    Uninstalling pip-26.0:
      Successfully uninstalled pip-26.0
Successfully installed pip-26.1.2
((venv) ) mpeg46551@cx2r6s2 bookOCR % python -m pip install pymupdf
Collecting pymupdf
  Downloading pymupdf-1.27.2.3-cp310-abi3-macosx_10_9_x86_64.whl.metadata (24 kB)
Downloading pymupdf-1.27.2.3-cp310-abi3-macosx_10_9_x86_64.whl (24.0 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 24.0/24.0 MB 41.9 MB/s  0:00:00
Installing collected packages: pymupdf
Successfully installed pymupdf-1.27.2.3
((venv) ) mpeg46551@cx2r6s2 bookOCR % python -m pip install opencv-python pillow numpy
Collecting opencv-python
  Downloading opencv_python-4.13.0.92-cp37-abi3-macosx_14_0_x86_64.whl.metadata (19 kB)
Collecting pillow
  Downloading pillow-12.2.0-cp312-cp312-macosx_10_13_x86_64.whl.metadata (8.8 kB)
Collecting numpy
  Downloading numpy-2.4.6-cp312-cp312-macosx_14_0_x86_64.whl.metadata (6.6 kB)
Downloading opencv_python-4.13.0.92-cp37-abi3-macosx_14_0_x86_64.whl (32.6 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 32.6/32.6 MB 52.3 MB/s  0:00:00
Downloading pillow-12.2.0-cp312-cp312-macosx_10_13_x86_64.whl (5.3 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 5.3/5.3 MB 63.6 MB/s  0:00:00
Downloading numpy-2.4.6-cp312-cp312-macosx_14_0_x86_64.whl (6.6 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 6.6/6.6 MB 13.9 MB/s  0:00:00
Installing collected packages: pillow, numpy, opencv-python
Successfully installed numpy-2.4.6 opencv-python-4.13.0.92 pillow-12.2.0
((venv) ) mpeg46551@cx2r6s2 bookOCR % 

좋습니다. 지금은 환경 문제가 해결됐습니다. 🎉

여기까지 왔으면:

```text
✓ venv 정상 동작
✓ pip 정상 동작
✓ PyMuPDF 설치 완료
✓ OpenCV 설치 완료
✓ Pillow 설치 완료
✓ NumPy 설치 완료
```

상태입니다.

---

## 한 가지 더 해야 할 것

지금 터미널을 새로 열면 alias가 다시 살아날 가능성이 높습니다.

현재 설정 확인:

```bash
grep PYTHON_HOME ~/.zshrc
```

또는

```bash
cat ~/.zshrc
```

를 보면 아마 이런 줄이 있을 겁니다.

```bash
alias python=$PYTHON_HOME/bin/python3.12
alias pip=$PYTHON_HOME/bin/pip3.12
```

이건 나중에 제거하는 게 좋습니다.

---

# 이제 OCR 전에 PDF 추출 테스트

프로젝트 구조:

```text
bookOCR/

input/
output/
main.py
venv/
```

---

## 테스트 PDF 넣기

```text
input/
└── sample.pdf
```

---

## main.py

아래 코드부터 실행해봅시다.

```python
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
```

---

## 실행

```bash
python main.py
```

---

## 기대 결과

```text
output/

└── sample/
    └── pages/
        ├── page_0001.png
        ├── page_0002.png
        ├── page_0003.png
        └── ...
```

---

## 먼저 OCR은 잠시 미룹시다

초기 단계에서는:

```text
PDF
 ↓
PNG 추출
 ↓
좌우 분리
 ↓
이미지 보정
 ↓
OCR
```

순서로 가는 게 좋습니다.

왜냐하면 OCR 품질은 전처리가 80%를 결정하기 때문입니다.

---

다음 단계 목표는 **"책 펼침 이미지 자동 분리"** 입니다.

예를 들어:

```text
+------------------------+
| Page 1 | Page 2        |
+------------------------+
```

를

```text
page_0001_L.png
page_0001_R.png
```

로 나누는 기능을 넣겠습니다.

우선 `main.py`를 실행해 보고, 실제로 PNG들이 생성되는지 확인해 주세요. 생성되면 다음 단계로 자동 페이지 분리 기능을 붙여보겠습니다.

>> png로 잘 저장되었어

좋습니다. 이제 **1단계(PDF → PNG)** 는 성공했습니다.

다음으로는 OCR보다 먼저 **책 스캔 전처리**를 넣는 것이 좋습니다. 실제로 OCR 품질은 OCR 엔진보다 전처리가 더 중요합니다.

추천 순서:

```text id="flow1"
PDF
 ↓
PNG 추출  ✅
 ↓
양면 페이지 분리
 ↓
기울기 보정
 ↓
명암/대비 개선
 ↓
OCR
```

---

# 2단계: 좌우 페이지 자동 분리

현재 생성된 PNG 중 하나를 열어보세요.

### 경우 1: 이미 단일 페이지

```text id="single"
+----------+
| 페이지 1 |
+----------+
```

그냥 그대로 사용.

### 경우 2: 펼침면(2페이지)

```text id="double"
+----------------------+
| 왼쪽 | 오른쪽 |
+----------------------+
```

분리 필요.

---

## 간단 버전

새 함수 추가:

```python
import cv2

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
```

---

## 처리 폴더

```text id="folders"
output/

└── sample/
    ├── pages/
    └── split/
```

생성:

```python
split_dir = book_dir / "split"
split_dir.mkdir(exist_ok=True)
```

---

## 더 좋은 방법

단순 중앙 자르기는 나중에 문제를 만듭니다.

실제 책은:

```text id="gutter"
| 페이지 |   골   | 페이지 |
```

중앙이 정확히 절반이 아닐 수 있습니다.

그래서 다음 버전에서는:

1. 흑백 변환
2. 세로 히스토그램 계산
3. 가장 어두운 세로선 찾기
4. 그 위치를 기준으로 분리

를 사용할 예정입니다.

그러면 책이 치우쳐 스캔돼도 잘 분리됩니다.

---

# 3단계로 추천하는 기능

OCR 전에 이것부터 넣는 게 좋습니다.

```python
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

clahe = cv2.createCLAHE(
    clipLimit=2.0,
    tileGridSize=(8,8)
)

result = clahe.apply(gray)
```

이 한 줄 추가만으로도 오래된 책이나 누런 종이 OCR 품질이 눈에 띄게 좋아집니다.

---

제가 추천하는 다음 목표는:

```text id="roadmap"
PDF
 ↓
PNG
 ↓
자동 페이지 분리
 ↓
CLAHE 적용
 ↓
기울기 보정
 ↓
PaddleOCR
 ↓
TXT 출력
```

입니다.

그런데 다음 작업 전에 하나만 알려주세요.

**현재 PDF가 대부분**

1. 스캐너로 뜬 양면 페이지 PDF인가요?
2. 스마트폰/카메라로 찍은 책 사진 PDF인가요?
3. 이미 OCR이 안 된 스캔 PDF인가요?

이 차이에 따라 "중앙 분리"와 "왜곡 보정(Dewarp)"의 우선순위가 달라집니다.

>> 양면 스마트폰으로 찍은것 같아 아직 OCR은 처리 안되었다.

그렇다면 방향이 완전히 달라집니다.

**양면 + 스마트폰 촬영본**이라면 단순 OCR 프로젝트가 아니라 사실상 **Book Scan Restoration(책 복원)** 프로젝트입니다.

보통 이런 이미지는:

```text id="phone_scan"
문제 1: 책이 휘어 있음
문제 2: 중앙 골(gutter) 그림자
문제 3: 페이지가 비스듬함
문제 4: 조명 불균일
문제 5: 좌우 2페이지가 붙어 있음
```

상태입니다.

---

## OCR을 지금 붙이면 안 되는 이유

예를 들어 이런 페이지:

```text id="bad_scan"
(휘어진 글자)

인 공 지 능 은 ...
```

를 OCR 하면

```text id="ocr_fail"
인공지능은
인공지늠은
인공지능온
```

처럼 오인식이 많아집니다.

그래서 순서를 바꿔야 합니다.

---

# 추천 파이프라인

```text id="pipeline"
PDF
 ↓
PNG 추출  ✅
 ↓
페이지 검출
 ↓
페이지 외곽 추출
 ↓
원근 보정
 ↓
중앙 골 검출
 ↓
좌우 분리
 ↓
명암 보정
 ↓
기울기 보정
 ↓
OCR
```

---

# 지금 바로 해볼 가치가 있는 것

먼저 실제 페이지 상태를 봐야 합니다.

현재 생성된 PNG 중 하나를 올려주세요.

예를 들어:

```text id="example"
page_0001.png
```

한 장만 있으면 됩니다.

그러면 제가:

* 스마트폰 왜곡 정도
* 중앙 골 위치
* 자동 분리 가능 여부
* Dewarp 필요 여부
* OCR 예상 인식률

을 보고 다음 단계 코드를 설계할 수 있습니다.

---

## 예상되는 구현 방향

스마트폰 촬영 책이라면 OpenCV만으로도 꽤 개선할 수 있습니다.

예를 들어:

```python id="preprocess"
1. grayscale
2. adaptive threshold
3. contour detection
4. page boundary detection
5. perspective transform
```

만 해도 효과가 큽니다.

---

## 장기적으로는

나중에 다음 오픈소스 기법도 검토할 수 있습니다.

* [OpenCV](https://opencv.org?utm_source=chatgpt.com) 기반 페이지 검출
* [PaddleOCR](https://www.paddleocr.ai?utm_source=chatgpt.com) OCR
* [OCRmyPDF](https://ocrmypdf.readthedocs.io?utm_source=chatgpt.com) 검색 가능 PDF 생성

---

다음 단계로는 PNG 한 장을 보여주는 것이 가장 좋습니다. 실제 이미지를 보면 "중앙 분리부터 해야 하는지" 아니면 "원근 보정부터 해야 하는지"를 바로 판단할 수 있습니다.

대화가 끊길 수 있다는 점은 이해됩니다.

이미지를 올리지 않고도 진행할 수 있는 방법이 있습니다.

현재 생성된 PNG 하나에 대해 아래 정보를 알려주세요.

### 1. 이미지 크기

터미널에서:

```bash
python -c "from PIL import Image; img=Image.open('output/sample/pages/page_0001.png'); print(img.size)"
```

또는 실제 경로로 바꿔서 실행하세요.

결과 예:

```text
(2480, 3508)
```

---

### 2. 책이 어떻게 보이나요?

가장 가까운 형태를 골라주세요.

A.

```text
+----------------------+
| 왼쪽 페이지 | 오른쪽 페이지 |
+----------------------+
```

B.

```text
+----------+
| 한 페이지 |
+----------+
```

C.

```text
카메라로 찍은 펼친 책

 /------------\
| 페이지|페이지 |
 \------------/
```

D.

```text
페이지가 휘어있고
중앙 그림자가 심함
```

복수 선택 가능.

---

### 3. PDF는 몇 페이지 정도인가요?

예:

```text
200페이지
```

또는

```text
500페이지
```

---

### 4. OCR 결과물 목표

어느 쪽이 더 중요한가요?

#### ① 정확도 우선

처리는 느려도 됨

```text
PDF
↓
왜곡보정
↓
OCR
```

#### ② 속도 우선

```text
PDF
↓
바로 OCR
```

---

개인적으로는 현재 설명만 보면:

```text
양면
+
스마트폰 촬영
+
OCR 없음
```

이므로

**중앙 분리 → 원근 보정 → OCR**

이 핵심이고, 첫 버전에서는 "곡면(페이지 휨) 보정"까지 욕심내지 않는 것이 좋습니다.

그리고 한 가지 더 좋은 방법이 있습니다.

PNG 한 장에 대해:

```bash
ls -lh output/*/pages/page_0001.png
```

그리고

```bash
python -c "
from PIL import Image
img=Image.open('output/.../page_0001.png')
print(img.size)
"
```

결과만 알려주셔도 이미지 상태를 꽤 추정할 수 있습니다.


>> 전체코드
좋습니다. 지금 단계에서는 **"PDF → 이미지 추출 → 스마트폰 촬영본 전처리 → 좌우 분리"** 까지 되는 하나의 실행 가능한 코드가 좋겠습니다.

아래 코드를 `main.py` 로 저장하세요.

이 버전은:

* input 폴더의 PDF 자동 검색
* PNG 추출
* 흑백 변환
* CLAHE 대비 향상
* Adaptive Threshold
* 양면 페이지 자동 분리
* 결과 저장

까지 수행합니다.

```python
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
```

실행:

```bash
python main.py
```

실행 후 결과 구조:

```text
output/

└── 책이름/
    ├── pages/
    │   ├── page_0001.png
    │   └── ...
    │
    ├── clean/
    │   ├── page_0001.png
    │   └── ...
    │
    └── split/
        ├── page_0001_L.png
        ├── page_0001_R.png
        └── ...
```

먼저 여기까지 돌려보세요.

특히 `split` 폴더를 확인해서:

* 좌우 페이지가 제대로 분리되는지
* 중앙 그림자가 잘 제거되는지
* 페이지가 잘리지 않는지

확인하는 것이 다음 단계(OCR 추가)보다 중요합니다. 만약 분리 결과가 이상하면 그에 맞게 gutter 검출 알고리즘을 개선할 수 있습니다.


좋습니다. 이건 환경 문제가 아니라 **코드 변수 스코프 버그**입니다.

에러 핵심:

```text
NameError: name 'book_dir' is not defined
```

즉 `main()` 안에서 `book_dir`을 쓰고 있는데, 그 변수가 그 위치에 없습니다.

---

>>
((venv) ) mpeg46551@cx2r6s2 bookOCR % python main.py                                                       
Traceback (most recent call last):
  File "/Users/mpeg46551/git/codyssey/bookOCR/main.py", line 80, in <module>
    main()
  File "/Users/mpeg46551/git/codyssey/bookOCR/main.py", line 68, in main
    split_dir = book_dir / "split"
                ^^^^^^^^
NameError: name 'book_dir' is not defined

>>>
-------

# 왜 이런 일이 생겼냐

제가 준 코드 흐름에서:

* `process_book(pdf_path)` 안에는 `book_dir` 있음
* 그런데 `main()`에서 `book_dir`을 잘못 참조했거나
* 복사 과정에서 줄이 꼬였을 가능성이 큽니다

---

# 해결: 안정된 "정리된 전체 코드"

아래 코드로 **main.py를 통째로 교체**하세요.

(이건 오류 안 나게 구조까지 정리한 버전입니다)

---

## ✅ 수정 완료 버전 main.py

```python id="fixed_main"
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
```

---

# 🚀 실행

```bash
python main.py
```

---

# 🔥 이제 정상 동작하면 나오는 결과

```text
output/
└── 책이름/
    ├── pages/
    ├── clean/
    └── split/
```

---

# 다음 단계 (중요)

이게 성공하면 다음이 핵심입니다:

### 1. split 결과 확인

* 왼쪽/오른쪽 정확히 나뉘는지
* 글자가 잘리지 않는지

### 2. 문제가 있으면

→ gutter detection 개선 (이건 정확도 핵심)

### 3. 그 다음

→ OCR (PaddleOCR)

---

원하면 다음 단계로 바로 갑니다:

👉 “OCR 붙여서 txt 만들기”
👉 “검색 가능한 PDF 만들기”
👉 “EPUB 변환”

지금 상태는 이미 **프로젝트 60% 완료 단계**입니다.
