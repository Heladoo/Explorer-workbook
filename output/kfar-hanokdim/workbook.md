# Noa and Amit's Kfar Hanokdim Adventure Book

*An activity book for young explorers*

| Field | Value |
| --- | --- |
| Destination | Kfar Hanokdim |
| Language | en |
| Pages | 12 |
| Made for | Noa (5), Amit (7) |
| Trip | — |
| Special interests | — |
| Knowledge source | file |
| Generated | 2026-08-16T05:39:56+00:00 |


## How to use this document

This is the build specification for the workbook. Each page below lists what the
child does, why it is there, and the exact prompt for the illustration it needs.
The prompts are also written out one per file under `prompts/`, ready to paste
into an image model. Machine-readable form: `workbook.json`.

Image prompts are written in English regardless of the workbook language, since
that is what image models are trained on. All copy the child reads is in the
workbook language.

## Page overview

| # | Activity | Difficulty | Est. age | Educational goal | Prompt file |
| --- | --- | --- | --- | --- | --- |
| 1 | cover | easy | 4-6 | Builds anticipation for the trip and gives the child ownership of the book. | [`01_cover.md`](prompts/01_cover.md) |
| 2 | coloring | easy | 4-6 | Develops fine motor control and color choice while introducing a real place the child will visit. | [`02_coloring.md`](prompts/02_coloring.md) |
| 3 | maze | easy | 4-6 | Practises visual planning, sequencing and pencil control, and links the trip to one real place the family will actually see. | — |
| 4 | word_search | easy | 6-6 | Builds letter recognition, spelling and systematic visual scanning, using vocabulary from the place the child is visiting. | — |
| 5 | scavenger_hunt | medium | 5-7 | Turns travelling itself into an active search: builds observation skills and vocabulary by sending the child looking for the real thing, not a drawing of it. | — |
| 6 | packing | medium | 5-7 | Introduces planning and cause-and-effect: what the weather and the activities mean for what you carry — and practises telling a good idea from a bad one, not just following a list. | — |
| 7 | matching | medium | 5-7 | Trains shape recognition and one-to-one correspondence by matching each subject to its silhouette. | — |
| 8 | quiz | medium | 7-7 | Checks what the child has picked up about the destination and its country, and practises reading three short options and choosing between them. | — |
| 9 | drawing | medium | 6-8 | Encourages observation and recall, and gives the child a page that is entirely their own work. | — |
| 10 | maze | medium | 6-8 | Practises visual planning, sequencing and pencil control, and links the trip to one real place the family will actually see. | — |
| 11 | coloring | medium | 6-8 | Develops fine motor control and color choice while introducing a real place the child will visit. | [`11_coloring.md`](prompts/11_coloring.md) |
| 12 | reflection | easy | 4-6 | Consolidates memory of the trip and builds early metacognition — noticing what you enjoyed and what you learned. | — |

## Pages

### Page 1 — Noa and Amit's Big Trip to Kfar Hanokdim

| | |
| --- | --- |
| **Activity type** | `cover` |
| **Educational goal** | Builds anticipation for the trip and gives the child ownership of the book. |
| **Estimated age** | 4-6 |
| **Difficulty** | easy |
| **Prompt file** | [`01_cover.md`](prompts/01_cover.md) |

**Instructions for the child**

> Get ready for adventure!

**Required illustration**

A welcoming cover scene of the Nokdim valley lookout.
A cheerful establishing view of Kfar Hanokdim, with the Nokdim valley lookout as the centrepiece and children setting off to explore.
Must contain: 2 happy children with small backpacks, the Nokdim valley lookout, the camel yard, rock hyraxes, white broom shrubs.
Render mode: `coloring`.

**Image prompt**

```text
Create a black-and-white coloring page for a children's travel activity book.

Scene:
A cheerful establishing view of Kfar Hanokdim, with the Nokdim valley lookout as the centrepiece and children setting off to explore.

Include:
• 2 happy children with small backpacks
• the Nokdim valley lookout
• the camel yard
• rock hyraxes
• white broom shrubs

Layout:
Leave a clear empty banner area across the top third for the title and an empty ruled line near the bottom for the child's name.

Style:
• Bold, clean, uniform black outlines on white with large open areas to color — no shading, no hatching, no grey fills, no solid black areas
• Friendly modern children's picture-book line art: rounded shapes, even line weight, simple expressive faces
• Clean, uncluttered composition — every element clearly separated and easy to recognise
• Age-appropriate for a 5-7 year old: gentle and welcoming, nothing frightening, no weapons, no injuries
• Visually consistent with every other page of this book: a single coherent book about Kfar Hanokdim, same line weight, same simple horizon treatment and the same friendly character design on every page
• Recurring characters, drawn identically wherever they appear: two child explorers, about 5 and about 7 years old, with simple round friendly faces, practical outdoor clothes and small backpacks

Constraints:
• Portrait A4 (210 x 297 mm), vertical orientation, 300 DPI
• Pure white background, generous margins, nothing important within 12 mm of the page edge
• No text, letters, numbers, captions, speech bubbles, watermarks or logos anywhere in the image
• Prints cleanly in black and white on a home printer
• Leave generous white space in the title banner and name line.
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "easy",
  "focus": "landmarks",
  "personalized": true,
  "child_names": [
    "Noa",
    "Amit"
  ],
  "title_placeholder": true,
  "name_line": true
}
```

</details>


### Page 2 — Color desert lizards

| | |
| --- | --- |
| **Activity type** | `coloring` |
| **Educational goal** | Develops fine motor control and color choice while introducing a real place the child will visit. |
| **Estimated age** | 4-6 |
| **Difficulty** | easy |
| **Prompt file** | [`02_coloring.md`](prompts/02_coloring.md) |

**Instructions for the child**

> Color this picture of desert lizards. Look closely for tamarisk bushes, date palms and desert lizards — you may see them for real on your trip!

**Required illustration**

Desert lizards.
desert lizards at Kfar Hanokdim, seen from a child's eye level, with plenty of large open areas to color.
Must contain: tamarisk bushes, date palms, desert lizards, goats and sheep.
Render mode: `coloring`.

**Image prompt**

```text
Create a black-and-white coloring page for a children's travel activity book.

Scene:
desert lizards at Kfar Hanokdim, seen from a child's eye level, with plenty of large open areas to color.

Include:
• tamarisk bushes
• date palms
• desert lizards
• goats and sheep

Layout:
Single full-page scene, very large shapes, few details, thick outlines.

Style:
• Bold, clean, uniform black outlines on white with large open areas to color — no shading, no hatching, no grey fills, no solid black areas
• Friendly modern children's picture-book line art: rounded shapes, even line weight, simple expressive faces
• Clean, uncluttered composition — every element clearly separated and easy to recognise
• Age-appropriate for a 5-7 year old: gentle and welcoming, nothing frightening, no weapons, no injuries
• Visually consistent with every other page of this book: a single coherent book about Kfar Hanokdim, same line weight, same simple horizon treatment and the same friendly character design on every page
• Recurring characters, drawn identically wherever they appear: two child explorers, about 5 and about 7 years old, with simple round friendly faces, practical outdoor clothes and small backpacks

Constraints:
• Portrait A4 (210 x 297 mm), vertical orientation, 300 DPI
• Pure white background, generous margins, nothing important within 12 mm of the page edge
• No text, letters, numbers, captions, speech bubbles, watermarks or logos anywhere in the image
• Prints cleanly in black and white on a home printer
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "easy",
  "focus": "wildlife",
  "subject": "desert lizards",
  "look_for": [
    "tamarisk bushes",
    "date palms",
    "desert lizards"
  ],
  "knowledge_focus": "wildlife"
}
```

</details>


### Page 3 — The Path to a fountain near Kfar Hanokdim

| | |
| --- | --- |
| **Activity type** | `maze` |
| **Educational goal** | Practises visual planning, sequencing and pencil control, and links the trip to one real place the family will actually see. |
| **Estimated age** | 4-6 |
| **Difficulty** | easy |
| **Prompt file** | — |

**Instructions for the child**

> Help Noa get from the airplane all the way to a fountain near Kfar Hanokdim. Draw one line through the maze without crossing any walls.

**Required illustration**

—

**Image prompt**

_No illustration prompt for this page._

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "easy",
  "focus": "activities",
  "start": "the airplane",
  "goal": "a fountain near Kfar Hanokdim",
  "needs_illustration": false,
  "grid": {
    "columns": 9,
    "rows": 11,
    "walls": [
      [
        10,
        13,
        5,
        1,
        5,
        3,
        13,
        5,
        3
      ],
      [
        12,
        3,
        9,
        6,
        11,
        12,
        5,
        5,
        2
      ],
      [
        9,
        6,
        12,
        3,
        12,
        3,
        9,
        3,
        10
      ],
      [
        12,
        5,
        5,
        6,
        9,
        6,
        10,
        12,
        6
      ],
      [
        9,
        5,
        1,
        7,
        8,
        5,
        6,
        13,
        3
      ],
      [
        14,
        9,
        2,
        9,
        6,
        13,
        1,
        3,
        10
      ],
      [
        9,
        6,
        14,
        12,
        5,
        5,
        6,
        12,
        2
      ],
      [
        12,
        5,
        3,
        9,
        1,
        5,
        7,
        9,
        6
      ],
      [
        9,
        1,
        6,
        10,
        10,
        9,
        5,
        6,
        11
      ],
      [
        10,
        14,
        9,
        6,
        10,
        10,
        13,
        5,
        2
      ],
      [
        12,
        5,
        4,
        7,
        12,
        4,
        5,
        5,
        2
      ]
    ],
    "start_cell": [
      0,
      0
    ],
    "goal_cell": [
      10,
      8
    ]
  },
  "symbol_keys": [
    "airplane",
    "fountain"
  ]
}
```

</details>


### Page 4 — Kfar Hanokdim Word Search

| | |
| --- | --- |
| **Activity type** | `word_search` |
| **Educational goal** | Builds letter recognition, spelling and systematic visual scanning, using vocabulary from the place the child is visiting. |
| **Estimated age** | 6-6 |
| **Difficulty** | easy |
| **Prompt file** | — |

**Instructions for the child**

> 8 words from your trip are hiding in the grid — across and down. Find and circle each one: Bushes, Camels, Coffee, Desert, Hoopoe, Labneh, Palms and Tent.

**Required illustration**

—

**Image prompt**

_No illustration prompt for this page._

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "easy",
  "focus": "plants",
  "grid": [
    "FHSSZFLTNQ",
    "AHKBTCACSI",
    "TOMDIEBWVC",
    "COBXXHNOZM",
    "TPUMBOESLQ",
    "EOSSIQHOCC",
    "NEHCOFFEEK",
    "TREANPALMS",
    "CYSCAMELSK",
    "DESERTNDQP"
  ],
  "grid_size": 10,
  "words": [
    "BUSHES",
    "CAMELS",
    "COFFEE",
    "DESERT",
    "HOOPOE",
    "LABNEH",
    "PALMS",
    "TENT"
  ],
  "placements": [
    {
      "word": "BUSHES",
      "row": 3,
      "column": 2,
      "direction": [
        1,
        0
      ]
    },
    {
      "word": "CAMELS",
      "row": 8,
      "column": 3,
      "direction": [
        0,
        1
      ]
    },
    {
      "word": "COFFEE",
      "row": 6,
      "column": 3,
      "direction": [
        0,
        1
      ]
    },
    {
      "word": "DESERT",
      "row": 9,
      "column": 0,
      "direction": [
        0,
        1
      ]
    },
    {
      "word": "HOOPOE",
      "row": 1,
      "column": 1,
      "direction": [
        1,
        0
      ]
    },
    {
      "word": "LABNEH",
      "row": 0,
      "column": 6,
      "direction": [
        1,
        0
      ]
    },
    {
      "word": "PALMS",
      "row": 7,
      "column": 5,
      "direction": [
        0,
        1
      ]
    },
    {
      "word": "TENT",
      "row": 4,
      "column": 0,
      "direction": [
        1,
        0
      ]
    }
  ],
  "word_count": 8,
  "needs_illustration": false
}
```

</details>


### Page 5 — Kfar Hanokdim Scavenger Hunt

| | |
| --- | --- |
| **Activity type** | `scavenger_hunt` |
| **Educational goal** | Turns travelling itself into an active search: builds observation skills and vocabulary by sending the child looking for the real thing, not a drawing of it. |
| **Estimated age** | 5-7 |
| **Difficulty** | medium |
| **Prompt file** | — |

**Instructions for the child**

> Keep your eyes open the whole way! There are 16 things to find on this page. Tick the box under each picture the moment you spot the real thing — anywhere, on any day of the trip.

**Required illustration**

—

**Image prompt**

_No illustration prompt for this page._

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "medium",
  "focus": "local_food",
  "items": [
    "a flag",
    "a squirrel",
    "a police car",
    "an insect",
    "a cow",
    "a dog",
    "a Nubian ibex",
    "a taxi",
    "a man with a mustache",
    "an ice cream",
    "an airplane",
    "a stop sign",
    "a bicycle",
    "a butterfly",
    "a bird on the ground",
    "a horse"
  ],
  "item_count": 16,
  "symbol_keys": [
    "flag",
    "squirrel",
    "police-car",
    "insect",
    "cow",
    "dog",
    "nubian-ibex",
    "taxi",
    "man-with-mustache",
    "ice-cream",
    "airplane",
    "stop-sign",
    "bicycle",
    "butterfly",
    "pigeon",
    "horse"
  ],
  "columns": 4,
  "rows": 4,
  "needs_illustration": false
}
```

</details>


### Page 6 — Pack Your Explorer Bag

| | |
| --- | --- |
| **Activity type** | `packing` |
| **Educational goal** | Introduces planning and cause-and-effect: what the weather and the activities mean for what you carry — and practises telling a good idea from a bad one, not just following a list. |
| **Estimated age** | 5-7 |
| **Difficulty** | medium |
| **Prompt file** | — |

**Instructions for the child**

> You are going to Kfar Hanokdim! Draw a line from everything you should pack to the backpack — but a few things don't belong, so look closely. Then draw one more thing of your own in the empty circle and connect it too.

**Required illustration**

—

**Image prompt**

_No illustration prompt for this page._

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "medium",
  "focus": "history",
  "backpack_key": "backpack",
  "ring_keys": [
    "woolly-hat",
    "sunscreen",
    "pomegranate",
    "umbrella",
    "gloves",
    "baseball-cap",
    "souvlaki",
    "rain-coat",
    "pasta"
  ],
  "pack_keys": [
    "baseball-cap",
    "gloves",
    "rain-coat",
    "sunscreen",
    "umbrella",
    "woolly-hat"
  ],
  "distractor_keys": [
    "pasta",
    "pomegranate",
    "souvlaki"
  ],
  "items": [
    "a baseball cap",
    "sunscreen",
    "gloves",
    "a woolly hat",
    "an open umbrella",
    "a rain coat"
  ],
  "not_to_pack": [
    "souvlaki",
    "a pomegranate",
    "a bowl of pasta"
  ],
  "blank_slots": 1,
  "matched_conditions": [
    "hot",
    "cold",
    "rain",
    "hike",
    "night"
  ],
  "needs_illustration": false
}
```

</details>


### Page 7 — Match the Shadows

| | |
| --- | --- |
| **Activity type** | `matching` |
| **Educational goal** | Trains shape recognition and one-to-one correspondence by matching each subject to its silhouette. |
| **Estimated age** | 5-7 |
| **Difficulty** | medium |
| **Prompt file** | — |

**Instructions for the child**

> Each picture on the left has a shadow on the right. Draw a line from every picture to its own shadow.

**Required illustration**

—

**Image prompt**

_No illustration prompt for this page._

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "medium",
  "focus": "interesting_facts",
  "pair_count": 5,
  "left_column": [
    "an airplane",
    "a cow",
    "a boat",
    "gloves",
    "a swan"
  ],
  "right_column": [
    "a swan",
    "gloves",
    "a boat",
    "a cow",
    "an airplane"
  ],
  "symbol_keys": [
    "airplane",
    "cow",
    "boat",
    "gloves",
    "swan"
  ],
  "shadow_keys": [
    "swan",
    "gloves",
    "boat",
    "cow",
    "airplane"
  ],
  "answer_key": {
    "an airplane": 5,
    "a cow": 4,
    "a boat": 3,
    "gloves": 2,
    "a swan": 1
  },
  "needs_illustration": false
}
```

</details>


### Page 8 — The Kfar Hanokdim Quiz

| | |
| --- | --- |
| **Activity type** | `quiz` |
| **Educational goal** | Checks what the child has picked up about the destination and its country, and practises reading three short options and choosing between them. |
| **Estimated age** | 7-7 |
| **Difficulty** | medium |
| **Prompt file** | — |

**Instructions for the child**

> Circle the answer you think is right. There are 3 questions — ask a grown-up if you get stuck.

**Required illustration**

—

**Image prompt**

_No illustration prompt for this page._

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "medium",
  "focus": "landmarks",
  "questions": [
    {
      "question": "What is the capital city of Israel?",
      "options": [
        "Nairobi",
        "Jerusalem",
        "Rome"
      ],
      "answer": "Jerusalem",
      "answer_index": 2,
      "category": "",
      "kind": "capital"
    },
    {
      "question": "Which colors are on the flag of Israel?",
      "options": [
        "blue and orange",
        "blue and red",
        "blue and white"
      ],
      "answer": "blue and white",
      "answer_index": 3,
      "category": "",
      "kind": "flag"
    },
    {
      "question": "What money do people use in Israel?",
      "options": [
        "the shekel",
        "the Australian dollar",
        "the Canadian dollar"
      ],
      "answer": "the shekel",
      "answer_index": 1,
      "category": "",
      "kind": "currency"
    }
  ],
  "question_count": 3,
  "needs_illustration": false,
  "dictionary": [
    {
      "concept": "yes",
      "meaning": "yes",
      "native": "כן",
      "pronunciation": "ken"
    },
    {
      "concept": "no",
      "meaning": "no",
      "native": "לא",
      "pronunciation": "lo"
    },
    {
      "concept": "please",
      "meaning": "please",
      "native": "בבקשה",
      "pronunciation": "be-va-ka-SHA"
    },
    {
      "concept": "thank_you",
      "meaning": "thank you",
      "native": "תודה",
      "pronunciation": "to-DA"
    },
    {
      "concept": "sorry",
      "meaning": "sorry",
      "native": "סליחה",
      "pronunciation": "sli-KHA"
    },
    {
      "concept": "good_morning",
      "meaning": "good morning",
      "native": "בוקר טוב",
      "pronunciation": "BO-ker tov"
    },
    {
      "concept": "good_night",
      "meaning": "good night",
      "native": "לילה טוב",
      "pronunciation": "LAI-la tov"
    },
    {
      "concept": "water",
      "meaning": "water",
      "native": "מים",
      "pronunciation": "MAI-im"
    },
    {
      "concept": "bathroom",
      "meaning": "bathroom",
      "native": "שירותים",
      "pronunciation": "she-ru-TIM"
    },
    {
      "concept": "family",
      "meaning": "family",
      "native": "משפחה",
      "pronunciation": "mish-pa-KHA"
    }
  ],
  "native_language": "he",
  "native_direction": "rtl",
  "script": "hebrew"
}
```

</details>


### Page 9 — Draw What You Saw

| | |
| --- | --- |
| **Activity type** | `drawing` |
| **Educational goal** | Encourages observation and recall, and gives the child a page that is entirely their own work. |
| **Estimated age** | 6-8 |
| **Difficulty** | medium |
| **Prompt file** | — |

**Instructions for the child**

> Draw what you remember about desert lizards inside the frame — the way *you* saw it. Add as many small details as you can.

**Required illustration**

—

**Image prompt**

_No illustration prompt for this page._

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "medium",
  "focus": "wildlife",
  "prompt_subject": "desert lizards",
  "blank_page": true,
  "needs_illustration": false
}
```

</details>


### Page 10 — The Path to a fountain near Kfar Hanokdim

| | |
| --- | --- |
| **Activity type** | `maze` |
| **Educational goal** | Practises visual planning, sequencing and pencil control, and links the trip to one real place the family will actually see. |
| **Estimated age** | 6-8 |
| **Difficulty** | medium |
| **Prompt file** | — |

**Instructions for the child**

> Help Noa get from the dog all the way to a fountain near Kfar Hanokdim. Draw one line through the maze without crossing any walls.

**Required illustration**

—

**Image prompt**

_No illustration prompt for this page._

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "medium",
  "focus": "activities",
  "start": "the dog",
  "goal": "a fountain near Kfar Hanokdim",
  "needs_illustration": false,
  "grid": {
    "columns": 12,
    "rows": 14,
    "walls": [
      [
        10,
        13,
        1,
        5,
        5,
        3,
        9,
        5,
        3,
        9,
        5,
        3
      ],
      [
        12,
        3,
        12,
        3,
        11,
        12,
        6,
        11,
        10,
        10,
        9,
        2
      ],
      [
        9,
        6,
        9,
        6,
        10,
        9,
        5,
        2,
        10,
        14,
        10,
        14
      ],
      [
        12,
        3,
        12,
        3,
        12,
        4,
        7,
        10,
        12,
        3,
        12,
        3
      ],
      [
        11,
        12,
        5,
        6,
        9,
        5,
        5,
        4,
        3,
        12,
        3,
        10
      ],
      [
        8,
        1,
        5,
        3,
        10,
        11,
        9,
        5,
        6,
        9,
        6,
        10
      ],
      [
        14,
        10,
        9,
        6,
        10,
        12,
        2,
        13,
        3,
        12,
        5,
        2
      ],
      [
        9,
        6,
        12,
        3,
        12,
        3,
        12,
        3,
        10,
        9,
        5,
        6
      ],
      [
        10,
        9,
        3,
        12,
        3,
        12,
        3,
        8,
        6,
        12,
        3,
        11
      ],
      [
        10,
        14,
        12,
        5,
        4,
        3,
        10,
        14,
        9,
        5,
        6,
        10
      ],
      [
        8,
        5,
        5,
        5,
        3,
        12,
        6,
        9,
        6,
        13,
        5,
        2
      ],
      [
        10,
        11,
        9,
        1,
        6,
        9,
        5,
        6,
        9,
        3,
        9,
        2
      ],
      [
        10,
        10,
        10,
        14,
        9,
        6,
        13,
        5,
        2,
        10,
        10,
        10
      ],
      [
        12,
        6,
        12,
        5,
        4,
        5,
        5,
        5,
        6,
        12,
        6,
        10
      ]
    ],
    "start_cell": [
      0,
      0
    ],
    "goal_cell": [
      13,
      11
    ]
  },
  "symbol_keys": [
    "dog",
    "fountain"
  ]
}
```

</details>


### Page 11 — Color desert wildflowers after rain

| | |
| --- | --- |
| **Activity type** | `coloring` |
| **Educational goal** | Develops fine motor control and color choice while introducing a real place the child will visit. |
| **Estimated age** | 6-8 |
| **Difficulty** | medium |
| **Prompt file** | [`11_coloring.md`](prompts/11_coloring.md) |

**Instructions for the child**

> Color this picture of desert wildflowers after rain. Look closely for desert wildflowers after rain, date palms and hoopoe birds — you may see them for real on your trip!

**Required illustration**

Desert wildflowers after rain.
desert wildflowers after rain at Kfar Hanokdim, seen from a child's eye level, with plenty of large open areas to color.
Must contain: desert wildflowers after rain, date palms, hoopoe birds, donkeys.
Render mode: `coloring`.

**Image prompt**

```text
Create a black-and-white coloring page for a children's travel activity book.

Scene:
desert wildflowers after rain at Kfar Hanokdim, seen from a child's eye level, with plenty of large open areas to color.

Include:
• desert wildflowers after rain
• date palms
• hoopoe birds
• donkeys

Layout:
Single full-page scene, medium-sized shapes with some background detail.

Style:
• Bold, clean, uniform black outlines on white with large open areas to color — no shading, no hatching, no grey fills, no solid black areas
• Friendly modern children's picture-book line art: rounded shapes, even line weight, simple expressive faces
• Clean, uncluttered composition — every element clearly separated and easy to recognise
• Age-appropriate for a 5-7 year old: gentle and welcoming, nothing frightening, no weapons, no injuries
• Visually consistent with every other page of this book: a single coherent book about Kfar Hanokdim, same line weight, same simple horizon treatment and the same friendly character design on every page
• Recurring characters, drawn identically wherever they appear: two child explorers, about 5 and about 7 years old, with simple round friendly faces, practical outdoor clothes and small backpacks

Constraints:
• Portrait A4 (210 x 297 mm), vertical orientation, 300 DPI
• Pure white background, generous margins, nothing important within 12 mm of the page edge
• No text, letters, numbers, captions, speech bubbles, watermarks or logos anywhere in the image
• Prints cleanly in black and white on a home printer
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "medium",
  "focus": "plants",
  "subject": "desert wildflowers after rain",
  "look_for": [
    "desert wildflowers after rain",
    "date palms",
    "hoopoe birds"
  ],
  "knowledge_focus": "plants"
}
```

</details>


### Page 12 — My Kfar Hanokdim Memories

| | |
| --- | --- |
| **Activity type** | `reflection` |
| **Educational goal** | Consolidates memory of the trip and builds early metacognition — noticing what you enjoyed and what you learned. |
| **Estimated age** | 4-6 |
| **Difficulty** | easy |
| **Prompt file** | — |

**Instructions for the child**

> Your trip is nearly over! Draw or write your favorite moment, answer the questions, and color one star for every day you had fun.

**Required illustration**

—

**Image prompt**

_No illustration prompt for this page._

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "easy",
  "focus": "local_food",
  "prompts": [
    "The best thing I saw was...",
    "Something new I learned was...",
    "Next time I want to..."
  ],
  "writing_lines": 6,
  "stars": 5,
  "closing_page": true,
  "needs_illustration": false
}
```

</details>


## Destination knowledge used

Everything above was built from these facts, supplied by the `file`
provider.

**Landmarks**

- the big Bedouin hospitality tent
- the camel yard
- the date palm grove
- the Nokdim valley lookout
- the Masada cliff fortress
- the Dead Sea shore

**Wildlife**

- camels
- Nubian ibex
- donkeys
- rock hyraxes
- desert lizards
- hoopoe birds
- goats and sheep

**Plants**

- date palms
- acacia trees
- tamarisk bushes
- white broom shrubs
- desert wildflowers after rain

**Activities**

- riding a camel
- sleeping in a Bedouin tent
- baking pita on a saj griddle
- a desert hike at sunrise
- stargazing after dark
- sitting around the campfire
- a donkey ride

**History**

- Bedouin families have crossed this desert for centuries
- hospitality to travellers is an old desert rule
- spice caravans once passed through the Negev
- Masada nearby is almost two thousand years old

**Local Food**

- fresh pita from the saj
- labneh cheese with olive oil
- hummus
- sweet tea with na'ana mint
- cardamom coffee
- dates from the palm trees

**Weather**

- hot and dry during the day
- surprisingly cold at night
- almost no rain
- very clear starry skies

**Interesting Facts**

- A camel can drink over 100 litres of water in one go.
- Bedouin tents are woven from black goat hair, which keeps them cool.
- Ibex climb steep cliffs that look impossible to stand on.
- The desert gets so cold at night that you need a jacket in summer.
- With no city lights, you can see thousands of stars here.
