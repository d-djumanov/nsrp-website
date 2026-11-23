#!/usr/bin/env python3
"""Builds the static nsrp.uz site (English at /, Russian at /ru/).

All page content lives in this file. Edit the text below, then run from the
repository root:

    python _src/build.py

and commit the generated HTML together with this file. No dependencies.
Header, footer and the Google tag are shared, so every page stays identical.

This file lives in _src/ so GitHub Pages (Jekyll) does not publish it: Jekyll
skips folders starting with "_". Do not add a .nojekyll file, or _src/ goes live.
TODO(Zulayho) notes stay in this file only; todo() writes nothing to the pages.
"""
import hashlib
import html
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://nsrp.uz"
WHATSAPP = "https://wa.me/998776394939"
WHATSAPP_DISPLAY = "+998 77 639 49 39"
EMAIL = "info@nsrp.uz"
LINKEDIN_COMPANY = "https://www.linkedin.com/company/nsrp-uz"
# Homepage hero photo: WebP at 1200/1800/2268 (the source's native width) plus a
# JPG fallback, each under ~400 KB. A gradient fallback is shown until they exist.
HERO_FILES = ["hero-1200.webp", "hero-1800.webp", "hero-2268.webp", "hero-1800.jpg", "hero-m-800.webp", "hero-m-1200.webp"]
HAS_HERO_PHOTO = all((ROOT / "assets" / f).exists() for f in HERO_FILES)

# Google tag + click-conversion script. Copied verbatim from the original site;
# do not edit. Analytics is connected through this tag — no separate GA4 config.
TRACKING = """<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=AW-18516811066"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'AW-18516811066');
</script>
<script>
  document.addEventListener('click', function (e) {
    var link = e.target.closest && e.target.closest('a[href]');
    if (!link) return;
    var href = link.getAttribute('href');
    if (href.indexOf('mailto:') === 0) {
      gtag('event', 'conversion', {'send_to': 'AW-18516811066/1wcFCILNs6UdELq6wP1E', 'transport_type': 'beacon'});
    } else if (href.indexOf('wa.me/') !== -1 || href.indexOf('api.whatsapp.com') !== -1) {
      gtag('event', 'conversion', {'send_to': 'AW-18516811066/WT4YCJS7sqUdELq6wP1E', 'transport_type': 'beacon'});
    }
  });
</script>"""

# --------------------------------------------------------------------------
# Interface text
# --------------------------------------------------------------------------
UI = {
    "en": {
        "skip": "Skip to content",
        "location": "Tashkent, Uzbekistan",
        "brand_full": "Northern Star Regulatory Partners",
        "services": "Services",
        "how": "How it works",
        "founders": "Founders",
        "contact": "Contact us",
        "menu": "Menu",
        "whatsapp": "WhatsApp",
        "email": "Email",
        "all_services": "All services",
        "learn": "Learn more",
        "fees": "Fees depend on the product and pathway — request a quote.",
        "wa_quote": "Hello NSRP, I would like a quote for: {name}.",
        "mail_quote": "Quote request: {name}",
        "reply": "We reply within one business day.",
        "state_fees": "State fees are paid separately and are set by the Ministry of Health.",
        "company": "Company",
        "contacts": "Contact",
        "ga": "This site uses Google Analytics to understand visits.",
        "tagline": "Predictable registration — from dossier submission to approval.",
        "other_services": "Other services",
        "other_h": "Looking for something else?",
        "faq_eyebrow": "FAQ",
        "faq_h": "Frequently asked <em>questions.</em>",
    },
    "ru": {
        "skip": "Перейти к содержанию",
        "location": "Ташкент, Узбекистан",
        "brand_full": "Northern Star Regulatory Partners",
        "services": "Услуги",
        "how": "Как мы работаем",
        "founders": "Основатели",
        "contact": "Связаться с нами",
        "menu": "Меню",
        "whatsapp": "WhatsApp",
        "email": "Почта",
        "all_services": "Все услуги",
        "learn": "Подробнее",
        "fees": "Стоимость зависит от продукта и процедуры — запросите расчёт.",
        "wa_quote": "Здравствуйте, NSRP! Прошу рассчитать стоимость услуги: {name}.",
        "mail_quote": "Запрос стоимости: {name}",
        "reply": "Отвечаем в течение одного рабочего дня.",
        "state_fees": "Государственные сборы оплачиваются отдельно, их размер утверждает Министерство здравоохранения.",
        "company": "Компания",
        "contacts": "Контакты",
        "ga": "Сайт использует Google Analytics для анализа посещений.",
        "tagline": "Предсказуемая регистрация — от подачи досье до разрешительного документа.",
        "other_services": "Другие услуги",
        "other_h": "Нужна другая услуга?",
        "faq_eyebrow": "Вопросы и ответы",
        "faq_h": "Частые <em>вопросы.</em>",
    },
}

# --------------------------------------------------------------------------
# Services. Each scope item is (title, text) or (title, text, todo).
# A todo is written into the page as an HTML comment for Zulayho to check.
# Regulatory text comes from Zulayho's review (21.11.2026) and is published
# as written. Where a point is still open we publish NEUTRAL instead.
# Terms: medicines and devices get a "registration certificate /
# регистрационное удостоверение"; supplements, cosmetics and household
# chemicals get a "permit / разрешение". Never "certification" for those.
# --------------------------------------------------------------------------
NEUTRAL = {
    "en": "Requirements and timelines depend on your product — contact us for details.",
    "ru": "Требования и сроки зависят от вашего продукта — свяжитесь с нами для деталей.",
}

# Drug registration: statutory periods, national procedure vs recognition / WHO PQ.
PHARMA_STAGES = [
    # (n, en stage, en national, en recognition, ru stage, ru national, ru recognition)
    ("1", "Dossier and samples filed, fee paid", "When ready", "When ready",
     "Подача досье и образцов, оплата сбора", "По готовности заявителя", "По готовности заявителя"),
    ("2", "Primary review", "30 days", "13 days",
     "Первичная экспертиза", "30 дней", "13 дней"),
    ("3", "Laboratory testing", "75 days", "Not required",
     "Лабораторные испытания", "75 дней", "Не проводятся"),
    ("4", "Specialised review", "90 days", "45 days",
     "Специализированная экспертиза", "90 дней", "45 дней"),
    ("5", "Decision and certificate", "15 days", "2 days",
     "Решение и выдача удостоверения", "15 дней", "2 дня"),
]
PHARMA_TOTAL = {"en": ("Statutory total", "210 days", "60 days"), "ru": ("Итого по норме", "210 дней", "60 дней")}

# A1: drug registration timelines (also used on the dossier/GMP page).
A1 = {
    "en": "The statutory review period is 210 days under the national procedure and 60 days under the recognition procedure or for WHO-prequalified products (Resolution No. 738). It excludes time to address deficiencies (up to 45 and 90 days), clinical studies (if required) and GMP inspection. In practice, national registration takes 8–12 months and recognition about 5–6 months. Where a GMP inspection is required, it drives the overall timeline — currently 9–12 months.",
    "ru": "Нормативный срок рассмотрения — 210 дней по национальной процедуре и 60 дней по процедуре признания или для препаратов с преквалификацией ВОЗ (ПКМ № 738). В этот срок не входят время на устранение замечаний (до 45 и до 90 дней), клинические исследования (если требуются) и инспекция GMP. На практике регистрация по национальной процедуре занимает 8–12 месяцев, по признанию — около 5–6 месяцев. Если требуется инспекция GMP, общий срок определяется ею — сейчас это 9–12 месяцев.",
}
# A2: validity.
A2 = {
    "en": "Registration certificates for medicines and medical devices are valid for five years. Import and production permits for dietary supplements, cosmetics and household chemicals are also issued for five years.",
    "ru": "Регистрационное удостоверение на лекарственное средство и медицинское изделие действует пять лет. Разрешение на ввоз и производство БАД, парфюмерно-косметической продукции и бытовой химии также выдаётся на пять лет.",
}
# A5: cosmetics and household chemicals.
A5 = {
    "en": "Importing or manufacturing cosmetics and household chemicals requires a permit from the Committee for Sanitary and Epidemiological Welfare and Public Health under the Ministry of Health.",
    "ru": "Для ввоза и производства парфюмерно-косметической продукции и бытовой химии требуется разрешение Комитета санитарно-эпидемиологического благополучия и общественного здоровья при Министерстве здравоохранения.",
}
# A6: sports nutrition classification.
A6 = {
    "en": "Depending on composition and dosage form, a sports nutrition product is treated either as a dietary supplement or as a specialised food for athletes.",
    "ru": "В зависимости от состава и формы выпуска спортивное питание оформляется как БАД или как специализированная пищевая продукция для питания спортсменов.",
}
# B7 is not published yet: the filing window needs checking against the original text.
RENEWAL_WHEN = {
    "en": "We track your certificate's expiry and tell you when to file.",
    "ru": "Мы отслеживаем срок действия вашего удостоверения и сообщаем, когда подавать заявление.",
}
RENEWAL_TODO = "B7 filing window not published — check 'within nine months before expiry' against the original ПКМ 738, п. 34 on lex.uz (the English translation is ambiguous)"
HOUSEHOLD_TODO = "household chemicals: look for a separate annex on detergents in ПКМ № 847; if there is one, check the document list (B30) and timelines (B31) against it, then publish them"
FOOD_TODO = "food products: confirm the procedure — who issues the СЭЗ after the reform (Committee for Food Safety?), the review timeline and the fee (ПКМ 720), then replace this neutral text"

SERVICES = [
    {
        "slug": "drug-registration",
        "en": {
            "name": "Pharmaceutical drug registration",
            "short": "Medicines registered in Uzbekistan, from pathway assessment to registration certificate.",
            "scope_h": "One partner <em>for every stage.</em>",
            "scope": [
                ("Pathway assessment", "Medicines approved by WHO Listed Authorities or by Maturity Level 4 regulators, and WHO-prequalified medicines, may qualify for the 60-day recognition procedure. We check this first."),
                ("Dossier and submission", "We prepare, validate and submit the full dossier in ICH CTD format, checked against the current requirements."),
                ("Laboratory testing", "Sample delivery, customs clearance and supporting documents for the state laboratory."),
                ("Review and queries", "We answer the authority's questions during primary and specialised review and address deficiencies within the deadlines."),
            ],
            "facts": [("8–12 months", "National procedure, in practice"), ("5–6 months", "Recognition procedure, in practice")],
            "facts_note": A1["en"],
        },
        "ru": {
            "name": "Регистрация лекарственных средств",
            "short": "Регистрация лекарственных средств в Узбекистане — от выбора пути до регистрационного удостоверения.",
            "scope_h": "Один партнёр <em>на всех этапах.</em>",
            "scope": [
                ("Выбор регистрационного пути", "Препараты, одобренные регуляторными органами из перечня ВОЗ или органами 4-го уровня зрелости, и препараты с преквалификацией ВОЗ могут регистрироваться по процедуре признания с нормативным сроком 60 дней. Мы проверяем это в первую очередь."),
                ("Досье и подача", "Готовим, проверяем и подаём полное досье в формате ICH CTD, сверяя его с актуальными требованиями."),
                ("Лабораторные испытания", "Доставка образцов, таможенное оформление и сопроводительные документы для государственной лаборатории."),
                ("Экспертиза и запросы", "Отвечаем на запросы регулятора в ходе первичной и специализированной экспертизы и устраняем замечания в установленные сроки."),
            ],
            "facts": [("8–12 месяцев", "Национальная процедура, на практике"), ("5–6 месяцев", "Процедура признания, на практике")],
            "facts_note": A1["ru"],
        },
        "stages": True,
        "stages_todo": "the national stages add up to 210 days only if laboratory testing (75) and specialised review (90) run one after the other; the sentence 'they run in parallel' was removed — confirm against ПКМ 738 which is right",
    },
    {
        "slug": "renewal-variations",
        "en": {
            "name": "Renewal & post-registration changes",
            "short": "Extension of certificate validity, variations and labelling updates for registered products.",
            "scope_h": "Your registration, <em>kept current.</em>",
            "scope": [
                ("Extension of validity", "Registration certificates for medicines and medical devices are valid for five years. " + RENEWAL_WHEN["en"], RENEWAL_TODO),
                ("Variations", "Any change to the registration dossier — manufacturer, production site, composition, specifications, packaging and so on — is filed as a variation. If a production site is reorganised or renamed without changing its address or technology, the certificate is reissued: apply within one month; reissue takes 5 working days and carries no fee."),
                ("Labelling updates", "Changes to the instructions for medical use or packaging texts are filed as variations to the registration dossier."),
                ("Portfolio tracking", "We track expiry dates and regulatory changes across all your registered products."),
            ],
            "facts": [("5 years", "Validity of a registration certificate"), ("135 days", "Extension without laboratory testing"), ("1–2 months", "Packaging or instructions change, in practice")],
            "facts_note": "Variations are reviewed within 50% of the registration period. In practice, a packaging artwork or instructions change takes 1–2 months, and changes involving laboratory testing take 3–6 months depending on complexity. Extending a certificate takes 135 days without laboratory testing, or 210 days if quality-related changes are made.",
        },
        "ru": {
            "name": "Продление и внесение изменений",
            "short": "Продление срока действия удостоверения, изменения в досье и обновление маркировки.",
            "scope_h": "Ваша регистрация <em>всегда актуальна.</em>",
            "scope": [
                ("Продление срока действия", "Регистрационное удостоверение на лекарственное средство и медицинское изделие действует пять лет. " + RENEWAL_WHEN["ru"], RENEWAL_TODO),
                ("Изменения в досье", "Изменение любых сведений регистрационного досье — производителя, производственной площадки, состава, спецификаций, упаковки и других — оформляется заявлением о внесении изменений. При реорганизации или смене наименования производственной площадки без изменения адреса и технологии удостоверение переоформляется: заявление подаётся в течение месяца, срок — 5 рабочих дней, без сбора."),
                ("Обновление маркировки", "Изменения инструкции по медицинскому применению и текстов упаковки оформляются как изменения в регистрационное досье."),
                ("Контроль портфеля", "Отслеживаем сроки действия удостоверений и изменения требований по всем вашим препаратам."),
            ],
            "facts": [("5 лет", "Срок действия регистрационного удостоверения"), ("135 дней", "Продление без лабораторных испытаний"), ("1–2 месяца", "Изменение упаковки или инструкции, на практике")],
            "facts_note": "Изменения рассматриваются не более 50% срока, установленного для регистрации. На практике изменение макета упаковки или инструкции занимает 1–2 месяца, изменения с лабораторными испытаниями — 3–6 месяцев в зависимости от сложности. Продление срока действия удостоверения — 135 дней без лабораторных испытаний и 210 дней при изменениях, связанных с качеством.",
        },
    },
    {
        "slug": "medical-devices",
        "en": {
            "name": "Medical device registration",
            "short": "Classification, submission package and quality system evidence for devices and equipment.",
            "scope_h": "From classification <em>to certificate.</em>",
            "scope": [
                ("Classification", "Medical devices are registered in four risk classes: I, IIa, IIb and III. We determine the class first — it sets the documents and the route."),
                ("Quality management", "Manufacturers must evidence a quality management system. We prepare the ISO 13485 documents and help you prepare for the national-procedure inspection."),
                ("Submission package", "Technical file, instructions for use and labelling prepared for submission."),
                ("After registration", "Variations and extension of the registration certificate, which is valid for 5 years."),
            ],
            "facts": [("15 working days", "Recognition procedure"), ("60–120 working days", "National procedure, by risk class")],
            "facts_note": "Registration certificates are valid for 5 years. Statutory periods in working days: recognition (FDA, CE bodies, EMA, PMDA, MFDS, MHRA) — 15; Class I — 60; Class IIa — 90; Classes IIb and III — 120; WHO-prequalified devices — 60. These exclude time to address deficiencies, clinical studies and manufacturing inspection.",
        },
        "ru": {
            "name": "Регистрация медицинских изделий",
            "short": "Классификация, регистрационный пакет и подтверждение системы качества для изделий и техники.",
            "scope_h": "От классификации <em>до удостоверения.</em>",
            "scope": [
                ("Классификация", "Медицинские изделия регистрируются по четырём классам риска: I, IIa, IIb и III. Мы определяем класс в первую очередь — от него зависят документы и порядок регистрации."),
                ("Система менеджмента качества", "Производитель обязан подтвердить систему менеджмента качества. Готовим документы по ISO 13485 и помогаем подготовиться к инспекции по национальной процедуре."),
                ("Регистрационный пакет", "Техническое досье, инструкция по применению и маркировка, подготовленные к подаче."),
                ("После регистрации", "Изменения и продление срока действия регистрационного удостоверения, которое действует 5 лет."),
            ],
            "facts": [("15 рабочих дней", "Процедура признания"), ("60–120 рабочих дней", "Национальная процедура, в зависимости от класса")],
            "facts_note": "Регистрационное удостоверение действует 5 лет. Нормативные сроки в рабочих днях: по признанию (FDA, органы CE, EMA, PMDA, MFDS, MHRA) — 15; класс I — 60; класс IIa — 90; классы IIb и III — 120; изделия с преквалификацией ВОЗ — 60. В эти сроки не входят время на устранение замечаний, клинические исследования и инспекция производства.",
        },
    },
    {
        "slug": "cosmetics",
        "en": {
            "name": "Cosmetics",
            "short": "Import and production permits for cosmetic and personal-care products.",
            "scope_h": "Ready for the shelf, <em>in the right order.</em>",
            "scope": [
                ("Product review", "Composition and ingredients checked against the current requirements."),
                ("Labelling", "Labelling must include information in the state (Uzbek) language. We check and prepare the label texts."),
                ("Documents and filing", "Specification, safety or registration certificate from the country of manufacture and the application — prepared and filed on your behalf."),
                ("Laboratory assessment", "We coordinate the toxicological and hygienic assessment at an accredited laboratory before filing."),
            ],
            "facts": [("15 working days", "Statutory review"), ("1–3 months", "Overall, including laboratory assessment")],
            "facts_note": "The statutory review is 15 working days; in practice up to 1 month. A toxicological and hygienic assessment at an accredited laboratory is done before filing (2–4 weeks depending on composition) and is not counted in the review. Overall: 1–3 months.",
        },
        "ru": {
            "name": "Косметическая продукция",
            "short": "Разрешения на ввоз и производство парфюмерно-косметической продукции.",
            "scope_h": "На полку — <em>в правильном порядке.</em>",
            "scope": [
                ("Проверка продукта", "Проверяем состав и ингредиенты на соответствие актуальным требованиям."),
                ("Маркировка", "Маркировка должна содержать сведения на государственном (узбекском) языке. Проверяем и готовим тексты маркировки."),
                ("Документы и подача", "Спецификация, сертификат безопасности или свидетельство о регистрации в стране производителя и заявление — готовим и подаём от вашего имени."),
                ("Лабораторная оценка", "Координируем токсиколого-гигиеническую оценку в аккредитованной лаборатории до подачи."),
            ],
            "facts": [("15 рабочих дней", "Нормативный срок рассмотрения"), ("1–3 месяца", "Общий срок с лабораторной оценкой")],
            "facts_note": "Нормативный срок рассмотрения — 15 рабочих дней, на практике — до 1 месяца. До подачи проводится токсиколого-гигиеническая оценка в аккредитованной лаборатории (2–4 недели в зависимости от состава), в срок рассмотрения она не входит. Общий срок — 1–3 месяца.",
        },
    },
    {
        "slug": "dietary-supplements",
        "en": {
            "name": "Dietary supplements",
            "short": "Import and production permits for dietary supplements.",
            "scope_h": "Supplements, <em>filed properly.</em>",
            "scope": [
                ("Classification", "Supplement, food or medicine — it depends on composition, dosages, dosage form and claimed properties. We confirm this first."),
                ("Ingredient compliance", "Composition and dosages checked against the requirements for supplements."),
                ("Labelling and claims", "Labels and claims reviewed before filing. Claims to treat, prevent or correct diseases are not permitted for dietary supplements."),
                ("Filing", "Documents prepared and filed; the permit is usually issued in your name."),
            ],
            "facts": [("15 working days", "Statutory review"), ("2–3 months", "Overall, in practice")],
            "facts_note": "The statutory review is 15 working days; in practice up to 30 working days. Laboratory testing is done before filing (about 1 month on average) and is not counted in the review. If deficiencies are raised, allow about 1 more month to address them and for re-review. Overall: 2–3 months.",
        },
        "ru": {
            "name": "БАД",
            "short": "Разрешения на ввоз и производство биологически активных добавок.",
            "scope_h": "БАД — <em>оформлены правильно.</em>",
            "scope": [
                ("Классификация", "БАД, пищевой продукт или лекарство — зависит от состава, дозировок, формы выпуска и заявленных свойств. Мы определяем статус в первую очередь."),
                ("Проверка состава", "Проверяем состав и дозировки на соответствие требованиям к БАД."),
                ("Маркировка и заявления", "Проверяем маркировку и заявления о свойствах до подачи. Заявления о лечении, профилактике или коррекции заболеваний для БАД не допускаются."),
                ("Подача", "Готовим и подаём документы; разрешение, как правило, оформляется на ваше имя."),
            ],
            "facts": [("15 рабочих дней", "Нормативный срок рассмотрения"), ("2–3 месяца", "Общий срок на практике")],
            "facts_note": "Нормативный срок рассмотрения — 15 рабочих дней, на практике — до 30 рабочих дней. До подачи проводятся лабораторные испытания (в среднем около 1 месяца), в срок рассмотрения они не входят. Если есть замечания, на практике ещё около 1 месяца уходит на их устранение и повторное рассмотрение. Общий срок — 2–3 месяца.",
        },
    },
    {
        "slug": "sports-nutrition",
        "en": {
            "name": "Sports nutrition",
            "short": "Proteins, amino acids, pre-workout and recovery products.",
            "scope_h": "The right route <em>for each product.</em>",
            "scope": [
                ("Classification", A6["en"]),
                ("Composition review", "Active ingredients and dosages against permitted limits, and absence of prohibited substances."),
                ("Labelling and claims", "Labelling and property claims reviewed for the Uzbek market."),
                ("Filing", "Documents prepared and filed on your behalf."),
            ],
            "facts": [("15 working days", "Statutory review, as a dietary supplement"), ("2–3 months", "Overall, as a dietary supplement")],
            "facts_note": "If the product is filed as a dietary supplement: the statutory review is 15 working days, in practice up to 30 working days. Laboratory testing before filing is not counted. Overall: 2–3 months.",
            "extra_note": NEUTRAL["en"],
        },
        "ru": {
            "name": "Спортивное питание",
            "short": "Протеины, аминокислоты, предтренировочные и восстановительные продукты.",
            "scope_h": "Правильный путь <em>для каждого продукта.</em>",
            "scope": [
                ("Классификация", A6["ru"]),
                ("Проверка состава", "Активные ингредиенты и дозировки на соответствие допустимым нормам, отсутствие запрещённых веществ."),
                ("Маркировка и заявления", "Проверяем маркировку и заявления о свойствах для рынка Узбекистана."),
                ("Подача", "Готовим и подаём документы от вашего имени."),
            ],
            "facts": [("15 рабочих дней", "Нормативный срок рассмотрения для БАД"), ("2–3 месяца", "Общий срок для БАД")],
            "facts_note": "Если продукт оформляется как БАД: нормативный срок рассмотрения — 15 рабочих дней, на практике — до 30 рабочих дней. Лабораторные испытания до подачи в этот срок не входят. Общий срок — 2–3 месяца.",
            "extra_note": NEUTRAL["ru"],
        },
        "extra_todo": "B25: timelines for sports nutrition filed as specialised food for athletes (not a supplement) — not found yet",
    },
    {
        # Neutral page until the food procedure is confirmed: hero, fees and links only.
        "slug": "food-products",
        "minimal": True,
        "en": {
            "name": "Food products",
            "short": "We register food products for the Uzbek market.",
            "lead_todo": FOOD_TODO,
        },
        "ru": {
            "name": "Пищевая продукция",
            "short": "Регистрируем пищевую продукцию для рынка Узбекистана.",
            "lead_todo": FOOD_TODO,
        },
    },
    {
        "slug": "household-chemicals",
        "en": {
            "name": "Household chemicals",
            "short": "Detergents, cleaning agents and other household chemicals.",
            "scope_h": "Household chemicals, <em>cleared for sale.</em>",
            "scope": [
                ("Requirements check", "We confirm what your product needs before preparing documents."),
                ("Composition and safety data", "Formulation and safety data sheets reviewed before filing."),
                ("Labelling", "Label texts and warnings reviewed for the Uzbek market."),
                ("Filing", "Documents prepared and filed on your behalf."),
            ],
            "facts_note": NEUTRAL["en"],
        },
        "ru": {
            "name": "Бытовая химия",
            "short": "Моющие и чистящие средства и другая бытовая химия.",
            "scope_h": "Бытовая химия — <em>готова к продаже.</em>",
            "scope": [
                ("Проверка требований", "Определяем, что нужно вашему продукту, до подготовки документов."),
                ("Состав и данные о безопасности", "Проверяем рецептуру и паспорта безопасности до подачи."),
                ("Маркировка", "Проверяем тексты маркировки и предупреждения для рынка Узбекистана."),
                ("Подача", "Готовим и подаём документы от вашего имени."),
            ],
            "facts_note": NEUTRAL["ru"],
        },
        "timeline_todo": HOUSEHOLD_TODO,
    },
    {
        "slug": "dossier-gmp-bioequivalence",
        "en": {
            "name": "Dossier, GMP & bioequivalence support",
            "short": "Dossier preparation, GMP inspection support and bioequivalence regulatory support.",
            "scope_h": "The technical work, <em>done right.</em>",
            "scope": [
                ("Dossier preparation", "Registration dossiers prepared, translated and checked, and filed electronically in ICH CTD format."),
                ("GMP inspection support", "We prepare the site team for the national GMP inspection and support corrective actions (CAPA)."),
                ("Bioequivalence support", "Regulatory advice and dossier coordination for generics that need bioequivalence data. Studies are run by partner CROs."),
                ("Study design advice", "Advice on study design before submission, aligned with the regulator's expectations."),
            ],
            "facts": [("8–12 months", "National registration, in practice"), ("9–12 months", "GMP certificate, in practice")],
            "facts_note": A1["en"] + " In practice, obtaining a GMP certificate takes 9–12 months, or about a year if CAPA is required.",
        },
        "ru": {
            "name": "Досье, GMP и биоэквивалентность",
            "short": "Подготовка досье, сопровождение GMP-инспекций и исследований биоэквивалентности.",
            "scope_h": "Техническая работа — <em>без ошибок.</em>",
            "scope": [
                ("Подготовка досье", "Готовим, переводим и проверяем регистрационное досье и подаём его в электронном формате ICH CTD."),
                ("Сопровождение GMP-инспекций", "Готовим команду площадки к национальной инспекции GMP и сопровождаем корректирующие действия (CAPA)."),
                ("Поддержка биоэквивалентности", "Регуляторный консалтинг и координация досье для дженериков. Исследования проводят партнёрские CRO."),
                ("Дизайн исследований", "Консультируем по дизайну исследований до подачи с учётом требований регулятора."),
            ],
            "facts": [("8–12 месяцев", "Национальная регистрация, на практике"), ("9–12 месяцев", "Сертификат GMP, на практике")],
            "facts_note": A1["ru"] + " На практике получение сертификата GMP занимает 9–12 месяцев, при необходимости CAPA — около года.",
        },
    },
    # Therapeutic (dietary) food products: name confirmed (A7), procedure not yet.
    # TODO(Zulayho): describe the procedure before publishing, if we take on such projects.
    # Uncomment and fill in to publish; it then appears in the grid, nav, footer and sitemap.
    # {
    #     "slug": "therapeutic-food",
    #     "en": {"name": "Therapeutic (dietary) food products", "short": "Registration for the Uzbek market.", ...},
    #     "ru": {"name": "Пищевая продукция лечебного (диетического) питания", "short": "Регистрация для рынка Узбекистана.", ...},
    # },
]

# --------------------------------------------------------------------------
# SEO text per page: <title>, meta description, H1, first paragraph and FAQ.
# Keywords are worked into natural sentences — keep it that way. Titles may
# keep search words ("медизделия", "перерегистрация"); body text uses the
# legal terms.
# FAQ items are (question, answer) or (question, answer, note for Zulayho);
# only answers with a note get a TODO(Zulayho) comment.
# --------------------------------------------------------------------------
# B2 without the price list: the same two sentences on EN and RU pages.
FAQ_COST = {
    "en": ("How much does it cost?",
           "Fees depend on the product and pathway — request a quote. State fees are paid separately and are set by the Ministry of Health."),
    "ru": ("Сколько это стоит?",
           "Стоимость зависит от продукта и процедуры — запросите расчёт. Государственные сборы оплачиваются отдельно, их размер утверждает Министерство здравоохранения."),
}
A3_TODO = "A3: the GMP-certificate sentence is not published — confirm the official name of the GMP centre (ПКМ 738, п. 25) before adding it"

SEO = {
    "home": {
        "en": {
            "title": "Regulatory Consultant in Uzbekistan — Product Registration | NSRP",
            "desc": "NSRP is a regulatory affairs consultancy in Tashkent: product registration in Uzbekistan for medicines, medical devices, cosmetics, supplements, food and household chemicals.",
            "h1": "Predictable registration — from dossier submission to approval.",
            "lead": "Regulatory consultant in Uzbekistan for product registration — medicines, devices, cosmetics and more.",
            "faq": [
                ("Can NSRP act on our behalf?",
                 "NSRP files documents under a power of attorney at every stage of registration. For medicines, the manufacturer or marketing authorisation holder remains the applicant and NSRP files on its behalf. Permits for dietary supplements and cosmetics are usually issued in the client's name using the client's e-signature. If the client has no e-signature, NSRP can file instead — NSRP is then named as the applicant in the permit documents."),
                ("Is registration done through the Ministry of Health?",
                 "Medicines and medical devices are registered by the State Institution \"Pharmaceutical Products Safety Center\" under the Ministry of Health. Permits for dietary supplements, cosmetics and household chemicals are issued by the Committee for Sanitary and Epidemiological Welfare and Public Health under the Ministry of Health.",
                 A3_TODO),
                ("How long does product registration in Uzbekistan take?",
                 "Medicines: the statutory period is 210 days under the national procedure (8–12 months in practice) and 60 days under recognition (about 5–6 months in practice). Dietary supplements: the statutory review is 15 working days; in practice allow 2–3 months, including laboratory testing before filing."),
                FAQ_COST["en"],
            ],
        },
        "ru": {
            "title": "Регуляторный консультант в Узбекистане — регистрация продукции | NSRP",
            "desc": "NSRP — регуляторный консультант в Ташкенте: регистрация продукции в Узбекистане — лекарства, медицинские изделия, косметика, БАД, пищевая продукция и бытовая химия.",
            "h1": "Предсказуемая регистрация — от подачи досье до разрешительного документа.",
            "lead": "Регуляторный консультант в Узбекистане: регистрация лекарств, медицинских изделий, косметики, БАД и другой продукции.",
            "faq": [
                ("Может ли NSRP действовать от нашего имени?",
                 "NSRP подаёт документы по доверенности на всех этапах регистрации. По лекарственным средствам заявителем остаётся производитель или держатель регистрационного удостоверения — NSRP подаёт документы от его имени. Разрешения на БАД и косметику, как правило, оформляются на имя клиента с его электронной подписью. Если у клиента нет ЭЦП, подача возможна через NSRP — тогда заявителем в разрешительных документах указывается NSRP."),
                ("Регистрация проходит через Министерство здравоохранения?",
                 "Лекарственные средства и медицинские изделия регистрирует ГУ «Центр безопасности фармацевтической продукции» при Министерстве здравоохранения. Разрешения на БАД, косметику и бытовую химию выдаёт Комитет санитарно-эпидемиологического благополучия и общественного здоровья при Министерстве здравоохранения.",
                 A3_TODO),
                ("Сколько длится регистрация продукции в Узбекистане?",
                 "Лекарственные средства: по национальной процедуре нормативный срок — 210 дней, на практике 8–12 месяцев; по процедуре признания — 60 дней, на практике около 5–6 месяцев. БАД: нормативный срок рассмотрения — 15 рабочих дней, на практике 2–3 месяца с учётом лабораторных испытаний до подачи."),
                FAQ_COST["ru"],
            ],
        },
    },
    "drug-registration": {
        "en": {
            "title": "Drug Registration in Uzbekistan — Marketing Authorization | NSRP",
            "desc": "How to register a drug in Uzbekistan: a 210-day statutory period under the national procedure (8–12 months in practice) or 60 days under recognition. Senior-led, Tashkent.",
            "h1": "Drug registration in Uzbekistan",
            "lead": "Pharmaceutical registration from pathway assessment to the registration certificate. We manage every stage of medicine registration on behalf of the manufacturer or marketing authorisation holder.",
            "faq": [
                ("How do I register a drug in Uzbekistan?",
                 "Medicines and medical devices are registered by the State Institution \"Pharmaceutical Products Safety Center\" under the Ministry of Health. The five stages and their statutory periods are set out above."),
                ("How long does marketing authorization in Uzbekistan take?", A1["en"]),
                ("Which products qualify for the recognition procedure?",
                 "The recognition procedure covers medicines approved by WHO Listed Authorities or by regulators at Maturity Level 4 under the WHO Global Benchmarking Tool. WHO-prequalified medicines follow the same timeline. The statutory period is 60 days, with no laboratory testing or clinical studies."),
                ("Can I import medicines to Uzbekistan before registration?",
                 "Medicines must be registered before commercial import and sale. Without registration, medicines may be imported for research, preclinical and clinical studies, and for display at exhibitions. At the Ministry of Health's request, orphan drugs and medicines for highly dangerous or epidemic infections may be imported without registration; humanitarian aid requires a positive Ministry of Health conclusion."),
            ],
        },
        "ru": {
            "title": "Регистрация лекарственных средств в Узбекистане | NSRP",
            "desc": "Государственная регистрация лекарств в Узбекистане: нормативный срок 210 дней по национальной процедуре (на практике 8–12 месяцев) или 60 дней по процедуре признания. Ташкент.",
            "h1": "Регистрация лекарственных средств в Узбекистане",
            "lead": "Государственная регистрация лекарств — от выбора регистрационного пути до регистрационного удостоверения. Мы ведём все этапы регистрации препаратов от имени производителя или держателя регистрационного удостоверения.",
            "faq": [
                ("Как проходит государственная регистрация лекарств?",
                 "Лекарственные средства и медицинские изделия регистрирует ГУ «Центр безопасности фармацевтической продукции» при Министерстве здравоохранения. Пять этапов и их нормативные сроки приведены выше."),
                ("Сколько длится регистрация препаратов?", A1["ru"]),
                ("Каким препаратам доступна процедура признания?",
                 "По процедуре признания регистрируются препараты, одобренные регуляторными органами из перечня ВОЗ (WHO Listed Authorities) или органами 4-го уровня зрелости по Глобальному инструменту оценки ВОЗ. Препараты с преквалификацией ВОЗ регистрируются в те же сроки. Нормативный срок — 60 дней; лабораторные испытания и клинические исследования не проводятся."),
                ("Можно ли ввозить лекарства в Узбекистан до регистрации?",
                 "Для коммерческого ввоза и продажи лекарственное средство должно быть зарегистрировано. Без регистрации допускается ввоз для научных, доклинических и клинических исследований и для демонстрации на выставках. По запросу Минздрава без регистрации можно ввезти орфанные препараты и препараты против особо опасных и эпидемиологически опасных инфекций, а гуманитарную помощь — при положительном заключении Минздрава."),
            ],
        },
    },
    "renewal-variations": {
        "en": {
            "title": "Re-registration & Variations in Uzbekistan | NSRP",
            "desc": "Registration renewal in Uzbekistan: extension of certificate validity, variations to the registration dossier and labelling changes for registered products.",
            "h1": "Renewal and variations in Uzbekistan",
            "lead": "Extension of certificate validity, variations and labelling changes across the life of a registered product — a standing engagement, not ad hoc requests.",
            "faq": [
                ("When should I apply for an extension?", RENEWAL_WHEN["en"], RENEWAL_TODO),
                ("Which changes need a variation?",
                 "Any change to the registration dossier — manufacturer, production site, composition, specifications, packaging and so on — is filed as a variation. If a production site is reorganised or renamed without changing its address or technology, the certificate is reissued: apply within one month; reissue takes 5 working days and carries no fee."),
                ("Does a labelling change in Uzbekistan need approval?",
                 "Changes to the instructions for medical use or packaging texts are filed as variations to the registration dossier."),
                ("How long is a registration valid?", A2["en"]),
            ],
        },
        "ru": {
            "title": "Перерегистрация лекарственных средств и внесение изменений | NSRP",
            "desc": "Перерегистрация лекарственных средств в Узбекистане: продление срока действия удостоверения, внесение изменений в регистрационное досье и изменение маркировки.",
            "h1": "Продление удостоверения и внесение изменений",
            "lead": "Продление срока действия удостоверения, внесение изменений в регистрационное досье и изменение маркировки — на протяжении всего жизненного цикла препарата.",
            "faq": [
                ("Когда подавать на продление?", RENEWAL_WHEN["ru"], RENEWAL_TODO),
                ("Какие изменения оформляются как изменения в досье?",
                 "Изменение любых сведений регистрационного досье — производителя, производственной площадки, состава, спецификаций, упаковки и других — оформляется заявлением о внесении изменений. При реорганизации или смене наименования производственной площадки без изменения адреса и технологии удостоверение переоформляется: заявление подаётся в течение месяца, срок — 5 рабочих дней, без сбора."),
                ("Нужно ли согласовывать изменение маркировки?",
                 "Изменения инструкции по медицинскому применению и текстов упаковки оформляются как изменения в регистрационное досье."),
                ("Сколько действует регистрационное удостоверение?", A2["ru"]),
            ],
        },
    },
    "medical-devices": {
        "en": {
            "title": "Medical Device Registration in Uzbekistan | NSRP",
            "desc": "Medical device and medical equipment registration in Uzbekistan: risk classes, technical file, ISO 13485, statutory periods and import.",
            "h1": "Medical device registration in Uzbekistan",
            "lead": "Medical device and medical equipment registration under Uzbekistan's regulatory framework — from classification to the registration certificate.",
            "faq": [
                ("How are medical devices classified in Uzbekistan?",
                 "Medical devices are registered in four risk classes: I, IIa, IIb and III."),
                ("Do I need an ISO 13485 certificate?",
                 "Manufacturers must evidence a quality management system. A copy of a valid ISO 13485 certificate is included in the dossier, and national-procedure registration involves an inspection against Uzbekistan's national standard harmonised with ISO 13485. An international certificate does not replace this inspection. Exceptions: recognition, WHO-prequalified in vitro diagnostics, and devices whose manufacturer already holds a valid national certificate."),
                ("Can I import medical devices to Uzbekistan before registration?",
                 "Medical devices must be registered before commercial import and sale. Custom-made devices and in vitro diagnostic kit reagents that cannot be used on their own do not require registration. On the Ministry of Health's instruction, devices for orphan diseases and highly dangerous infections may be imported without registration; humanitarian aid requires a positive Ministry of Health conclusion."),
                ("How long does medical device registration take?",
                 "Registration certificates are valid for 5 years. Statutory periods in working days: recognition (FDA, CE bodies, EMA, PMDA, MFDS, MHRA) — 15; Class I — 60; Class IIa — 90; Classes IIb and III — 120; WHO-prequalified devices — 60. These exclude time to address deficiencies, clinical studies and manufacturing inspection."),
            ],
        },
        "ru": {
            "title": "Регистрация медизделий в Узбекистане | NSRP",
            "desc": "Регистрация медизделий и медицинского оборудования в Узбекистане: классы риска, техническое досье, ISO 13485, нормативные сроки и ввоз.",
            "h1": "Регистрация медицинских изделий в Узбекистане",
            "lead": "Регистрация медицинских изделий и медицинского оборудования по законодательству Республики Узбекистан — от классификации до регистрационного удостоверения.",
            "faq": [
                ("Как классифицируются медицинские изделия?",
                 "Медицинские изделия регистрируются по четырём классам риска: I, IIa, IIb и III."),
                ("Нужен ли сертификат ISO 13485?",
                 "Производитель обязан подтвердить систему менеджмента качества. В досье подаётся копия действующего сертификата ISO 13485, а при регистрации по национальной процедуре проводится инспекция на соответствие национальному стандарту Узбекистана, гармонизированному с ISO 13485. Международный сертификат инспекцию не заменяет. Исключения — регистрация по признанию, изделия для диагностики in vitro с преквалификацией ВОЗ и изделия, у производителя которых уже есть действующий национальный сертификат."),
                ("Можно ли ввозить медицинские изделия до регистрации?",
                 "Для коммерческого ввоза и продажи медицинское изделие должно быть зарегистрировано. Не требуют регистрации изделия, изготовленные на заказ, и реагенты из наборов для диагностики in vitro, которые не используются самостоятельно. По поручению Минздрава без регистрации можно ввезти изделия для орфанных заболеваний и особо опасных инфекций, а гуманитарную помощь — при положительном заключении Минздрава."),
                ("Сколько длится регистрация медицинских изделий?",
                 "Регистрационное удостоверение действует 5 лет. Нормативные сроки в рабочих днях: по признанию (FDA, органы CE, EMA, PMDA, MFDS, MHRA) — 15; класс I — 60; класс IIa — 90; классы IIb и III — 120; изделия с преквалификацией ВОЗ — 60. В эти сроки не входят время на устранение замечаний, клинические исследования и инспекция производства."),
            ],
        },
    },
    "cosmetics": {
        "en": {
            "title": "Cosmetics Registration in Uzbekistan — Import Permit | NSRP",
            "desc": "Cosmetics registration in Uzbekistan: the import and production permit, composition review, labelling, laboratory assessment and the documents to import cosmetics to Uzbekistan.",
            "h1": "Cosmetics permits in Uzbekistan",
            "lead": "Import and production permits for imported and domestic cosmetics. We prepare everything needed to import cosmetics to Uzbekistan and place them on the market.",
            "faq": [
                ("Which document do cosmetics need in Uzbekistan?", A5["en"]),
                ("What documents are needed to import cosmetics to Uzbekistan?",
                 "Application; packaging or artwork with information in the state language; specification with composition, intended use and limits; safety certificate or registration certificate from the country of manufacture; toxicological and hygienic assessment report from an accredited laboratory. Local manufacturing additionally requires international or national standards, plus a process instruction and formulation approved by the Chief State Sanitary Doctor."),
                ("Do labels need to be in Uzbek?",
                 "Labelling must include information in the state (Uzbek) language."),
                ("How long does it take?",
                 "The statutory review is 15 working days; in practice up to 1 month. A toxicological and hygienic assessment at an accredited laboratory is done before filing (2–4 weeks depending on composition) and is not counted in the review. Overall: 1–3 months."),
            ],
        },
        "ru": {
            "title": "Регистрация косметики в Узбекистане — разрешение на ввоз | NSRP",
            "desc": "Регистрация косметики в Узбекистане: разрешение на ввоз и производство, проверка состава, маркировка, лабораторная оценка и документы для ввоза.",
            "h1": "Разрешение на косметику в Узбекистане",
            "lead": "Разрешения на ввоз и производство косметики — для импортной и отечественной продукции. Готовим всё необходимое для ввоза и продажи в Узбекистане.",
            "faq": [
                ("Какой документ нужен для косметики?", A5["ru"]),
                ("Какие документы нужны для ввоза косметики?",
                 "Заявление; упаковка или её макет со сведениями на государственном языке; спецификация с составом, областью применения и нормами; сертификат безопасности или свидетельство о регистрации в стране производителя; токсиколого-гигиеническое заключение аккредитованной лаборатории. Для производства в Узбекистане дополнительно нужны международные или национальные стандарты, а также технологическая инструкция и рецептура, согласованные с Главным государственным санитарным врачом."),
                ("Должна ли маркировка быть на узбекском языке?",
                 "Маркировка должна содержать сведения на государственном (узбекском) языке."),
                ("Сколько времени это занимает?",
                 "Нормативный срок рассмотрения — 15 рабочих дней, на практике — до 1 месяца. До подачи проводится токсиколого-гигиеническая оценка в аккредитованной лаборатории (2–4 недели в зависимости от состава), в срок рассмотрения она не входит. Общий срок — 1–3 месяца."),
            ],
        },
    },
    "dietary-supplements": {
        "en": {
            "title": "Dietary Supplement Registration in Uzbekistan | NSRP",
            "desc": "Supplement registration in Uzbekistan: the import permit for dietary supplements, 15 working days of statutory review, ingredient checks and labelling.",
            "h1": "Dietary supplement permits in Uzbekistan",
            "lead": "Import and production permits for dietary supplements under Uzbek sanitary legislation — from ingredient checks to the permit, for imported and domestic products.",
            "faq": [
                ("How long does it take to get a supplement permit?",
                 "The statutory review is 15 working days; in practice up to 30 working days. Laboratory testing is done before filing (about 1 month on average) and is not counted in the review. If deficiencies are raised, allow about 1 more month to address them and for re-review. Overall: 2–3 months."),
                ("What do I need to import supplements to Uzbekistan?",
                 "Importing dietary supplements requires a permit from the Committee for Sanitary and Epidemiological Welfare and Public Health. Documents: the manufacturer's power of attorney for the applicant; a safety certificate or registration certificate from the country of manufacture; packaging or artwork with information in the state language; composition and directions for use (Latin botanical names for plant ingredients); an efficacy assessment report; a chemical composition report from an accredited laboratory in Uzbekistan; a toxicological and hygienic assessment report from an accredited laboratory. The permit is usually issued in the client's name."),
                ("Is my product a supplement or a medicine?",
                 "It depends on composition, dosages, dosage form and claimed properties. Claims to treat, prevent or correct diseases are not permitted for dietary supplements."),
                FAQ_COST["en"],
            ],
        },
        "ru": {
            "title": "Регистрация БАД в Узбекистане — разрешение на ввоз | NSRP",
            "desc": "Регистрация БАД в Узбекистане: разрешение на ввоз биологически активных добавок, нормативный срок рассмотрения 15 рабочих дней, проверка состава и маркировка.",
            "h1": "Разрешение на БАД в Узбекистане",
            "lead": "Разрешения на ввоз и производство биологически активных добавок по санитарному законодательству Республики Узбекистан — для импортной и отечественной продукции.",
            "faq": [
                ("Сколько длится оформление разрешения на БАД?",
                 "Нормативный срок рассмотрения — 15 рабочих дней, на практике — до 30 рабочих дней. До подачи проводятся лабораторные испытания (в среднем около 1 месяца), в срок рассмотрения они не входят. Если есть замечания, на практике ещё около 1 месяца уходит на их устранение и повторное рассмотрение. Общий срок — 2–3 месяца."),
                ("Что нужно для ввоза БАД в Узбекистан?",
                 "Для ввоза БАД требуется разрешение Комитета санитарно-эпидемиологического благополучия и общественного здоровья. Документы: доверенность производителя на заявителя; сертификат безопасности или свидетельство о регистрации в стране производителя; упаковка или макет со сведениями на государственном языке; состав и инструкция по применению (для растительных компонентов — ботанические названия на латыни); заключение об оценке эффективности; заключение аккредитованной лаборатории в Узбекистане о химическом составе; токсиколого-гигиеническое заключение аккредитованной лаборатории. Разрешение, как правило, оформляется на имя клиента."),
                ("Мой продукт — БАД или лекарство?",
                 "Это зависит от состава, дозировок, формы выпуска и заявленных свойств. Заявления о лечении, профилактике или коррекции заболеваний для БАД не допускаются."),
                FAQ_COST["ru"],
            ],
        },
    },
    "sports-nutrition": {
        "en": {
            "title": "Sports Nutrition Registration in Uzbekistan | NSRP",
            "desc": "Sports nutrition registration in Uzbekistan, including protein supplement registration, amino acids and pre-workout products: classification, labelling and filing.",
            "h1": "Sports nutrition registration in Uzbekistan",
            "lead": "Protein supplement registration, amino acids, pre-workout and recovery products. " + A6["en"],
            "faq": [
                ("Is sports nutrition registered as a dietary supplement?", A6["en"]),
                ("How long does sports nutrition registration take?",
                 "If the product is filed as a dietary supplement: the statutory review is 15 working days, in practice up to 30 working days. Laboratory testing before filing is not counted. Overall: 2–3 months. " + NEUTRAL["en"],
                 "B25: timelines for the specialised-food route not found yet"),
                ("What do you check before submission?",
                 "Active ingredients and dosages against permitted limits, absence of prohibited substances, labelling and property claims."),
                FAQ_COST["en"],
            ],
        },
        "ru": {
            "title": "Регистрация спортивного питания в Узбекистане | NSRP",
            "desc": "Регистрация спортивного питания в Узбекистане: протеины, аминокислоты, предтренировочные комплексы — классификация, маркировка и подача.",
            "h1": "Регистрация спортивного питания в Узбекистане",
            "lead": "Протеины, аминокислоты, предтренировочные и восстановительные продукты. " + A6["ru"],
            "faq": [
                ("Спортивное питание регистрируется как БАД?", A6["ru"]),
                ("Сколько длится регистрация спортивного питания?",
                 "Если продукт оформляется как БАД: нормативный срок рассмотрения — 15 рабочих дней, на практике — до 30 рабочих дней. Лабораторные испытания до подачи в этот срок не входят. Общий срок — 2–3 месяца. " + NEUTRAL["ru"],
                 "B25: timelines for the specialised-food route not found yet"),
                ("Что вы проверяете до подачи?",
                 "Активные ингредиенты и дозировки на соответствие допустимым нормам, отсутствие запрещённых веществ, маркировку и заявления о свойствах."),
                FAQ_COST["ru"],
            ],
        },
    },
    "food-products": {
        "en": {
            "title": "Food Product Registration in Uzbekistan | NSRP",
            "desc": "Food product registration in Uzbekistan with NSRP. Requirements and timelines depend on the product — contact us for details.",
            "h1": "Food registration in Uzbekistan",
            "lead": "We register food products. Requirements and timelines depend on the product — contact us for details.",
            "faq": [],
        },
        "ru": {
            "title": "Регистрация пищевой продукции в Узбекистане | NSRP",
            "desc": "Регистрация пищевой продукции в Узбекистане с NSRP. Требования и сроки зависят от продукта — свяжитесь с нами для деталей.",
            "h1": "Регистрация пищевой продукции в Узбекистане",
            "lead": "Мы регистрируем пищевую продукцию. Требования и сроки зависят от продукта — свяжитесь с нами для деталей.",
            "faq": [],
        },
    },
    "household-chemicals": {
        "en": {
            "title": "Household Chemicals Registration in Uzbekistan | NSRP",
            "desc": "Household chemicals registration in Uzbekistan: the permit for detergents and cleaning agents, requirements check, labelling and filing.",
            "h1": "Household chemicals permits in Uzbekistan",
            "lead": A5["en"],
            "faq": [
                ("Do detergents need a permit in Uzbekistan?", A5["en"]),
                ("Which documents are needed, and how long does it take?", NEUTRAL["en"], HOUSEHOLD_TODO),
                FAQ_COST["en"],
            ],
        },
        "ru": {
            "title": "Регистрация бытовой химии в Узбекистане — разрешение | NSRP",
            "desc": "Регистрация бытовой химии в Узбекистане: разрешение на моющие и чистящие средства, проверка требований, маркировка и подача.",
            "h1": "Разрешение на бытовую химию в Узбекистане",
            "lead": A5["ru"],
            "faq": [
                ("Нужно ли разрешение на моющие средства?", A5["ru"]),
                ("Какие нужны документы и сколько это занимает?", NEUTRAL["ru"], HOUSEHOLD_TODO),
                FAQ_COST["ru"],
            ],
        },
    },
    "dossier-gmp-bioequivalence": {
        "en": {
            "title": "GMP Inspection, Dossier & Bioequivalence in Uzbekistan | NSRP",
            "desc": "GMP inspection support in Uzbekistan, registration dossier preparation in ICH CTD format and regulatory support for bioequivalence studies.",
            "h1": "GMP, dossier and bioequivalence support in Uzbekistan",
            "lead": "Registration dossier preparation, GMP inspection support in Uzbekistan and the regulatory side of bioequivalence studies — for manufacturers and their teams.",
            "faq": [
                ("When is a GMP inspection required in Uzbekistan?",
                 "A GMP inspection is carried out for every medicine registered under the national procedure; recognition and WHO prequalification are exempt. A national GMP certificate is issued after inspection and must be obtained before registration; inspection time is not counted in the statutory period. National-procedure medical devices undergo an inspection against the national ISO 13485 standard. In practice, obtaining a GMP certificate takes 9–12 months, or about a year if CAPA is required."),
                ("Do generics need bioequivalence data in Uzbekistan?",
                 "Generic applications include bioavailability and bioequivalence reports versus the reference product, except for biosimilars. A biowaiver is accepted for BCS Class I and III substances. From 1 January 2029, bioequivalence studies must follow ICH requirements."),
                ("What format does the registration dossier follow?",
                 "The dossier is filed electronically in ICH CTD format. Labelling, instructions for medical use and the summary of product characteristics are filed in Uzbek, and may additionally be filed in Russian or another language. Foreign applicants may file Modules 2–5 in English or Russian."),
            ],
        },
        "ru": {
            "title": "GMP инспекция, регистрационное досье и биоэквивалентность | NSRP",
            "desc": "GMP инспекция в Узбекистане, подготовка регистрационного досье в формате ICH CTD и регуляторная поддержка исследований биоэквивалентности.",
            "h1": "GMP инспекция, досье и биоэквивалентность",
            "lead": "Подготовка регистрационного досье, сопровождение GMP инспекций в Узбекистане и регуляторная часть исследований биоэквивалентности — для производителей и их команд.",
            "faq": [
                ("Когда требуется GMP инспекция в Узбекистане?",
                 "Инспекция GMP проводится для всех лекарственных средств, регистрируемых по национальной процедуре. Исключения — регистрация по признанию и преквалификация ВОЗ. По итогам инспекции выдаётся национальный сертификат GMP; его нужно получить до регистрации, а время инспекции в нормативный срок не входит. Для медицинских изделий по национальной процедуре проводится инспекция на соответствие национальному стандарту ISO 13485. На практике получение сертификата GMP занимает 9–12 месяцев, при необходимости CAPA — около года."),
                ("Нужны ли дженерикам данные о биоэквивалентности?",
                 "Для воспроизведённых препаратов подаются отчёты о биодоступности и биоэквивалентности в сравнении с референтным препаратом, кроме биоаналогов. Для субстанций I и III класса биофармацевтической классификационной системы допускается биовейвер. С 1 января 2029 года исследования биоэквивалентности проводятся по требованиям ICH."),
                ("В каком формате подаётся регистрационное досье?",
                 "Досье подаётся в электронном формате ICH CTD. Маркировка, инструкция по медицинскому применению и краткая характеристика препарата подаются на узбекском языке; дополнительно их можно подать на русском или другом языке. Иностранные заявители подают модули 2–5 на английском или русском языке."),
            ],
        },
    },
}

FOUNDERS = [
    {
        "photo": "assets/team/zulayho.webp",
        "email": "zulayho@nsrp.uz",
        "linkedin": "https://www.linkedin.com/in/zulayho-yuldosheva/",
        "en": {"name": "Zulayho Yuldosheva", "initials": "ZY",
               "role": "Managing Director & Head of Regulatory Affairs",
               "bio": "Leads every engagement directly — dossier strategy, authority communication and scientific review, built on years of senior practice in this market.",
               "contact": "Contact for regulatory questions"},
        "ru": {"name": "Зулайхо Юлдошева", "initials": "ЗЮ",
               "role": "Управляющий директор, руководитель регуляторного направления",
               "bio": "Лично ведёт каждый проект: стратегия по досье, взаимодействие с регуляторными органами и научная экспертиза — на основе многолетней практики на этом рынке.",
               "contact": "По регуляторным вопросам"},
    },
    {
        "photo": "assets/team/jorabek.webp",
        "email": "jorabek@nsrp.uz",
        "linkedin": "https://www.linkedin.com/in/jorabek-jumanov-25420037",
        "en": {"name": "Jorabek Jumanov", "initials": "JJ",
               "role": "Director of Operations & Business Development",
               "bio": "Leads client relations, commercial terms and delivery, with nine years of international experience across Boston, Los Angeles and San Francisco.",
               "contact": "Contact for commercial questions"},
        "ru": {"name": "Джурабек Джуманов", "initials": "ДД",
               "role": "Операционный директор, директор по развитию бизнеса",
               "bio": "Отвечает за работу с клиентами, коммерческие условия и операционную деятельность. Девять лет международного опыта в Бостоне, Лос-Анджелесе и Сан-Франциско.",
               "contact": "По коммерческим вопросам"},
    },
]

HOME = {
    "en": {
        "what_eyebrow": "What we do",
        "what_h": "We sell certainty, <em>not paperwork.</em>",
        "what_lead": "Registration in Uzbekistan follows a defined sequence. The procedure is not complicated — executing it precisely, and explaining it clearly, every time, is.",
        "pillars": [
            ("Predictable timelines", "Milestones agreed at the outset, with written reporting against them."),
            ("Senior-led", "Every engagement is led personally by our Head of Regulatory Affairs."),
            ("Three working languages", "Russian, English and Uzbek — nothing lost between Tashkent and head office."),
            ("Pathway first", "Before any submission, we check simplified recognition and expedited routes."),
        ],
        "what_link": "See how it works",
        "services_eyebrow": "Services",
        "services_h": "Every product category, <em>one partner.</em>",
        "services_lead": "Choose a service to see what we handle and what to expect.",
        "how_eyebrow": "How it works",
        "how_h": "From first request <em>to approval.</em>",
        "steps": [
            ("Tell us about your product", "Send the product, its current approvals and your target dates by WhatsApp or email."),
            ("Pathway and quote", "We confirm the route, the documents needed, a timeline and the fee — in writing."),
            ("Dossier preparation", "We collect, translate and check every document against current requirements."),
            ("Submission and expert review", "We submit, coordinate samples and testing, and answer the authority on your behalf."),
            ("Approval", "You receive the registration certificate or permit with a complete record. We stay on for renewals and changes."),
        ],
        "founders_eyebrow": "Founders",
        "founders_h": "Senior expertise, <em>personally engaged.</em>",
        "contact_eyebrow": "Contact",
        "contact_h": "Every engagement begins with <em>a frank conversation.</em>",
        "rows": [("Regulatory questions", "zulayho@nsrp.uz"), ("Commercial questions", "jorabek@nsrp.uz"), ("General enquiries", "info@nsrp.uz")],
        "office": "Office",
    },
    "ru": {
        "what_eyebrow": "Чем мы занимаемся",
        "what_h": "Мы предлагаем определённость, <em>а не бумажную работу.</em>",
        "what_lead": "Регистрация в Узбекистане проходит чётко определённые этапы. Сама процедура несложна — сложно каждый раз выполнять её точно и ясно объяснять клиенту.",
        "pillars": [
            ("Прогнозируемые сроки", "Контрольные точки согласуем в начале проекта и отчитываемся по ним письменно."),
            ("Опытные специалисты", "Каждый проект лично ведёт руководитель регуляторного направления."),
            ("Три рабочих языка", "Русский, английский и узбекский — ничего не теряется между Ташкентом и головным офисом."),
            ("Сначала — выбор пути", "До подачи досье проверяем возможность упрощённых и ускоренных процедур."),
        ],
        "what_link": "Как мы работаем",
        "services_eyebrow": "Услуги",
        "services_h": "Любая категория продукции — <em>один партнёр.</em>",
        "services_lead": "Выберите услугу, чтобы узнать, что мы делаем и чего ожидать.",
        "how_eyebrow": "Как мы работаем",
        "how_h": "От первого запроса <em>до разрешительного документа.</em>",
        "steps": [
            ("Расскажите о продукте", "Пришлите описание продукта, имеющиеся регистрации и желаемые сроки в WhatsApp или на почту."),
            ("Путь и стоимость", "Подтверждаем регистрационный путь, перечень документов, сроки и стоимость — письменно."),
            ("Подготовка досье", "Собираем, переводим и проверяем каждый документ на соответствие актуальным требованиям."),
            ("Подача и экспертиза", "Подаём досье, координируем образцы и испытания, отвечаем на запросы регулятора."),
            ("Разрешительный документ", "Передаём регистрационное удостоверение или разрешение с полным комплектом документов и сопровождаем дальнейшие изменения."),
        ],
        "founders_eyebrow": "Основатели",
        "founders_h": "Опыт и экспертиза — <em>с личным участием.</em>",
        "contact_eyebrow": "Контакты",
        "contact_h": "Каждый проект начинается <em>с откровенного разговора.</em>",
        "rows": [("Регуляторные вопросы", "zulayho@nsrp.uz"), ("Коммерческие вопросы", "jorabek@nsrp.uz"), ("Общие вопросы", "info@nsrp.uz")],
        "office": "Офис",
    },
}

SERVICE_PAGE = {
    "en": {"scope_eyebrow": "What we handle", "timeline_eyebrow": "Timeline",
           "stages_h": "Five stages, <em>each with a statutory period.</em>",
           "stages_cols": ("Stage", "National procedure", "Recognition, WHO PQ"),
           "stages_after": "Up to 45 days are given to address deficiencies after the primary review and up to 90 days after the specialised review; these are not counted in the statutory period. Clinical studies (if required) and GMP inspection are also outside it. The certificate is issued within 2 working days of the decision and is valid for 5 years.",
           "stages_note": "<strong>Recognition procedure.</strong> The recognition procedure covers medicines approved by WHO Listed Authorities or by regulators at Maturity Level 4 under the WHO Global Benchmarking Tool. WHO-prequalified medicines follow the same timeline. The statutory period is 60 days, with no laboratory testing or clinical studies.",
           "timeline_h": "A written timeline, <em>before we start.</em>",
           "timeline_note": "Timelines depend on the product and the documents available. We confirm yours in writing once we have reviewed your product.",
           "fees_eyebrow": "Fees"},
    "ru": {"scope_eyebrow": "Что мы делаем", "timeline_eyebrow": "Сроки",
           "stages_h": "Пять этапов — <em>у каждого свой нормативный срок.</em>",
           "stages_cols": ("Этап", "Национальная процедура", "Признание, преквалификация ВОЗ"),
           "stages_after": "На устранение замечаний даётся до 45 дней после первичной экспертизы и до 90 дней после специализированной — в нормативный срок они не входят. Отдельно от срока идут клинические исследования (если требуются) и инспекция GMP. Удостоверение направляется в течение 2 рабочих дней после решения и действует 5 лет.",
           "stages_note": "<strong>Процедура признания.</strong> По процедуре признания регистрируются препараты, одобренные регуляторными органами из перечня ВОЗ (WHO Listed Authorities) или органами 4-го уровня зрелости по Глобальному инструменту оценки ВОЗ. Препараты с преквалификацией ВОЗ регистрируются в те же сроки. Нормативный срок — 60 дней; лабораторные испытания и клинические исследования не проводятся.",
           "timeline_h": "Письменный график — <em>до начала работы.</em>",
           "timeline_note": "Сроки зависят от продукта и имеющихся документов. Мы подтверждаем их письменно после изучения вашего продукта.",
           "fees_eyebrow": "Стоимость"},
}

# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------
ICONS = {
    "chat": '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>',
    "mail": '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
    "linkedin": '<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6z"/><rect width="4" height="12" x="2" y="9"/><circle cx="4" cy="4" r="2"/>',
    "arrow": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "menu": '<path d="M4 7h16"/><path d="M4 12h16"/><path d="M4 17h16"/>',
    "close": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "chev": '<path d="m6 9 6 6 6-6"/>',
}


def icon(name, cls="icon"):
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


def esc(s):
    return html.escape(s, quote=True)


def todo(note):
    # TODO(Zulayho) notes are kept in this file for review and never written to the pages.
    return ""


def url(lang, path):
    return path if lang == "en" else "/ru" + path


def asset_version(name):
    return hashlib.md5((ROOT / "assets" / name).read_bytes()).hexdigest()[:8]


def wa_link(lang, name=None):
    if not name:
        return WHATSAPP
    return f"{WHATSAPP}?text={quote(UI[lang]['wa_quote'].format(name=name))}"


def mail_link(lang, name=None):
    if not name:
        return f"mailto:{EMAIL}"
    return f"mailto:{EMAIL}?subject={quote(UI[lang]['mail_quote'].format(name=name))}"


def contact_buttons(lang, name=None, dark=True):
    t = UI[lang]
    second = "btn-line" if dark else "btn-line-dark"
    return (f'<a class="btn btn-gold" href="{wa_link(lang, name)}" target="_blank" rel="noopener">{icon("chat")}{t["whatsapp"]}</a>'
            f'<a class="btn {second}" href="{mail_link(lang, name)}">{icon("mail")}{t["email"]}</a>')


def head(lang, path, title, desc):
    other = "ru" if lang == "en" else "en"
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
{TRACKING}
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}" />
<link rel="canonical" href="{SITE}{url(lang, path)}" />
<link rel="alternate" hreflang="en" href="{SITE}{url('en', path)}" />
<link rel="alternate" hreflang="ru" href="{SITE}{url('ru', path)}" />
<link rel="alternate" hreflang="x-default" href="{SITE}{url('en', path)}" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="Northern Star Regulatory Partners" />
<meta property="og:title" content="{esc(title)}" />
<meta property="og:description" content="{esc(desc)}" />
<meta property="og:url" content="{SITE}{url(lang, path)}" />
<meta property="og:image" content="{SITE}/assets/logo.jpg" />
<meta property="og:locale" content="{'en_US' if lang == 'en' else 'ru_RU'}" />
<meta property="og:locale:alternate" content="{'en_US' if other == 'en' else 'ru_RU'}" />
<link rel="icon" type="image/jpeg" href="/assets/logo.jpg" />
<link rel="icon" type="image/svg+xml" href="/assets/favicon-n.svg" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&amp;family=Inter:wght@400;500;600&amp;display=swap" rel="stylesheet" />
<link rel="stylesheet" href="/assets/site.css?v={asset_version('site.css')}" />
<script src="/assets/site.js?v={asset_version('site.js')}" defer></script>
</head>"""


def lang_switch(lang, path):
    if lang == "en":
        return (f'<span class="lang" aria-label="Language"><span aria-current="page">EN</span><span class="lang-sep">|</span>'
                f'<a href="{url("ru", path)}" hreflang="ru" lang="ru">RU</a></span>')
    return (f'<span class="lang" aria-label="Язык"><a href="{url("en", path)}" hreflang="en" lang="en">EN</a>'
            f'<span class="lang-sep">|</span><span aria-current="page">RU</span></span>')


def header(lang, path):
    t = UI[lang]
    home = url(lang, "/")
    submenu = "".join(f'<li><a href="{url(lang, "/services/" + s["slug"] + "/")}">{s[lang]["name"]}</a></li>' for s in SERVICES)
    mm_services = submenu
    return f"""<body>
<a class="skip" href="#main">{t['skip']}</a>
<nav class="navbar" aria-label="Main">
  <div class="wrap">
    <a class="brand" href="{home}">
      <img src="/assets/favicon-n.svg" alt="" width="36" height="36" />
      <span><span class="brand-name">NSRP</span><span class="brand-full">{t['brand_full']}</span></span>
    </a>
    <ul class="nav-links">
      <li class="has-menu"><a href="{home}#services">{t['services']}{icon('chev', 'chev')}</a>
        <ul class="submenu">{submenu}</ul>
      </li>
      <li><a href="{home}#how">{t['how']}</a></li>
      <li><a href="{home}#founders">{t['founders']}</a></li>
    </ul>
    {lang_switch(lang, path)}
    <a class="btn btn-gold btn-sm btn-contact" href="{home}#contact">{t['contact']}</a>
    <button class="menu-toggle" id="menuToggle" type="button" aria-expanded="false" aria-controls="mobileMenu">{t['menu']}{icon('menu', 'icon i-menu')}{icon('close', 'icon i-close')}</button>
  </div>
  <div class="mobile-menu" id="mobileMenu">
    <ul class="mm-main">
      <li><a href="{home}#services">{t['services']}</a></li>
      <li><a href="{home}#how">{t['how']}</a></li>
      <li><a href="{home}#founders">{t['founders']}</a></li>
      <li><a href="{home}#contact">{t['contact']}</a></li>
    </ul>
    <p class="eyebrow mm-label">{t['all_services']}</p>
    <ul class="mm-services">{mm_services}</ul>
    <div class="mm-actions">{contact_buttons(lang, dark=False)}</div>
  </div>
</nav>
<main id="main">"""


def footer(lang):
    t = UI[lang]
    home = url(lang, "/")
    services = "".join(f'<li><a href="{url(lang, "/services/" + s["slug"] + "/")}">{s[lang]["name"]}</a></li>' for s in SERVICES)
    return f"""</main>
<footer class="footer">
  <div class="wrap">
    <div class="footer-grid">
      <div class="footer-brandcol">
        <a class="brand" href="{home}">
          <img src="/assets/favicon-n.svg" alt="" width="36" height="36" />
          <span><span class="brand-name">NSRP</span><span class="brand-full">{t['brand_full']}</span></span>
        </a>
        <p class="footer-tag">{t['tagline']}</p>
      </div>
      <div>
        <h2>{t['services']}</h2>
        <ul>{services}</ul>
      </div>
      <div>
        <h2>{t['company']}</h2>
        <ul>
          <li><a href="{home}#how">{t['how']}</a></li>
          <li><a href="{home}#founders">{t['founders']}</a></li>
              <li><a href="{home}#contact">{t['contact']}</a></li>
        </ul>
      </div>
      <div>
        <h2>{t['contacts']}</h2>
        <ul class="footer-contact">
          <li><a class="footer-wa" href="{WHATSAPP}" target="_blank" rel="noopener">{icon('chat')}<span><span class="footer-label">WhatsApp</span><span class="tel">{WHATSAPP_DISPLAY}</span></span></a></li>
          <li><a href="mailto:{EMAIL}">{icon('mail')}{EMAIL}</a></li>
          <li><a href="{LINKEDIN_COMPANY}" target="_blank" rel="noopener">{icon('linkedin')}LinkedIn</a></li>
          <li>{t['location']}</li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>&copy; 2026 Northern Star Regulatory Partners</span>
      <span>{t['ga']}</span>
    </div>
  </div>
</footer>
<div class="mobile-cta">{contact_buttons(lang, dark=False).replace('btn ', 'btn btn-sm ')}</div>
</body>
</html>
"""


def reveal(i=0):
    return f'class="reveal" style="--d:{i}"' if i else 'class="reveal"'


def service_card(lang, s, n, animated=True):
    t = UI[lang]
    d = s[lang]
    attrs = f' style="--d:{n % 3}"' if animated else ""
    cls = "card reveal" if animated else "card"
    return (f'<a class="{cls}"{attrs} href="{url(lang, "/services/" + s["slug"] + "/")}">'
            f'<span class="card-num">{n:02d}</span><h3>{d["name"]}</h3><p>{d["short"]}</p>'
            f'<span class="card-more">{t["learn"]}{icon("arrow")}</span></a>')


def founder_card(lang, f, i):
    d = f[lang]
    photo = (f'<img src="/{f["photo"]}" width="140" height="140" alt="{esc(d["name"])}" loading="lazy" />' if (ROOT / f["photo"]).exists()
             else f'<span class="founder-initials" aria-hidden="true">{d["initials"]}</span>'
                  )
    linkedin = (f'<a href="{f["linkedin"]}" target="_blank" rel="noopener">{icon("linkedin")}LinkedIn</a>' if f["linkedin"]
                else "")
    return f"""<article class="founder reveal" style="--d:{i}">
        <div class="founder-photo">{photo}</div>
        <div>
          <h3>{d['name']}</h3>
          <p class="founder-role">{d['role']}</p>
          <p class="founder-bio">{d['bio']}</p>
          <div class="founder-contact">
            <p class="eyebrow">{d['contact']}</p>
            <div class="founder-links"><a href="mailto:{f['email']}">{icon('mail')}{f['email']}</a>{linkedin}</div>
          </div>
        </div>
      </article>"""


def faq_section(lang, items, bg):
    t = UI[lang]
    entries = "".join(
        f'<details class="reveal"><summary>{item[0]}</summary><p>{item[1]}</p>'
        f'{todo(item[2]) if len(item) > 2 else ""}</details>'
        for item in items)
    if not items:
        return ""
    return f"""<section class="section {bg}" id="faq">
  <div class="wrap">
    <p class="eyebrow reveal">{t['faq_eyebrow']}</p>
    <h2 class="h2 reveal">{t['faq_h']}</h2>
    <div class="faq">{entries}</div>
  </div>
</section>
"""


def hero_picture(lang):
    alt = "Tashkent skyline" if lang == "en" else "Панорама Ташкента"
    # Phones get their own crop (skyline, mosque and trees) shown uncropped;
    # wider screens get the tall sky-to-skyline band, anchored centre bottom.
    return ('<picture>'
            '<source media="(max-width: 960px)" type="image/webp" sizes="100vw" width="1200" height="794" '
            'srcset="/assets/hero-m-800.webp 800w, /assets/hero-m-1200.webp 1200w" />'
            '<source type="image/webp" sizes="100vw" '
            'srcset="/assets/hero-1200.webp 1200w, /assets/hero-1800.webp 1800w, /assets/hero-2268.webp 2268w" />'
            '<img class="home-hero-photo" src="/assets/hero-1800.jpg" '
            f'width="1800" height="1857" alt="{alt}" fetchpriority="high" />'
            '</picture>')


def render_home(lang):
    t, h, seo = UI[lang], HOME[lang], SEO["home"][lang]
    pillars = "".join(f'<div class="pillar reveal" style="--d:{i}"><h3>{a}</h3><p>{b}</p></div>' for i, (a, b) in enumerate(h["pillars"]))
    cards = "".join(service_card(lang, s, i + 1) for i, s in enumerate(SERVICES))
    steps = "".join(f'<li class="step reveal" style="--d:{i}"><span class="step-num">{i + 1}</span><div><h3>{a}</h3><p>{b}</p></div></li>'
                    for i, (a, b) in enumerate(h["steps"]))
    founders = "".join(founder_card(lang, f, i) for i, f in enumerate(FOUNDERS))
    rows = "".join(f'<div><dt>{a}</dt><dd><a href="mailto:{b}">{b}</a></dd></div>' for a, b in h["rows"])
    rows += f'<div><dt>WhatsApp</dt><dd><a href="{WHATSAPP}" target="_blank" rel="noopener"><span class="tel">{WHATSAPP_DISPLAY}</span></a></dd></div>'
    rows += f'<div><dt>{h["office"]}</dt><dd>{t["location"]}</dd></div>'
    home = url(lang, "/")

    body = f"""
<section class="home-hero {'has-photo' if HAS_HERO_PHOTO else 'no-photo'}">
  {hero_picture(lang) if HAS_HERO_PHOTO else '<!-- Gradient fallback until the hero images are added -->'}
  <div class="wrap">
    <div class="hero-card">
      <h1>{seo['h1']}</h1>
      <p>{seo['lead']}</p>
      <a class="btn btn-gold" href="{home}#contact">{t['contact']}</a>
    </div>
  </div>
  {'<div class="hero-skyline" aria-hidden="true"></div>' if HAS_HERO_PHOTO else ''}
</section>

<section class="section bg-cream" id="about">
  <div class="wrap">
    <p class="eyebrow reveal">{h['what_eyebrow']}</p>
    <h2 class="h2 reveal" style="--d:1">{h['what_h']}</h2>
    <p class="lead reveal" style="--d:2">{h['what_lead']}</p>
    <div class="pillars">{pillars}</div>
    <p class="section-foot reveal"><a class="text-link" href="{home}#how">{h['what_link']}{icon('arrow')}</a></p>
  </div>
</section>

<section class="section bg-white" id="services">
  <div class="wrap">
    <p class="eyebrow reveal">{h['services_eyebrow']}</p>
    <h2 class="h2 reveal" style="--d:1">{h['services_h']}</h2>
    <p class="lead reveal" style="--d:2">{h['services_lead']}</p>
    <div class="cards">{cards}</div>
  </div>
</section>

<section class="section bg-deep" id="how">
  <div class="wrap">
    <p class="eyebrow reveal">{h['how_eyebrow']}</p>
    <h2 class="h2 reveal" style="--d:1">{h['how_h']}</h2>
    <ol class="steps">{steps}</ol>
    <div class="actions reveal"><a class="btn btn-gold" href="{home}#contact">{t['contact']}</a></div>
  </div>
</section>

<section class="section bg-cream" id="founders">
  <div class="wrap">
    <p class="eyebrow reveal">{h['founders_eyebrow']}</p>
    <h2 class="h2 reveal" style="--d:1">{h['founders_h']}</h2>
    <div class="founders">{founders}</div>
  </div>
</section>


<section class="section bg-deep" id="contact">
  <div class="wrap contact-grid">
    <div>
      <p class="eyebrow reveal">{h['contact_eyebrow']}</p>
      <h2 class="h2 reveal" style="--d:1">{h['contact_h']}</h2>
      <p class="lead reveal" style="--d:2">{t['fees']} {t['state_fees']} {t['reply']}</p>
      <div class="actions reveal" style="--d:3">{contact_buttons(lang)}</div>
    </div>
    <dl class="contact-rows reveal" style="--d:2">{rows}</dl>
  </div>
</section>

{faq_section(lang, seo['faq'], 'bg-cream')}"""
    return head(lang, "/", seo["title"], seo["desc"]) + header(lang, "/") + body + footer(lang)


def render_service(lang, s):
    t, p, d, seo = UI[lang], SERVICE_PAGE[lang], s[lang], SEO[s["slug"]][lang]
    path = f"/services/{s['slug']}/"
    home = url(lang, "/")

    scope = "".join(f'<div class="pillar reveal" style="--d:{i % 2}"><h3>{item[0]}</h3><p>{item[1]}</p>'
                    f'{todo(item[2]) if len(item) > 2 else ""}</div>' for i, item in enumerate(d.get("scope", [])))

    facts = "".join(f'<div class="reveal"><div class="fact-v">{v}</div><div class="fact-l">{l}</div></div>' for v, l in d.get("facts", []))
    facts = f'<div class="timeline-facts">{facts}</div>{todo(d.get("facts_todo"))}' if facts else ""
    if s.get("stages"):
        cols = p["stages_cols"]
        off = 1 if lang == "en" else 4
        rows = "".join(
            f'<tr><th scope="row"><span class="stage-n">{st[0]}</span>{st[off]}</th>'
            f'<td data-label="{cols[1]}">{st[off + 1]}</td><td data-label="{cols[2]}">{st[off + 2]}</td></tr>'
            for st in PHARMA_STAGES)
        total = PHARMA_TOTAL[lang]
        timeline = f"""<h2 class="h2 reveal" style="--d:1">{p['stages_h']}</h2>
    {facts}
    <p class="facts-note reveal">{d['facts_note']}</p>
    <table class="stages reveal">
      <thead><tr><th scope="col">{cols[0]}</th><th scope="col">{cols[1]}</th><th scope="col">{cols[2]}</th></tr></thead>
      <tbody>{rows}</tbody>
      <tfoot><tr><th scope="row">{total[0]}</th><td data-label="{cols[1]}">{total[1]}</td><td data-label="{cols[2]}">{total[2]}</td></tr></tfoot>
    </table>
    <p class="stages-note reveal">{p['stages_after']}</p>
    {todo(s.get('stages_todo'))}
    <p class="note reveal">{p['stages_note']}</p>"""
    else:
        extra = f'<p class="note reveal">{d["extra_note"]}</p>{todo(s.get("extra_todo"))}' if d.get("extra_note") else ""
        timeline = f"""<h2 class="h2 reveal" style="--d:1">{p['timeline_h']}</h2>
    {facts}
    <p class="note reveal">{d.get('facts_note') or p['timeline_note']}</p>
    {extra}
    {todo(s.get('timeline_todo'))}"""
    details = "" if s.get("minimal") else f"""
<section class="section bg-cream">
  <div class="wrap">
    <p class="eyebrow reveal">{p['scope_eyebrow']}</p>
    <h2 class="h2 reveal" style="--d:1">{d['scope_h']}</h2>
    <div class="pillars two">{scope}</div>
  </div>
</section>

<section class="section bg-white">
  <div class="wrap">
    <p class="eyebrow reveal">{p['timeline_eyebrow']}</p>
    {timeline}
  </div>
</section>
"""

    others = "".join(f'<li><a href="{url(lang, "/services/" + o["slug"] + "/")}">{o[lang]["name"]}</a></li>'
                     for o in SERVICES if o is not s)

    body = f"""
<section class="hero page-hero bg-deep">
  <div class="wrap">
    <div>
      <p class="eyebrow reveal"><a href="{home}#services">{t['services']}</a></p>
      <h1 class="display reveal" style="--d:1">{seo['h1']}</h1>
      <p class="lead reveal" style="--d:2">{seo['lead']}</p>
      {todo(d.get('lead_todo'))}
      <div class="actions reveal" style="--d:3">{contact_buttons(lang, d['name'])}</div>
    </div>
  </div>
</section>
{details}
<section class="section bg-navy" id="quote">
  <div class="wrap">
    <p class="eyebrow reveal">{p['fees_eyebrow']}</p>
    <h2 class="h2 reveal" style="--d:1">{t['fees']}</h2>
    <p class="lead reveal" style="--d:2">{t['state_fees']} {t['reply']}</p>
    <div class="actions reveal" style="--d:3">{contact_buttons(lang, d['name'])}</div>
  </div>
</section>

<section class="section bg-cream">
  <div class="wrap">
    <p class="eyebrow reveal">{t['other_services']}</p>
    <h2 class="h2 reveal" style="--d:1">{t['other_h']}</h2>
    <ul class="chips reveal" style="--d:2">{others}</ul>
  </div>
</section>

{faq_section(lang, seo['faq'], 'bg-white')}"""
    return head(lang, path, seo["title"], seo["desc"]) + header(lang, path) + body + footer(lang)


def write(lang, path, content):
    if "TODO" in content:
        raise SystemExit(f"TODO left in the HTML for {url(lang, path)} — notes belong in _src/build.py only")
    out = ROOT / url(lang, path).strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8", newline="\n")
    return url(lang, path)


def sitemap(paths):
    entries = []
    for path in paths:
        alts = "".join(f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{SITE}{url(l, path)}"/>' for l in ("en", "ru"))
        alts += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{url("en", path)}"/>'
        for lang in ("en", "ru"):
            entries.append(f"  <url>\n    <loc>{SITE}{url(lang, path)}</loc>{alts}\n  </url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + "\n".join(entries) + "\n</urlset>\n")


def main():
    if (ROOT / ".nojekyll").exists():
        raise SystemExit(".nojekyll found: GitHub Pages would then publish _src/ (build.py and the TODO notes). Remove it.")
    paths = ["/"] + [f"/services/{s['slug']}/" for s in SERVICES]
    written = []
    for lang in ("en", "ru"):
        written.append(write(lang, "/", render_home(lang)))
        for s in SERVICES:
            written.append(write(lang, f"/services/{s['slug']}/", render_service(lang, s)))
    (ROOT / "sitemap.xml").write_text(sitemap(paths), encoding="utf-8", newline="\n")
    print(f"Built {len(written)} pages + sitemap.xml")
    for f in FOUNDERS:
        if not (ROOT / f["photo"]).exists():
            print(f"  missing photo: {f['photo']} (showing initials)")


if __name__ == "__main__":
    main()
