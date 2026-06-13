[데이터클래스 공부](https://cocojen.tistory.com/13)

현재 제공된 소스(문서)에는 `@dataclass`와 일반 클래스 간의 '성능 차이'에 대한 직접적인 언급이나 비교 자료는 포함되어 있지 않습니다. 

프로젝트 문서에 따르면, 이번 가계부 앱에서 `@dataclass`를 사용한 주된 이유는 성능 향상보다는 **속성의 명료함, 코드의 가독성 확보, 그리고 딕셔너리 직렬화/역직렬화(DTO) 로직을 아주 단순하고 깔끔하게 구현하기 위함**입니다.

---

**💡 소스 외부의 일반적인 파이썬 지식을 바탕으로 추가 설명을 드리자면 (독립적인 검증이 필요할 수 있는 외부 정보입니다):**

결론부터 말씀드리면, `@dataclass`와 일반 파이썬 클래스 간에는 **유의미한 실행 속도나 메모리 성능 차이가 사실상 없습니다.**

그 이유는 다음과 같습니다.
1. **단순한 코드 생성기 역할**: `@dataclass`는 새로운 마법 같은 데이터 구조를 만드는 것이 아니라, 개발자가 일반 클래스에서 손으로 직접 쳐야 하는 `__init__` (초기화), `__repr__` (출력), `__eq__` (비교) 등의 반복적인 특수 메서드 코드를 백그라운드에서 대신 타이핑해서 만들어주는(Boilerplate 절감) 데코레이터일 뿐입니다.
2. **동일한 내부 동작**: 결과적으로 메모리에 올라갈 때는 개발자가 직접 메서드를 다 구현한 일반 클래스와 완전히 동일한 형태의 파이썬 객체로 컴파일되어 동작합니다. 

즉, `@dataclass`는 '컴퓨터의 실행 성능'을 최적화하기 위한 도구가 아니라, **'개발자의 작성 시간과 코드 가독성(생산성)'을 극대화하기 위한 설계적 선택**이라고 이해하시면 좋습니다.

데이터 클래스를 사용해서 아이스크림을 만들 때:
위에서 만든 클래스와 똑같은 정보를 가지는 아이스크림 데이터클래스를 만들어보자.

import random
import string
from dataclasses import dataclass


def generate_id() -> str:
    return "".join(random.choices(string.ascii_uppercase, k=12))


@dataclass
class Icecream:
    name: str
    flavor: str


def main() -> None:
    icecream = Icecream(name="together", flavor="vanilla")
    print(icecream)


if __name__ == "__main__":
    main()
한 눈에 봐도 코드의 길이가 짧아졌다. instance variable을 위와 같이 작성해주면 끝이다. 

기존의 클래스와 비교해서 데이터 클래스가 더 빠르고 쉬운 이유는

 

1) 데이터클래스가 이니셜라이저를 자동으로 만들어주고

 

2) __repr__ 메소드도 자동으로 생성해주기 때문에 위에서와 같이 프린트 찍을 때 인스턴스의 값을 보기 위해 따로 __str__ 메소드를

작성해주거나 하지 않아도 되고, ( 따로 메소드를 작성해주지 않아도 icecream을 프린트하면 Icecream(name='together', flavor='vanilla') 와 같이 출력됨 )

 

3) 위와 같이 name: str 같은 형식으로 타입을 쉽게 제공할 수 있기 떄문이다.

 

데이터 클래스의 간단한 사용법을 알아보았으니, 데이터클래스를 사용했을 때 얻을 수 있는 장점을 알아보자.

dataclass 의 여러가지 기능
1. 디폴트 값 설정하기
: 아래와 같이 in_stock 이라는 인스턴스 변수에 boolean 값으로 True를 주면 이니셜라이저에 따로 명시하지 않아도 디폴트 값이 True로 설정된다.

@dataclass
class Icecream:
    name: str
    flavor: str
    in_stock: bool = True
Icecream(name='together', flavor='vanilla', in_stock=True)
 

조금 더 심화해서, 아이스크림이 발매되는 사이즈들을 넣을 list와 아이디에 디폴트 값을 주어보자.

여기서 주의할 점은 email_address: list = [] 와 같은 식으로 줄 수 없다는 점이다.

list는 mutable하기 때문에 모든 인스턴스들이 필드의 기본 값을 공유하기 때문에, 허용되지 않는다.

따라서 field를 import 하고 default_factory 를 사용해주어야 한다.

데이터클래스가 클래스를 생성할 때, default_factory=list 로 적어놓은 함수(타입아님)를 call 해서 매번 새로운 리스트를 생성해준다.

 

@dataclass
class Icecream:
    name: str
    flavor: str
    in_stock: bool = True
    sizes: list = field(default_factory=list)
    id: str = field(default_factory=generate_id)
디폴트값을 준 것이니, 당연히 클래스를 만들 때 값을 넣어주면 그 값을 가진 클래스가 생성된다.

    icecream = Icecream(name="together", flavor="vanilla", id="my_id")
아래는 print(icecream) 의 결과 :

 

Icecream(name='together', flavor='vanilla', in_stock=True, sizes=[], id='my_id')
 

2. Init 옵션 주기
여기에서 위와같이 id를 따로 생성해줄 수 없게 만들고 싶을 때는, init 옵션을 주면 된다.

@dataclass
class Icecream:
    name: str
    flavor: str
    in_stock: bool = True
    sizes: List[str] = field(default_factory=list)
    id: str = field(init=False, default_factory=generate_id)


def main() -> None:
    icecream = Icecream(name="together", flavor="vanilla", id="my_id")
    print(icecream)
이렇게 init=False 옵션을 주고 이니셜라이저에 id값을 넣어주면 아래와 같은 에러가 난다.

TypeError: __init__() got an unexpected keyword argument 'id'
 

3. post_init 메서드 사용해서 필드 생성하기
만약에 위 Icecream 을 찾기 쉽게 유니크한 아이디와 제품명으로 이루어진 search_string 이라는 필드를 추가하고자 하면 어떻게 해야할까? 아이디는 인스턴스가 생성될 때 생성되기 때문에 동시에 값을 넣어줄 수 없다. 인스턴스가 생성된 후에 id값과 name 값이 생겨야만 만들 수 있는 필드이다. 이럴 때는 말그대로 post_init , 즉 이니셜라이즈 후의 라는 메소드를 사용하면 된다.

@dataclass
class Icecream:
    name: str
    flavor: str
    in_stock: bool = True
    sizes: List[str] = field(default_factory=list)
    id: str = field(init=False, default_factory=generate_id)
    search_str: str = field(init=False)

    def __post_init__(self) -> None:
        self.search_str = f"{self.name} - {self.id}"
Icecream(name='together', flavor='vanilla', in_stock=True, sizes=[], id='WGSJNSLLIKRX', search_str='together - WGSJNSLLIKRX')
search_str 필드의 값도 잘 생성된 것을 확인할 수 있다.

 

이 외에도 데이터클래스의 장점은 아주 많다.

더 많은 정보는 아래의 유투브 링크를 추천한다.

내가 매우 좋아하는 파이썬 유투버이고, 이 블로그 또한 그의 영상을 참고하여 (예시는 내가 만들었다) 정리한 것이다.

 

 

참고 : https://www.youtube.com/watch?v=CvQ7e6yUtnw

# 코드내 사용예제
네, 맞습니다! 이번 가계부 애플리케이션 코드에서도 데이터 구조를 명확하고 간결하게 표현하기 위해 `@dataclass`를 적극적으로 활용했습니다.

구체적으로 **`models.py`** 파일에서 다음 두 가지 핵심 데이터 모델을 정의할 때 사용되었습니다.

1. **`Transaction` 클래스**: 개별 수입 및 지출 거래 내역 정보를 담는 데이터 클래스입니다. 고유 ID(`id`), 거래 타입(`type`), 날짜(`date`), 금액(`amount`), 카테고리(`category`), 메모(`memo`), 태그(`tags`) 등의 속성을 간결하게 정의하는 데 사용되었습니다.
2. **`RecurringTemplate` 클래스**: 매달 고정적으로 발생하는 반복 거래(예: 월세, 월급 등)의 템플릿 명세를 정의하는 데이터 클래스입니다.

**`@dataclass` 적용을 통해 얻은 이점:**
* **코드 간결성 및 가독성 향상**: 클래스를 생성할 때 번거롭게 `__init__` 메서드를 직접 작성해 변수를 하나하나 할당할 필요 없이, 각 데이터 모델이 어떤 속성(규격)을 가지는지 아주 명료하게 선언할 수 있었습니다.
* **직렬화(DTO) 로직 단순화**: 데이터를 JSON 파일로 영구 저장하거나 다시 객체로 불러오기 위한 딕셔너리 직렬화/역직렬화 연산이 매우 단순하고 깔끔하게 구현되었습니다.

실제로 이번 프로젝트의 미션 기능 요구 사항에도 "데이터 모델은 `dataclass` 또는 그에 준하는 구조로 정의해야 합니다"라는 필수 조건이 명시되어 있었으며, 본 코드는 이를 완벽하게 충족하여 설계되었습니다.

파이썬에서 데코레이터(Decorator, @ 기호)는 쉽게 말해 "기존 함수나 클래스를 수정하지 않고, 새로운 기능을 덧붙여(장식해) 주는 도구"입니다. [1] 
선택하신 코드는 파이썬의 내장 데코레이터인 @property와 @속성명.setter를 사용해 Getter와 Setter를 구현한 전통적인 방식입니다. 각 구문이 어떤 역할을 하는지 알기 쉽게 풀어 설명해 드릴게요.
------------------------------

질문하신 내용은 파이썬에서 @dataclass를 사용할 때 "클래스 선언부에 데코레이터(@)를 붙이면, 수많은 getter와 setter 메서드를 직접 만들지 않아도 된다"는 의미입니다.
기호 +가 아니라 골뱅이 기호인 @(데코레이터)를 의미하신 것으로 보입니다. 자바(Java) 같은 다른 언어나 과거 파이썬 방식과 비교해 보면 왜 안 써도 되는지 바로 이해하실 수 있습니다.
------------------------------
## 1. 과거 방식 (또는 타 언어): 무수한 Getter / Setter 지옥
일반적으로 객체의 멤버 변수를 안전하게 가져오고(getter) 수정(setter)하기 위해 아래와 같이 수많은 코드를 직접 작성해야 했습니다. 변수가 10개면 이런 메서드를 20개나 만들어야 해서 코드가 매우 길어졌습니다.

class OldTransaction:
    def __init__(self, category: str, amount: int):
        self._category = category
        self._amount = amount

    # category를 가져오는 Getter
    @property
    def category(self):
        return self._category

    # category를 수정하는 Setter
    @category.setter
    def category(self, value):
        self._category = value

    # amount를 가져오는 Getter
    @property
    def amount(self):
        return self._amount

    # amount를 수정하는 Setter
    @amount.setter
    def amount(self, value):
        self._amount = value

------------------------------
## 2. @dataclass 방식: 선언만 하면 끝
클래스 위에 @dataclass를 붙여주면, 파이썬이 내부적으로 데이터를 다루기 가장 편리한 형태로 클래스를 알아서 세팅해 줍니다.
따라서 복잡한 문법 없이 점(.) 기호 하나만으로 데이터를 곧바로 가져오고 변경할 수 있습니다.

from dataclasses import dataclass

@dataclassclass Transaction:
    category: str
    amount: int
# 사용 예시t = Transaction("식비", 10000)
# Getter 없이 바로 가져오기 (Read)
print(t.amount)   # 출력: 10000
# Setter 없이 바로 수정하기 (Update)
t.amount = 12000 
print(t.amount)   # 출력: 12000

------------------------------
## 💡 그래도 수정을 못 하게 막고 싶다면? (Read-Only 데이터)
"Getter/Setter를 안 쓰면 아무나 값을 마음대로 바꿀 수 있어서 위험하지 않나요?"라는 의문이 생길 수 있습니다.
가계부 과거 내역처럼 한 번 쓰면 절대 수정할 수 없게(상수처럼) 막고 싶다면, @dataclass(frozen=True) 옵션을 주면 됩니다.

@dataclass(frozen=True) # frozen=True를 붙이면 고정(Freeze)됩니다.class ImmutableTransaction:
    category: str
    amount: int
t = ImmutableTransaction("식비", 10000)
# 값을 수정하려고 하면?
t.amount = 12000  # ❌ dataclasses.FrozenInstanceError 오류 발생! (수정 불가)

이처럼 @dataclass를 사용하면 변수를 가져오고 수정하는 기본 동작이 자동으로 허용되므로 굳이 귀찮게 getter/setter 코드를 도배할 필요가 없어집니다.
혹시 코드 동작 중에 "특정 금액 이하로 지출을 제한"하는 것처럼 데이터 수정 시 제한 조건(유효성 검사)을 두고 싶으신가요? 아니면 이 문법에 대해 더 궁금한 점이 있으신가요?


---------------
## 1. self._category (변수명 앞의 언더바 _)
파이썬에는 자바의 private처럼 변수를 완벽히 숨기는 기능이 없습니다. 대신 개발자들끼리 "변수 이름 앞에 언더바(_)를 붙이면 외부에선 직접 건드리지 말고 조심히 다뤄달라"고 암묵적으로 약속(관례)한 것입니다.
## 2. @property (Getter 역할)
변수 앞에 언더바(_)를 붙여 숨겼기 때문에, 외부에서 이 값을 안전하게 읽어갈 수 있는 통로가 필요합니다. 그 통로를 만들어주는 것이 @property입니다.

@propertydef category(self):
    return self._category


* 기능: 외부에서 객체.category라고 호출하면, 이 함수가 실행되어 숨겨둔 self._category 값을 반환합니다.
* 특징: 분명 함수(def)로 만들었지만, 호출할 때는 괄호()를 붙이지 않고 마치 일반 변수처럼 t.category로 사용할 수 있게 바뀝니다. [2] 

## 3. @category.setter (Setter 역할)
숨겨둔 변수의 값을 안전하게 변경할 수 있도록 검문소 역할을 해주는 데코레이터입니다.

@category.setterdef category(self, value):
    self._category = value


* 기능: 외부에서 객체.category = "새값" 형태로 값을 대입하려고 할 때 이 함수가 자동으로 실행됩니다.
* 장점: 이곳에 검사 로직을 넣을 수 있습니다. 예를 들어 가계부 금액에 음수가 들어오지 못하게 막는 식입니다.

------------------------------
## 💡 왜 이런 복잡한 짓을 할까요? (데코레이터의 진짜 가치)
"그냥 self.category로 만들면 편한데 왜 굳이 숨기고 데코레이터를 쓰나요?"라는 의문이 듭니다. 데이터 오염을 막기 위한 안전장치를 걸 수 있기 때문입니다.
금액(amount)을 다루는 하단 코드를 예시로, 데코레이터 내부에 안전장치(검문소)를 추가해 보겠습니다.

class OldTransaction:
    def __init__(self, category: str, amount: int):
        self._category = category
        self._amount = amount

    @property
    def amount(self):
        return self._amount

    # 금액을 수정할 때 검문소(Setter) 작동!
    @amount.setter
    def amount(self, value):
        if value < 0:
            print("❌ 오류: 가계부 금액은 음수(-)가 될 수 없습니다!")
            return  # 저장하지 않고 차단
        self._amount = value

이렇게 데코레이터를 써두면, 누군가 실수로 금액을 잘못 입력했을 때 시스템이 망가지는 것을 막을 수 있습니다.

t = OldTransaction("식비", 10000)

t.amount = -5000  # 겉보기엔 변수에 값을 넣는 것 같지만, 사실 Setter 함수가 실행됨!# 출력: ❌ 오류: 가계부 금액은 음수(-)가 될 수 없습니다!

print(t.amount)   # 기존 값인 10000 유지됨

------------------------------
## 📌 요약하자면

* @ (데코레이터): 파이썬이 제공하는 마법 기호로, 함수 위에 얹어서 특수한 능력(기능)을 부여함.
* @property: 메서드를 일반 '변수'처럼 읽을 수 있게 장식함 (Getter).
* @변수명.setter: 변수에 값을 대입할 때 '검문소 함수'가 켜지도록 장식함 (Setter).

앞서 배운 @dataclass는 이 귀찮은 @property와 @setter 과정마저도 "특별한 검문소가 필요 없다면 파이썬이 알아서 생략하고 깔끔하게 만들어줄게!" 하고 등장한 아주 편리한 데코레이터인 셈입니다.
혹시 이 데코레이터 개념을 활용해서 금액이 음수가 되지 않도록 가계부 코드를 직접 수정하는 연습을 같이 해볼까요? 아니면 데코레이터 자체의 동작 원리가 더 궁금하신가요?

[1] https://yanghojun.github.io
[2] [https://blog.dnd.ac](https://blog.dnd.ac/python-decorator/)


네, 아주 날카로운 관찰이십니다! 겉보기에는 이름이 똑같은 def amount(self)가 2번 선언되어서 충돌이 나거나 덮어써질 것 같지만, 파이썬에서는 위에 붙은 데코레이터(@) 덕분에 둘을 완전히 다른 역할로 구분하여 인식합니다.
이름은 같아도 컴퓨터는 아래와 같이 다르게 처리합니다.
## 1. 첫 번째 def amount(self) + @property

* 역할: 값을 읽어오는 Getter
* 컴퓨터가 이해하는 방식: "앞으로 사용자가 내역.amount라고 호출(출력)하면, 이 첫 번째 함수를 실행해서 값을 넘겨주자."

## 2. 두 번째 def amount(self, value) + @amount.setter

* 역할: 값을 수정하는 Setter
* 컴퓨터가 이해하는 방식: "앞으로 사용자가 내역.amount = 5000처럼 뒤에 등호(=)를 붙여 대입(수정)하려고 하면, 이 두 번째 함수를 실행해서 검사하자."

------------------------------
## 💡 왜 파이썬은 이름을 똑같이 만들도록 설계했을까요?
사용하는 사람 입장에서 하나의 변수를 다루는 것처럼 통일감을 주기 위해서입니다.
만약 이름을 다르게 지어야 했다면 코드가 아래처럼 지저분해졌을 것입니다.

# 만약 이름이 달라야 했다면? (실제 파이썬 방식 아님)
print(t.get_amount())      # 읽을 때
t.set_amount(10000)        # 쓸 때

하지만 파이썬은 데코레이터를 이용해 이름을 amount 하나로 통일해 준 덕분에, 쓰는 사람은 복잡한 메서드 이름을 외울 필요 없이 마치 일반 변수 하나를 다루듯 직관적으로 코딩할 수 있게 됩니다.

# 파이썬이 이름을 똑같이 맞추게 해준 덕분에 가능한 직관적인 방식
print(t.amount)            # 읽을 때 (첫 번째 amount 함수 실행)
t.amount = 10000           # 쓸 때 (두 번째 amount 함수 실행)

즉, "이름은 같지만, 동작하는 타이밍(읽기 vs 쓰기)이 다른 두 개의 함수"라고 이해하시면 됩니다.
데코레이터 문법의 이 독특한 특징이 이제 좀 이해가 가시나요? 혹시 가계부 데이터베이스 코드와 관련해서 또 헷갈리거나 직관적으로 이해되지 않는 부분이 있다면 편하게 말씀해 주세요!

네, 다른 방법이 존재합니다! 파이썬에서 Getter와 Setter를 설정하는 방법은 크게 4가지가 있습니다.
어렴풋이 기억나셨던 문법은 아마 데코레이터를 쓰지 않고 클래스 하단에 한 줄로 정의하는 property() 내장 함수 방식이거나, 더 강력한 검문소를 만드는 __setattr__ 마법 메서드 방식일 것입니다. [1, 2] 
상황에 따라 골라 쓸 수 있는 나머지 3가지 방법을 가계부 예제와 함께 소개해 드립니다. [3] 
------------------------------
## 1. 데코레이터가 없던 시절의 방식: property() 내장 함수 [4] 
파이썬 초창기나 데코레이터 문법을 선호하지 않는 개발자들이 쓰는 방식입니다. 일반 메서드를 먼저 만든 뒤, 클래스 하단에서 property(getter, setter) 형태로 묶어 변수에 대입합니다. [4, 5, 6] 

class OldLedger:
    def __init__(self, amount):
        self._amount = amount

    # 1. 평범한 이름으로 일반 메서드를 만듭니다.
    def get_amount(self):
        return self._amount

    def set_amount(self, value):
        if value < 0: raise ValueError("음수 불가")
        self._amount = value

    # 2. 하단에서 property 함수로 묶어 변수에 할당합니다.
    # property(fget, fset) 순서입니다.
    amount = property(get_amount, set_amount)
# 사용법은 똑같습니다.t = OldLedger(1000)
t.amount = 2000  # set_amount 가 실행됨


* 장점: 데코레이터 없이 한눈에 getter/setter 관계를 클래스 끝에서 매핑할 수 있습니다. t.get_amount()처럼 기존 함수 호출 방식으로도 쓸 수 있습니다. [6] 

------------------------------
## 2. 모든 변수를 한 곳에서 통제하는 방식: __setattr__ 마법 메서드
변수가 수십 개인데 일일이 @property를 달기 귀찮을 때 쓰는 강력한 방법입니다. 클래스 내부로 들어오는 모든 대입 연산(=)을 하나의 길목(메서드)에서 가로채서 검사합니다. [1, 7] 

class AutoCheckLedger:
    def __init__(self, category: str, amount: int):
        self.category = category
        self.amount = amount  # 이 순간에도 __setattr__ 검문소가 켜집니다.

    # 클래스의 어떤 변수든 등호(=)로 값이 대입될 때 무조건 실행되는 마법 메서드
    def __setattr__(self, name, value):
        # 금액(amount) 변수에 값이 들어올 때만 특별 검사 진행!
        if name == "amount" and value < 0:
            raise ValueError("💸 가계부 금액은 음수가 될 수 없습니다!")
        
        # 검사를 통과하면 부모(super) 객체의 기능을 빌려 원래대로 값을 저장함
        super().__setattr__(name, value)
t = AutoCheckLedger("식비", 10000)
t.amount = -500  # ❌ ValueError: 가계부 금액은 음수가 될 수 없습니다!


* 장점: 변수가 아무리 많아도 이 메서드 하나만 구현해 두면 모든 변수의 유효성 검사를 1타 2피로 처리할 수 있어 대규모 프레임워크에서 자주 씁니다.

------------------------------
## 3. 가장 고급 기법: 디스크립터 (Descriptor) 클래스
데이터의 성격(예: "0 이상의 정수여야 함") 자체를 별도의 클래스로 분리하여 재사용하는 방식입니다. 여러 클래스에서 똑같은 검사 로직(Getter/Setter)이 중복될 때 매우 유용합니다. [1, 8, 9] 

# 1. '음수가 안 되는 숫자 변수'라는 타입(검문소)을 독립된 클래스로 정의class PositiveInteger:
    def __set_name__(self, owner, name):
        self.name = f"_{name}" # 실제 값이 저장될 내부 변수명 세팅

    def __get__(self, instance, owner):
        return getattr(instance, self.name)

    def __set__(self, instance, value):
        if value < 0:
            raise ValueError(f"❌ {value}는 입력할 수 없습니다. 음수 불가!")
        setattr(instance, self.name, value)
# 2. 실제 가계부 클래스에서 위 장치를 가져다 씀class SmartLedger:
    # 이 클래스의 amount와 fee 변수는 이제 무조건 0 이상이어야 함
    amount = PositiveInteger()
    fee = PositiveInteger()

    def __init__(self, amount, fee):
        self.amount = amount
        self.fee = fee


* 장점: 가계부뿐만 아니라 은행 앱, 쇼핑몰 장바구니 등 수많은 클래스에서 똑같은 양수 검사 로직을 재사용하고 싶을 때 복사 붙여넣기 없이 완벽하게 모듈화할 수 있습니다.

------------------------------
## 📌 어떤 상황에 뭘 써야 할까요?

   1. 일반적인 상황: 무조건 맨 처음 배웠던 @property 데코레이터가 파이썬에서 표준(Pythonic)으로 권장되는 방식입니다.
   2. 과거 코드 유지보수: 예전 소스코드에서 property() 함수 형태를 만나면 당황하지 않고 읽으실 수 있으면 됩니다.
   3. 특수한 대규모 프레임워크 구현: 변수가 너무 많아 자동화가 필요할 때만 __setattr__이나 디스크립터를 꺼내 듭니다. [1, 5, 8, 10, 11] 

기억 저편에 있던 문법 모양과 매칭되는 방식이 이 중에 있었나요? 가계부 데이터베이스 공부 방향을 이 기법들을 섞어 정교하게 만들어 볼지, 아니면 다른 기능으로 넘어갈지 선택해 주세요!

[1] [https://realpython.com](https://realpython.com/python-getter-setter/)
[2] [https://www.reddit.com](https://www.reddit.com/r/learnpython/comments/fk51jz/getters_and_setter_in_python_using_property/)
[3] [https://salma-mohamed.medium.com](https://salma-mohamed.medium.com/getters-setters-and-deleters-in-python-b8ae8fc02662)
[4] [https://stackoverflow.com](https://stackoverflow.com/questions/6618002/using-property-versus-getters-and-setters)
[5] [https://stackoverflow.com](https://stackoverflow.com/questions/6618002/using-property-versus-getters-and-setters)
[6] [https://jinmay.github.io](https://jinmay.github.io/2019/11/23/python/python-class-first/)
[7] [https://stackoverflow.com](https://stackoverflow.com/questions/17576009/python-class-property-use-setter-but-evade-getter)
[8] [https://realpython.com](https://realpython.com/python-getter-setter/)
[9] [https://www.geeksforgeeks.org](https://www.geeksforgeeks.org/python/getter-and-setter-in-python/)
[10] [https://nyyang.tistory.com](https://nyyang.tistory.com/79)
[11] [https://ardentdays.tistory.com](https://ardentdays.tistory.com/61)


@dataclass를 사용하면서도 특정 변수에 "금액은 음수가 될 수 없다" 같은 나만의 조건(유효성 검사)을 넣고 싶을 때 사용할 수 있는 방법은 크게 2가지가 있습니다.
상황에 맞는 가장 직관적이고 깔끔한 해결책을 가계부 예제로 보여드릴게요.
------------------------------
## 방법 1. @dataclass 안에 @property 섞어 쓰기 (가장 추천 ⭐️)
데코레이터 @dataclass가 자동으로 만들어주는 기본 기능을 내버려 두고, 조건 검사가 필요한 특정 변수만 직접 Getter/Setter로 덮어쓰는(Override) 방식입니다.
이 방식을 쓸 때는 @dataclass가 엉뚱한 변수를 만들지 않도록 데이터 타입을 지정할 때 실제 저장 공간인 언더바 명칭(_amount)을 활용해야 합니다.

from dataclasses import dataclass

@dataclassclass Transaction:
    category: str
    _amount: int = 0  # 1. 실제 값이 저장될 변수는 언더바(_)를 붙여 선언

    # 2. 외부에서 접근할 이름으로 Getter(property) 정의
    @property
    def amount(self) -> int:
        return self._amount

    # 3. 여기에 내가 원하는 조건을 채워 넣은 Setter 정의
    @amount.setter
    def amount(self, value: int):
        if value < 0:
            print("❌ 오류: 가계부 금액은 음수가 될 수 없습니다!")
            return  # 조건에 맞지 않으면 저장하지 않고 튕겨냄
        self._amount = value
# --- 작동 테스트 ---# 생성할 때 실제 저장 변수인 _amount로 값을 넣어줍니다.t = Transaction(category="식비", _amount=10000)

print(t.amount)   # 출력: 10000 (Getter 작동)

t.amount = -5000  # ❌ 오류: 가계부 금액은 음수가 될 수 없습니다! (Setter 조건 검사 작동)
print(t.amount)   # 출력: 10000 (기존 안전한 값 유지)

t.amount = 12000  # ✅ 정상 변경
print(t.amount)   # 출력: 12000

------------------------------
## 방법 2. __post_init__ 메서드로 생성 시점에만 검사하기
만약 "수정할 때"가 아니라, 처음 가계부 데이터를 "생성(초기화)하는 시점"에만 조건이 맞는지 꼼꼼하게 검사하고 싶다면 파이썬 데이터클래스가 제공하는 특수 메서드인 __post_init__을 쓰면 됩니다.
__init__ 생성자가 실행된 '직후(Post)'에 자동으로 호출되어 조건을 검사해 주는 장치입니다.

from dataclasses import dataclass

@dataclassclass StrictTransaction:
    category: str
    amount: int

    # 데이터클래스가 자동으로 세팅을 다 끝낸 직후에 실행되는 검문소
    def __post_init__(self):
        if self.amount < 0:
            # 아예 프로그램이 잘못된 데이터를 바탕으로 돌지 못하도록 예외를 발생시킴
            raise ValueError(f"❌ 가계부 금액 오류: {self.amount}원은 불가능합니다.")
        
        if not self.category:
            raise ValueError("❌ 카테고리 칸은 비워둘 수 없습니다.")
# --- 작동 테스트 ---try:
    # 생성 시점에 조건 검사기가 돌아갑니다.
    invalid_data = StrictTransaction(category="교통비", amount=-1500)except ValueError as e:
    print(e)  # 출력: ❌ 가계부 금액 오류: -1500원은 불가능합니다.

------------------------------
## 📌 요약 가이드

* 데이터를 수시로 변경해야 하고, 변경할 때마다 조건을 체크해야 한다 ➡️ 방법 1 (@property 조합)을 사용하세요.
* 한번 만들 때만 똑바로 검사하면 되고, 이후엔 바꿀 일이 거의 없다 ➡️ 코드가 훨씬 간결해지는 방법 2 (__post_init__)를 사용하세요.

가계부 앱의 특성상 잘못된 데이터 입력을 막는 것은 매우 중요합니다. 혹시 이 조건 검사 코드를 우리가 처음에 만들었던 LedgerDatabase(전체 장부 클래스) 시스템에 합쳐서 완성도 높은 가계부를 만들어 보고 싶으신가요? 아니면 이 문법에 대해 더 궁금한 점이 있으신가요?

