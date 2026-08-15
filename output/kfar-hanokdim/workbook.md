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
| Generated | 2026-08-11T12:11:50+00:00 |


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
| 3 | maze | easy | 4-6 | Practises visual planning, sequencing and pencil control, and links the trip to one real place the family will actually see. | [`03_maze.md`](prompts/03_maze.md) |
| 4 | wildlife_facts | easy | 4-6 | Builds knowledge of local fauna and habitats, and encourages the child to look for real animals during the trip. | [`04_wildlife_facts.md`](prompts/04_wildlife_facts.md) |
| 5 | spot_difference | medium | 5-7 | Sharpens visual discrimination and attention to detail through careful comparison of two scenes. | [`05_spot_difference.md`](prompts/05_spot_difference.md) |
| 6 | word_search | medium | 6-7 | Builds letter recognition, spelling and systematic visual scanning, using vocabulary from the place the child is visiting. | [`06_word_search.md`](prompts/06_word_search.md) |
| 7 | hidden_objects | medium | 5-7 | Builds sustained visual search and vocabulary for local plants, animals and objects. | [`07_hidden_objects.md`](prompts/07_hidden_objects.md) |
| 8 | packing | medium | 5-7 | Introduces planning and cause-and-effect: what the weather and the activities mean for what you carry — and practises telling a good idea from a bad one, not just following a list. | [`08_packing.md`](prompts/08_packing.md) |
| 9 | scavenger_hunt | medium | 6-8 | Turns travelling itself into an active search: builds observation skills and vocabulary by sending the child looking for the real thing, not a drawing of it. | [`09_scavenger_hunt.md`](prompts/09_scavenger_hunt.md) |
| 10 | quiz | medium | 7-8 | Checks what the child has picked up about the destination and its country, and practises reading three short options and choosing between them. | [`10_quiz.md`](prompts/10_quiz.md) |
| 11 | matching | medium | 6-8 | Trains shape recognition and one-to-one correspondence by matching each subject to its silhouette. | [`11_matching.md`](prompts/11_matching.md) |
| 12 | reflection | easy | 4-6 | Consolidates memory of the trip and builds early metacognition — noticing what you enjoyed and what you learned. | [`12_reflection.md`](prompts/12_reflection.md) |

## Pages

### Page 1 — Noa and Amit's Big Trip to Kfar Hanokdim

| | |
| --- | --- |
| **Activity type** | `cover` |
| **Educational goal** | Builds anticipation for the trip and gives the child ownership of the book. |
| **Estimated age** | 4-6 |
| **Difficulty** | easy |
| **Prompt file** | [`prompts/01_cover.md`](prompts/01_cover.md) |

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
| **Prompt file** | [`prompts/02_coloring.md`](prompts/02_coloring.md) |

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


### Page 3 — The Path to the Masada cliff fortress

| | |
| --- | --- |
| **Activity type** | `maze` |
| **Educational goal** | Practises visual planning, sequencing and pencil control, and links the trip to one real place the family will actually see. |
| **Estimated age** | 4-6 |
| **Difficulty** | easy |
| **Prompt file** | [`prompts/03_maze.md`](prompts/03_maze.md) |

**Instructions for the child**

> Help Noa get from home all the way to the Masada cliff fortress. Draw one line through the maze without crossing any walls.

**Required illustration**

A decorative border for a maze page.
A thin decorative border of Kfar Hanokdim motifs framing an otherwise completely empty page.
Must contain: the Masada cliff fortress.
Render mode: `frame`.

**Image prompt**

```text
Create a black-and-white activity page with a large empty drawing area for a children's travel activity book.

Scene:
A thin decorative border of Kfar Hanokdim motifs framing an otherwise completely empty page.

Include:
• the Masada cliff fortress

Layout:
Border only, no more than 15 mm wide. The entire centre of the page is left blank white — the maze is typeset there, not drawn.

Style:
• Delicate black line art confined to the border, with the working area left completely blank white
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
• Do not draw a maze, a path, walls, corridors or a grid of any kind.
• This border is optional decoration; the page is complete without it.
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "easy",
  "focus": "activities",
  "start": "home",
  "goal": "the Masada cliff fortress",
  "needs_illustration": false,
  "illustration": "decorative",
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
    "masada-cliff-fortress-flag"
  ]
}
```

</details>


### Page 4 — Amazing Animals of Kfar Hanokdim

| | |
| --- | --- |
| **Activity type** | `wildlife_facts` |
| **Educational goal** | Builds knowledge of local fauna and habitats, and encourages the child to look for real animals during the trip. |
| **Estimated age** | 4-6 |
| **Difficulty** | easy |
| **Prompt file** | [`prompts/04_wildlife_facts.md`](prompts/04_wildlife_facts.md) |

**Instructions for the child**

> Meet 3 animals that live around Kfar Hanokdim. Color each one, then put a star next to the animal you would most like to see.

**Required illustration**

A fact card sheet of 3 animals from Kfar Hanokdim.
A page of equally sized cards, each holding one animal drawn accurately and clearly in its natural surroundings.
Must contain: desert lizards, goats and sheep, hoopoe birds.
Render mode: `illustration`.

**Image prompt**

```text
Create a black-and-white illustrated information page for a children's travel activity book.

Scene:
A page of equally sized cards, each holding one animal drawn accurately and clearly in its natural surroundings.

Include:
• desert lizards
• goats and sheep
• hoopoe birds

Layout:
3 rectangular cards stacked down the page. In each card the animal fills the left two-thirds and the right third is left empty for a caption and a star the child can color.

Style:
• Accurate black line art with light grey shading used sparingly for depth, keeping every subject clearly identifiable
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
• Draw the animals in this order, one per card: desert lizards, goats and sheep, hoopoe birds
• Anatomically believable animals — this page teaches, so no cartoon proportions that misrepresent the species.
• Leave the caption strip in each card completely blank.
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "easy",
  "focus": "plants",
  "animals": [
    "desert lizards",
    "goats and sheep",
    "hoopoe birds"
  ],
  "cards": [
    {
      "animal": "desert lizards",
      "caption": "desert lizards — look for one near the date palm grove."
    },
    {
      "animal": "goats and sheep",
      "caption": "goats and sheep — look for one near the big Bedouin hospitality tent."
    },
    {
      "animal": "hoopoe birds",
      "caption": "hoopoe birds — look for one near the camel yard."
    }
  ],
  "star_rating": true
}
```

</details>


### Page 5 — Spot the Differences

| | |
| --- | --- |
| **Activity type** | `spot_difference` |
| **Educational goal** | Sharpens visual discrimination and attention to detail through careful comparison of two scenes. |
| **Estimated age** | 5-7 |
| **Difficulty** | medium |
| **Prompt file** | [`prompts/05_spot_difference.md`](prompts/05_spot_difference.md) |

**Instructions for the child**

> These two pictures of the Dead Sea shore look the same — but 6 things are different. Circle every difference you find.

**Required illustration**

Two nearly identical scenes of the Dead Sea shore.
The same view of the Dead Sea shore at Kfar Hanokdim drawn twice: the top half is the original, the bottom half repeats it with small changes.
Must contain: dates from the palm trees, rock hyraxes, goats and sheep, sleeping in a Bedouin tent, hoopoe birds, hummus.
Render mode: `puzzle`.

**Image prompt**

```text
Create a black-and-white puzzle illustration for a children's travel activity book.

Scene:
The same view of the Dead Sea shore at Kfar Hanokdim drawn twice: the top half is the original, the bottom half repeats it with small changes.

Include:
• dates from the palm trees
• rock hyraxes
• goats and sheep
• sleeping in a Bedouin tent
• hoopoe birds
• hummus

Layout:
Portrait page split into two equal panels stacked vertically, each with a thin frame, containing exactly 6 deliberate differences.

Style:
• Crisp black line art with high contrast and clear separation between elements, so the puzzle stays readable when printed small — no shading or textures that could be mistaken for part of the puzzle
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
• Introduce exactly 6 differences between the two panels: missing — dates from the palm trees; extra — rock hyraxes; moved — goats and sheep; resized — sleeping in a Bedouin tent; missing — hoopoe birds; extra — hummus
• Everything not listed as a difference must be pixel-for-pixel identical.
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "medium",
  "focus": "local_food",
  "subject": "the Dead Sea shore",
  "difference_count": 6,
  "differences": [
    {
      "item": "dates from the palm trees",
      "kind": "missing",
      "description": "dates from the palm trees is missing from the second picture"
    },
    {
      "item": "rock hyraxes",
      "kind": "extra",
      "description": "an extra rock hyraxes appears in the second picture"
    },
    {
      "item": "goats and sheep",
      "kind": "moved",
      "description": "goats and sheep has moved to the other side"
    },
    {
      "item": "sleeping in a Bedouin tent",
      "kind": "resized",
      "description": "sleeping in a Bedouin tent is a different size"
    },
    {
      "item": "hoopoe birds",
      "kind": "missing",
      "description": "hoopoe birds is missing from the second picture"
    },
    {
      "item": "hummus",
      "kind": "extra",
      "description": "an extra hummus appears in the second picture"
    }
  ]
}
```

</details>


### Page 6 — Kfar Hanokdim Word Search

| | |
| --- | --- |
| **Activity type** | `word_search` |
| **Educational goal** | Builds letter recognition, spelling and systematic visual scanning, using vocabulary from the place the child is visiting. |
| **Estimated age** | 6-7 |
| **Difficulty** | medium |
| **Prompt file** | [`prompts/06_word_search.md`](prompts/06_word_search.md) |

**Instructions for the child**

> 8 words from your trip are hiding in the grid — across, down and sometimes slanted. Find and circle each one: Acacia, Bedouin, Donkeys, Griddle, Labneh, Lookout, Nubian and Shrubs.

**Required illustration**

A decorative border for a word search page.
A thin decorative border of Kfar Hanokdim motifs framing an otherwise completely empty page.
Must contain: tamarisk bushes, date palms, donkeys.
Render mode: `frame`.

**Image prompt**

```text
Create a black-and-white activity page with a large empty drawing area for a children's travel activity book.

Scene:
A thin decorative border of Kfar Hanokdim motifs framing an otherwise completely empty page.

Include:
• tamarisk bushes
• date palms
• donkeys

Layout:
Border only, no more than 15 mm wide. The entire centre of the page is left blank white — the puzzle grid is typeset there, not drawn.

Style:
• Delicate black line art confined to the border, with the working area left completely blank white
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
• Do not draw a grid, squares, letters or any puzzle content.
• This border is optional decoration; the page is complete without it.
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "medium",
  "focus": "history",
  "grid": [
    "BVXMUDLLEHSG",
    "SHRUBSOCYZER",
    "XMOXFLORYQAI",
    "ALJDONKEYSXD",
    "DMRCNAOFHNHD",
    "DAAWTLUJGYJL",
    "GRCWXMTUNNVE",
    "RBFALBEDOUIN",
    "RSKZCVWGGBNJ",
    "ZSSPIITTIIXG",
    "LEUCOOALCAIQ",
    "URJVKMLABNEH"
  ],
  "grid_size": 12,
  "words": [
    "ACACIA",
    "BEDOUIN",
    "DONKEYS",
    "GRIDDLE",
    "LABNEH",
    "LOOKOUT",
    "NUBIAN",
    "SHRUBS"
  ],
  "placements": [
    {
      "word": "ACACIA",
      "row": 5,
      "column": 1,
      "direction": [
        1,
        1
      ]
    },
    {
      "word": "BEDOUIN",
      "row": 7,
      "column": 5,
      "direction": [
        0,
        1
      ]
    },
    {
      "word": "DONKEYS",
      "row": 3,
      "column": 3,
      "direction": [
        0,
        1
      ]
    },
    {
      "word": "GRIDDLE",
      "row": 0,
      "column": 11,
      "direction": [
        1,
        0
      ]
    },
    {
      "word": "LABNEH",
      "row": 11,
      "column": 6,
      "direction": [
        0,
        1
      ]
    },
    {
      "word": "LOOKOUT",
      "row": 0,
      "column": 6,
      "direction": [
        1,
        0
      ]
    },
    {
      "word": "NUBIAN",
      "row": 6,
      "column": 9,
      "direction": [
        1,
        0
      ]
    },
    {
      "word": "SHRUBS",
      "row": 1,
      "column": 0,
      "direction": [
        0,
        1
      ]
    }
  ],
  "word_count": 8,
  "illustration": "decorative",
  "needs_illustration": false
}
```

</details>


### Page 7 — Find the Hidden Things

| | |
| --- | --- |
| **Activity type** | `hidden_objects` |
| **Educational goal** | Builds sustained visual search and vocabulary for local plants, animals and objects. |
| **Estimated age** | 5-7 |
| **Difficulty** | medium |
| **Prompt file** | [`prompts/07_hidden_objects.md`](prompts/07_hidden_objects.md) |

**Instructions for the child**

> 7 things are hiding in this picture of the Dead Sea shore: camels, Nubian ibex, hoopoe birds, labneh cheese with olive oil, goats and sheep, date palms and desert wildflowers after rain. Circle each one as you find it.

**Required illustration**

A busy search-and-find scene at the Dead Sea shore.
A lively wide view of the Dead Sea shore at Kfar Hanokdim, full of nooks, foliage and small structures where objects can hide.
Must contain: camels, Nubian ibex, hoopoe birds, labneh cheese with olive oil, goats and sheep, date palms, desert wildflowers after rain.
Render mode: `puzzle`.

**Image prompt**

```text
Create a black-and-white puzzle illustration for a children's travel activity book.

Scene:
A lively wide view of the Dead Sea shore at Kfar Hanokdim, full of nooks, foliage and small structures where objects can hide.

Include:
• camels
• Nubian ibex
• hoopoe birds
• labneh cheese with olive oil
• goats and sheep
• date palms
• desert wildflowers after rain

Layout:
One detailed full-page scene. Each hidden object is drawn completely and left partly visible — tucked behind or among scenery, never fully covered and never shrunk beyond easy recognition.

Style:
• Crisp black line art with high contrast and clear separation between elements, so the puzzle stays readable when printed small — no shading or textures that could be mistaken for part of the puzzle
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
• Hide exactly these 7 objects, one of each: camels, Nubian ibex, hoopoe birds, labneh cheese with olive oil, goats and sheep, date palms, desert wildflowers after rain
• Draw a small empty checkbox row along the bottom margin, one box per hidden object, with no text or numbers in them.
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "medium",
  "focus": "interesting_facts",
  "scene": "the Dead Sea shore",
  "objects": [
    "camels",
    "Nubian ibex",
    "hoopoe birds",
    "labneh cheese with olive oil",
    "goats and sheep",
    "date palms",
    "desert wildflowers after rain"
  ],
  "object_count": 7
}
```

</details>


### Page 8 — Pack Your Explorer Bag

| | |
| --- | --- |
| **Activity type** | `packing` |
| **Educational goal** | Introduces planning and cause-and-effect: what the weather and the activities mean for what you carry — and practises telling a good idea from a bad one, not just following a list. |
| **Estimated age** | 5-7 |
| **Difficulty** | medium |
| **Prompt file** | [`prompts/08_packing.md`](prompts/08_packing.md) |

**Instructions for the child**

> You are going to Kfar Hanokdim! Draw a line from everything you should pack to the backpack — but a few things don't belong, so look closely. Then draw one more thing of your own in the empty circle and connect it too.

**Required illustration**

A young explorer standing beside their open backpack, deciding what to take.
Render mode: `coloring`.

**Image prompt**

```text
Create a black-and-white coloring page for a children's travel activity book.

Scene:
a young explorer standing beside their open backpack, deciding what to take

Layout:
A single small header illustration for the top of a puzzle page: one child and one open backpack, wide and short, with empty white space around them. No other objects, no lines, no grid.

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
• Draw only the child and the backpack — no packing items scattered around them, no lines and no checkboxes.
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "medium",
  "focus": "landmarks",
  "backpack_key": "backpack",
  "ring_keys": [
    "sunscreen",
    "rain-coat",
    "insect",
    "ice-cream",
    "woolly-hat",
    "umbrella",
    "gloves",
    "baseball-cap",
    "fish"
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
    "fish",
    "ice-cream",
    "insect"
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
    "an insect",
    "an ice cream",
    "a fish"
  ],
  "blank_slots": 1,
  "matched_conditions": [
    "hot",
    "cold",
    "rain",
    "hike",
    "night"
  ]
}
```

</details>


### Page 9 — Kfar Hanokdim Scavenger Hunt

| | |
| --- | --- |
| **Activity type** | `scavenger_hunt` |
| **Educational goal** | Turns travelling itself into an active search: builds observation skills and vocabulary by sending the child looking for the real thing, not a drawing of it. |
| **Estimated age** | 6-8 |
| **Difficulty** | medium |
| **Prompt file** | [`prompts/09_scavenger_hunt.md`](prompts/09_scavenger_hunt.md) |

**Instructions for the child**

> Keep your eyes open the whole way! There are 16 things to find on this page. Tick the box under each picture the moment you spot the real thing — anywhere, on any day of the trip.

**Required illustration**

A young explorer with binoculars, looking out for things to spot.
Render mode: `coloring`.

**Image prompt**

```text
Create a black-and-white coloring page for a children's travel activity book.

Scene:
a young explorer with binoculars, looking out for things to spot

Layout:
A single small header illustration for the top of a checklist page: one child with binoculars, wide and short, with empty white space around them. No grid, no boxes, no list.

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
• Draw only the child and their binoculars — no checklist, no cells, no ticks and no items around them.
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "medium",
  "focus": "wildlife",
  "items": [
    "a rain coat",
    "cardamom coffee",
    "a jar of honey",
    "a Nubian ibex",
    "fresh pita",
    "a cow",
    "a bridge",
    "a man with a mustache",
    "white broom shrubs",
    "desert lizards",
    "gloves",
    "sunglasses",
    "a water bottle",
    "flip-flops",
    "a horse",
    "dates"
  ],
  "item_count": 16,
  "symbol_keys": [
    "rain-coat",
    "cardamom-coffee",
    "honey",
    "nubian-ibex",
    "fresh-pita",
    "cow",
    "bridge",
    "man-with-mustache",
    "white-broom-shrubs",
    "desert-lizards",
    "gloves",
    "sunglasses",
    "water-bottle",
    "flip-flops",
    "horse",
    "dates"
  ],
  "columns": 4,
  "rows": 4
}
```

</details>


### Page 10 — The Kfar Hanokdim Quiz

| | |
| --- | --- |
| **Activity type** | `quiz` |
| **Educational goal** | Checks what the child has picked up about the destination and its country, and practises reading three short options and choosing between them. |
| **Estimated age** | 7-8 |
| **Difficulty** | medium |
| **Prompt file** | [`prompts/10_quiz.md`](prompts/10_quiz.md) |

**Instructions for the child**

> Circle the answer you think is right. There are 3 questions — ask a grown-up if you get stuck.

**Required illustration**

A decorative border for a quiz page.
A thin decorative border of Kfar Hanokdim motifs framing an otherwise completely empty page.
Must contain: Kfar Hanokdim.
Render mode: `frame`.

**Image prompt**

```text
Create a black-and-white activity page with a large empty drawing area for a children's travel activity book.

Scene:
A thin decorative border of Kfar Hanokdim motifs framing an otherwise completely empty page.

Include:
• Kfar Hanokdim

Layout:
Border only, no more than 15 mm wide. The entire centre of the page is left blank white — the questions and their options are typeset there as text, not drawn.

Style:
• Delicate black line art confined to the border, with the working area left completely blank white
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
• This border is optional decoration; the page is complete without it.
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "medium",
  "focus": "activities",
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
  "illustration": "decorative",
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


### Page 11 — Match the Shadows

| | |
| --- | --- |
| **Activity type** | `matching` |
| **Educational goal** | Trains shape recognition and one-to-one correspondence by matching each subject to its silhouette. |
| **Estimated age** | 6-8 |
| **Difficulty** | medium |
| **Prompt file** | [`prompts/11_matching.md`](prompts/11_matching.md) |

**Instructions for the child**

> Each picture on the left has a shadow on the right. Draw a line from every picture to its own shadow.

**Required illustration**

A young explorer looking at their own shadow on the ground.
Render mode: `coloring`.

**Image prompt**

```text
Create a black-and-white coloring page for a children's travel activity book.

Scene:
a young explorer looking at their own shadow on the ground

Layout:
A single small header illustration for the top of a puzzle page: one child and the shadow they cast, wide and short, with empty white space around them. No columns, no boxes, no other objects.

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
• Draw only the child and their own cast shadow — no puzzle, no columns, no connecting lines and no other silhouettes.
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "medium",
  "focus": "plants",
  "pair_count": 5,
  "left_column": [
    "a rain coat",
    "binoculars",
    "hiking shoes",
    "a bridge",
    "a tortoise"
  ],
  "right_column": [
    "hiking shoes",
    "a tortoise",
    "binoculars",
    "a rain coat",
    "a bridge"
  ],
  "symbol_keys": [
    "rain-coat",
    "binoculars",
    "hiking-shoes",
    "bridge",
    "turtle"
  ],
  "shadow_keys": [
    "hiking-shoes",
    "turtle",
    "binoculars",
    "rain-coat",
    "bridge"
  ],
  "answer_key": {
    "a rain coat": 4,
    "binoculars": 3,
    "hiking shoes": 1,
    "a bridge": 5,
    "a tortoise": 2
  }
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
| **Prompt file** | [`prompts/12_reflection.md`](prompts/12_reflection.md) |

**Instructions for the child**

> Your trip is nearly over! Draw or write your favorite moment, answer the questions, and color one star for every day you had fun.

**Required illustration**

A thin decorative border for a closing keepsake page.
A thin decorative border of Kfar Hanokdim motifs framing an otherwise completely empty page.
Must contain: the Masada cliff fortress, goats and sheep.
Render mode: `frame`.

**Image prompt**

```text
Create a black-and-white activity page with a large empty drawing area for a children's travel activity book.

Scene:
A thin decorative border of Kfar Hanokdim motifs framing an otherwise completely empty page.

Include:
• the Masada cliff fortress
• goats and sheep

Layout:
Border only, no more than 15 mm wide. The entire centre of the page is left blank white — the drawing box, prompts and stars are typeset there, not drawn.

Style:
• Delicate black line art confined to the border, with the working area left completely blank white
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
• Do not draw a frame, guide lines or any content in the page centre.
• This border is optional decoration; the page is complete without it.
```

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
