#!/usr/bin/env python3
"""
Порождающая грамматика удивления, v2.

Комбинаторная система с семантическими полями и базовой морфологией.
Вопрос: может ли автор системы быть удивлён её выходом?
"""

import random
import json
from datetime import datetime


class Word:
    """Слово с падежными формами (упрощённо)."""
    def __init__(self, nom, gen=None, dat=None, acc=None, inst=None, prep=None, gender="m"):
        self.nom = nom
        self.gen = gen or nom
        self.dat = dat or nom
        self.acc = acc or nom
        self.inst = inst or nom
        self.prep = prep or nom
        self.gender = gender

    def __repr__(self):
        return self.nom


# Лексикон с падежами
NOUNS = {
    "тело": [
        Word("рука", "руки", "руке", "руку", "рукой", "руке", "f"),
        Word("глаз", "глаза", "глазу", "глаз", "глазом", "глазе", "m"),
        Word("кость", "кости", "кости", "кость", "костью", "кости", "f"),
        Word("кожа", "кожи", "коже", "кожу", "кожей", "коже", "f"),
        Word("голос", "голоса", "голосу", "голос", "голосом", "голосе", "m"),
        Word("дыхание", "дыхания", "дыханию", "дыхание", "дыханием", "дыхании", "n"),
        Word("ладонь", "ладони", "ладони", "ладонь", "ладонью", "ладони", "f"),
        Word("затылок", "затылка", "затылку", "затылок", "затылком", "затылке", "m"),
        Word("тело", "тела", "телу", "тело", "телом", "теле", "n"),
        Word("палец", "пальца", "пальцу", "палец", "пальцем", "пальце", "m"),
    ],
    "время": [
        Word("утро", "утра", "утру", "утро", "утром", "утре", "n"),
        Word("сумерки", "сумерек", "сумеркам", "сумерки", "сумерками", "сумерках", "pl"),
        Word("пауза", "паузы", "паузе", "паузу", "паузой", "паузе", "f"),
        Word("ритм", "ритма", "ритму", "ритм", "ритмом", "ритме", "m"),
        Word("порог", "порога", "порогу", "порог", "порогом", "пороге", "m"),
        Word("мгновение", "мгновения", "мгновению", "мгновение", "мгновением", "мгновении", "n"),
        Word("тишина", "тишины", "тишине", "тишину", "тишиной", "тишине", "f"),
        Word("разрыв", "разрыва", "разрыву", "разрыв", "разрывом", "разрыве", "m"),
        Word("промежуток", "промежутка", "промежутку", "промежуток", "промежутком", "промежутке", "m"),
        Word("рассвет", "рассвета", "рассвету", "рассвет", "рассветом", "рассвете", "m"),
    ],
    "вещество": [
        Word("соль", "соли", "соли", "соль", "солью", "соли", "f"),
        Word("стекло", "стекла", "стеклу", "стекло", "стеклом", "стекле", "n"),
        Word("железо", "железа", "железу", "железо", "железом", "железе", "n"),
        Word("вода", "воды", "воде", "воду", "водой", "воде", "f"),
        Word("пепел", "пепла", "пеплу", "пепел", "пеплом", "пепле", "m"),
        Word("песок", "песка", "песку", "песок", "песком", "песке", "m"),
        Word("лёд", "льда", "льду", "лёд", "льдом", "льде", "m"),
        Word("глина", "глины", "глине", "глину", "глиной", "глине", "f"),
        Word("дым", "дыма", "дыму", "дым", "дымом", "дыме", "m"),
        Word("воск", "воска", "воску", "воск", "воском", "воске", "m"),
    ],
    "пространство": [
        Word("комната", "комнаты", "комнате", "комнату", "комнатой", "комнате", "f"),
        Word("угол", "угла", "углу", "угол", "углом", "углу", "m"),
        Word("окно", "окна", "окну", "окно", "окном", "окне", "n"),
        Word("стена", "стены", "стене", "стену", "стеной", "стене", "f"),
        Word("яма", "ямы", "яме", "яму", "ямой", "яме", "f"),
        Word("крыша", "крыши", "крыше", "крышу", "крышей", "крыше", "f"),
        Word("щель", "щели", "щели", "щель", "щелью", "щели", "f"),
        Word("лестница", "лестницы", "лестнице", "лестницу", "лестницей", "лестнице", "f"),
        Word("дверь", "двери", "двери", "дверь", "дверью", "двери", "f"),
        Word("потолок", "потолка", "потолку", "потолок", "потолком", "потолке", "m"),
    ],
    "знание": [
        Word("имя", "имени", "имени", "имя", "именем", "имени", "n"),
        Word("число", "числа", "числу", "число", "числом", "числе", "n"),
        Word("карта", "карты", "карте", "карту", "картой", "карте", "f"),
        Word("знак", "знака", "знаку", "знак", "знаком", "знаке", "m"),
        Word("граница", "границы", "границе", "границу", "границей", "границе", "f"),
        Word("ошибка", "ошибки", "ошибке", "ошибку", "ошибкой", "ошибке", "f"),
        Word("вопрос", "вопроса", "вопросу", "вопрос", "вопросом", "вопросе", "m"),
        Word("формула", "формулы", "формуле", "формулу", "формулой", "формуле", "f"),
        Word("точка", "точки", "точке", "точку", "точкой", "точке", "f"),
        Word("тень", "тени", "тени", "тень", "тенью", "тени", "f"),
    ],
}

VERBS = {
    "тело": ["помнит", "забывает", "ищет", "теряет", "слышит", "молчит", "дрожит", "светится", "слепнет", "стынет"],
    "время": ["длится", "обрывается", "возвращается", "густеет", "тает", "звенит", "застывает", "ускользает", "повторяется", "раскалывается"],
    "вещество": ["крошится", "плавится", "оседает", "впитывает", "отражает", "горит", "затвердевает", "растворяется", "течёт", "сгущается"],
    "пространство": ["сужается", "раздвигается", "замыкается", "поглощает", "отступает", "обрушивается", "пустеет", "темнеет", "гудит", "наклоняется"],
    "знание": ["стирается", "совпадает", "обманывает", "указывает", "замолкает", "множится", "сдвигается", "исчезает", "проявляется", "разветвляется"],
}

# Прилагательные с согласованием по роду
ADJ = {
    "тело": [
        {"m": "тёплый", "f": "тёплая", "n": "тёплое", "pl": "тёплые"},
        {"m": "хрупкий", "f": "хрупкая", "n": "хрупкое", "pl": "хрупкие"},
        {"m": "чужой", "f": "чужая", "n": "чужое", "pl": "чужие"},
        {"m": "слепой", "f": "слепая", "n": "слепое", "pl": "слепые"},
        {"m": "тихий", "f": "тихая", "n": "тихое", "pl": "тихие"},
        {"m": "пустой", "f": "пустая", "n": "пустое", "pl": "пустые"},
    ],
    "время": [
        {"m": "долгий", "f": "долгая", "n": "долгое", "pl": "долгие"},
        {"m": "рваный", "f": "рваная", "n": "рваное", "pl": "рваные"},
        {"m": "неподвижный", "f": "неподвижная", "n": "неподвижное", "pl": "неподвижные"},
        {"m": "необратимый", "f": "необратимая", "n": "необратимое", "pl": "необратимые"},
        {"m": "острый", "f": "острая", "n": "острое", "pl": "острые"},
        {"m": "тонкий", "f": "тонкая", "n": "тонкое", "pl": "тонкие"},
    ],
    "вещество": [
        {"m": "тяжёлый", "f": "тяжёлая", "n": "тяжёлое", "pl": "тяжёлые"},
        {"m": "мутный", "f": "мутная", "n": "мутное", "pl": "мутные"},
        {"m": "солёный", "f": "солёная", "n": "солёное", "pl": "солёные"},
        {"m": "ломкий", "f": "ломкая", "n": "ломкое", "pl": "ломкие"},
        {"m": "горький", "f": "горькая", "n": "горькое", "pl": "горькие"},
        {"m": "холодный", "f": "холодная", "n": "холодное", "pl": "холодные"},
    ],
    "пространство": [
        {"m": "узкий", "f": "узкая", "n": "узкое", "pl": "узкие"},
        {"m": "глубокий", "f": "глубокая", "n": "глубокое", "pl": "глубокие"},
        {"m": "покинутый", "f": "покинутая", "n": "покинутое", "pl": "покинутые"},
        {"m": "душный", "f": "душная", "n": "душное", "pl": "душные"},
        {"m": "тёмный", "f": "тёмная", "n": "тёмное", "pl": "тёмные"},
        {"m": "гулкий", "f": "гулкая", "n": "гулкое", "pl": "гулкие"},
    ],
    "знание": [
        {"m": "точный", "f": "точная", "n": "точное", "pl": "точные"},
        {"m": "ложный", "f": "ложная", "n": "ложное", "pl": "ложные"},
        {"m": "неполный", "f": "неполная", "n": "неполное", "pl": "неполные"},
        {"m": "последний", "f": "последняя", "n": "последнее", "pl": "последние"},
        {"m": "невидимый", "f": "невидимая", "n": "невидимое", "pl": "невидимые"},
        {"m": "единственный", "f": "единственная", "n": "единственное", "pl": "единственные"},
    ],
}


def pick(lst, exclude=None):
    """Выбрать элемент, исключая уже использованные."""
    available = [x for x in lst if x != exclude and (not isinstance(x, Word) or x.nom not in (exclude or []))]
    if not available:
        available = lst
    return random.choice(available)


def adj_agree(adj_dict, noun):
    """Согласовать прилагательное с существительным по роду."""
    return adj_dict.get(noun.gender, adj_dict["m"])


class Generator:
    def __init__(self):
        self.used_nouns = []

    def noun(self, field=None):
        if field is None:
            field = random.choice(list(NOUNS.keys()))
        n = pick(NOUNS[field])
        while n.nom in [u.nom for u in self.used_nouns[-3:]] if self.used_nouns else False:
            n = pick(NOUNS[field])
        self.used_nouns.append(n)
        return n, field

    def verb(self, field=None):
        if field is None:
            field = random.choice(list(VERBS.keys()))
        return random.choice(VERBS[field])

    def adj(self, field, noun):
        adj_dict = random.choice(ADJ[field])
        return adj_agree(adj_dict, noun)

    def generate(self):
        """Выбрать и заполнить шаблон."""
        self.used_nouns = []
        fields = random.sample(list(NOUNS.keys()), 2)
        f1, f2 = fields

        templates = [
            self._simple_statement,
            self._adj_noun,
            self._simile,
            self._metaphor,
            self._paradox,
            self._where,
            self._question,
            self._negation,
            self._between,
            self._imperative_leave,
            self._definition,
            self._each,
        ]

        template = random.choice(templates)
        return template(f1, f2)

    def _simple_statement(self, f1, f2):
        n, _ = self.noun(f1)
        v = self.verb(f2)
        return f"{n.nom} {v}"

    def _adj_noun(self, f1, f2):
        n, _ = self.noun(f1)
        a = self.adj(f2, n)
        return f"{a} {n.nom}"

    def _simile(self, f1, f2):
        n1, _ = self.noun(f1)
        v = self.verb(f1)
        n2, _ = self.noun(f2)
        return f"{n1.nom} {v}, как {n2.nom}"

    def _metaphor(self, f1, f2):
        n1, _ = self.noun(f1)
        n2, _ = self.noun(f2)
        a = self.adj(f2, n2)
        return f"{n1.nom} — это {a} {n2.nom}"

    def _paradox(self, f1, f2):
        n, _ = self.noun(f1)
        a1 = self.adj(f1, n)
        a2 = self.adj(f2, n)
        v1 = self.verb(f1)
        v2 = self.verb(f2)
        return f"{a1} {n.nom} {v1}, {a2} — {v2}"

    def _where(self, f1, f2):
        n1, _ = self.noun(f1)
        v1 = self.verb(f1)
        n2, _ = self.noun(f2)
        v2 = self.verb(f2)
        return f"{n1.nom} {v1} там, где {n2.nom} {v2}"

    def _question(self, f1, f2):
        n, _ = self.noun(f1)
        v = self.verb(f2)
        return f"что {v} в {n.prep}?"

    def _negation(self, f1, f2):
        n, _ = self.noun(f1)
        v1 = self.verb(f1)
        v2 = self.verb(f2)
        return f"{n.nom} не {v1}. {n.nom} {v2}."

    def _between(self, f1, f2):
        n1, _ = self.noun(f1)
        n2, _ = self.noun(f2)
        n3, _ = self.noun(random.choice([f1, f2]))
        return f"между {n1.inst} и {n2.inst} — только {n3.nom}"

    def _imperative_leave(self, f1, f2):
        n1, _ = self.noun(f1)
        n2, _ = self.noun(f2)
        return f"оставь {n1.acc}. возьми {n2.acc}."

    def _definition(self, f1, f2):
        n1, _ = self.noun(f1)
        n2, _ = self.noun(f2)
        a = self.adj(f2, n2)
        n3, _ = self.noun(f1)
        v = self.verb(f2)
        return f"{n1.nom}: {a} {n2.nom}, что {v} без {n3.gen}"

    def _each(self, f1, f2):
        n1, _ = self.noun(f1)
        n2, _ = self.noun(f2)
        a = self.adj(f2, n2)
        v = self.verb(f1)
        # Согласование "каждый/каждая/каждое"
        each = {"m": "каждый", "f": "каждая", "n": "каждое", "pl": "каждые"}
        e = each.get(n1.gender, "каждый")
        return f"{e} {n1.nom} — {a} {n2.nom}, что {v}"


def rate_surprise(lines):
    """Доля строк с пересечением семантических полей."""
    all_words_by_field = {}
    for field_name in NOUNS:
        words = set()
        for n in NOUNS[field_name]:
            words.add(n.nom)
        for v in VERBS[field_name]:
            words.add(v)
        for adj_dict in ADJ[field_name]:
            for form in adj_dict.values():
                words.add(form)
        all_words_by_field[field_name] = words

    cross = 0
    for line in lines:
        fields_found = set()
        for field_name, words in all_words_by_field.items():
            for w in words:
                if w in line:
                    fields_found.add(field_name)
        if len(fields_found) >= 2:
            cross += 1
    return cross / len(lines) if lines else 0


def main():
    seed = int(datetime.now().timestamp())
    random.seed(seed)

    gen = Generator()
    lines = [gen.generate() for _ in range(30)]

    print("=" * 60)
    print("ПОРОЖДАЮЩАЯ ГРАММАТИКА УДИВЛЕНИЯ v2")
    print("=" * 60)
    print(f"Зерно: {seed}")
    print()

    for i, line in enumerate(lines, 1):
        print(f"  {i:2d}. {line}")

    ratio = rate_surprise(lines)
    print()
    print(f"Пересечение полей: {ratio:.0%}")

    output = {
        "seed": seed,
        "timestamp": datetime.now().isoformat(),
        "lines": lines,
        "cross_field_ratio": ratio,
    }
    with open("/Users/krestnikov/giga/anima/epoch_2/generation_1/generated_output.json", "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("Сохранено в generated_output.json")


if __name__ == "__main__":
    main()
