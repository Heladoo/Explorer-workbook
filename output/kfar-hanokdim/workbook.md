# Noa and Amit's Kfar Hanokdim Adventure Book

*An activity book for young explorers*

| Field | Value |
| --- | --- |
| Destination | Kfar Hanokdim |
| Language | en |
| Pages | 14 |
| Made for | Noa (7), Amit (9) |
| Trip | 3 day(s), itinerary: Arrival and camel yard; Desert hike and Masada; Dead Sea day |
| Special interests | animals |
| Knowledge source | file |
| Generated | 2026-07-26T11:37:48+00:00 |


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
| 1 | cover | easy | 6-8 | Builds anticipation for the trip and gives the child ownership of the book. | [`01_cover.md`](prompts/01_cover.md) |
| 2 | hidden_objects | easy | 6-8 | Builds sustained visual search and vocabulary for local plants, animals and objects. | [`02_hidden_objects.md`](prompts/02_hidden_objects.md) |
| 3 | wildlife_facts | easy | 6-8 | Builds knowledge of local fauna and habitats, and encourages the child to look for real animals during the trip. | [`03_wildlife_facts.md`](prompts/03_wildlife_facts.md) |
| 4 | matching | easy | 6-8 | Trains shape recognition and one-to-one correspondence by matching each subject to its silhouette. | [`04_matching.md`](prompts/04_matching.md) |
| 5 | coloring | easy | 7-9 | Develops fine motor control and color choice while introducing a real place the child will visit. | [`05_coloring.md`](prompts/05_coloring.md) |
| 6 | maze | medium | 7-9 | Practises visual planning, sequencing and pencil control, and links two real locations from the trip. | [`06_maze.md`](prompts/06_maze.md) |
| 7 | word_search | medium | 7-9 | Builds letter recognition, spelling and systematic visual scanning, using vocabulary from the place the child is visiting. | [`07_word_search.md`](prompts/07_word_search.md) |
| 8 | spot_difference | medium | 7-9 | Sharpens visual discrimination and attention to detail through careful comparison of two scenes. | [`08_spot_difference.md`](prompts/08_spot_difference.md) |
| 9 | crossword | medium | 7-9 | Practises spelling, reading comprehension and inference — the child has to work out the answer from a clue and fit it to the letters already there. | [`09_crossword.md`](prompts/09_crossword.md) |
| 10 | packing | hard | 7-9 | Introduces planning and cause-and-effect: what the weather and the activities mean for what you carry. | [`10_packing.md`](prompts/10_packing.md) |
| 11 | quiz | hard | 8-10 | Consolidates what the child has learned about the destination and practises choosing between plausible options. | [`11_quiz.md`](prompts/11_quiz.md) |
| 12 | drawing | hard | 8-10 | Encourages observation and recall, and gives the child a page that is entirely their own work. | [`12_drawing.md`](prompts/12_drawing.md) |
| 13 | coloring | hard | 8-10 | Develops fine motor control and color choice while introducing a real place the child will visit. | [`13_coloring.md`](prompts/13_coloring.md) |
| 14 | reflection | easy | 6-8 | Consolidates memory of the trip and builds early metacognition — noticing what you enjoyed and what you learned. | [`14_reflection.md`](prompts/14_reflection.md) |

## Pages

### Page 1 — Noa and Amit's Big Trip to Kfar Hanokdim

| | |
| --- | --- |
| **Activity type** | `cover` |
| **Educational goal** | Builds anticipation for the trip and gives the child ownership of the book. |
| **Estimated age** | 6-8 |
| **Difficulty** | easy |
| **Prompt file** | [`prompts/01_cover.md`](prompts/01_cover.md) |

**Instructions for the child**

> This adventure book belongs to Noa and Amit. Write your name on the line, color the cover, and get ready to explore Kfar Hanokdim!

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
• Age-appropriate for a 7-9 year old: gentle and welcoming, nothing frightening, no weapons, no injuries
• Visually consistent with every other page of this book: a single coherent book about Kfar Hanokdim, same line weight, same simple horizon treatment and the same friendly character design on every page
• Recurring characters, drawn identically wherever they appear: two child explorers, about 7 and about 9 years old, with simple round friendly faces, practical outdoor clothes and small backpacks

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
  "focus": "wildlife",
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


### Page 2 — Find the Hidden Things

| | |
| --- | --- |
| **Activity type** | `hidden_objects` |
| **Educational goal** | Builds sustained visual search and vocabulary for local plants, animals and objects. |
| **Estimated age** | 6-8 |
| **Difficulty** | easy |
| **Prompt file** | [`prompts/02_hidden_objects.md`](prompts/02_hidden_objects.md) |

**Instructions for the child**

> 5 things are hiding in this picture of the Dead Sea shore: camels, Nubian ibex, hoopoe birds, labneh cheese with olive oil and goats and sheep. Circle each one as you find it.

**Required illustration**

A busy search-and-find scene at the Dead Sea shore.
A lively wide view of the Dead Sea shore at Kfar Hanokdim, full of nooks, foliage and small structures where objects can hide.
Must contain: camels, Nubian ibex, hoopoe birds, labneh cheese with olive oil, goats and sheep.
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

Layout:
One detailed full-page scene. Each hidden object is drawn completely and left partly visible — tucked behind or among scenery, never fully covered and never shrunk beyond easy recognition.

Style:
• Crisp black line art with high contrast and clear separation between elements, so the puzzle stays readable when printed small — no shading or textures that could be mistaken for part of the puzzle
• Friendly modern children's picture-book line art: rounded shapes, even line weight, simple expressive faces
• Clean, uncluttered composition — every element clearly separated and easy to recognise
• Age-appropriate for a 7-9 year old: gentle and welcoming, nothing frightening, no weapons, no injuries
• Visually consistent with every other page of this book: a single coherent book about Kfar Hanokdim, same line weight, same simple horizon treatment and the same friendly character design on every page
• Recurring characters, drawn identically wherever they appear: two child explorers, about 7 and about 9 years old, with simple round friendly faces, practical outdoor clothes and small backpacks

Constraints:
• Portrait A4 (210 x 297 mm), vertical orientation, 300 DPI
• Pure white background, generous margins, nothing important within 12 mm of the page edge
• No text, letters, numbers, captions, speech bubbles, watermarks or logos anywhere in the image
• Prints cleanly in black and white on a home printer
• Hide exactly these 5 objects, one of each: camels, Nubian ibex, hoopoe birds, labneh cheese with olive oil, goats and sheep
• Draw a small empty checkbox row along the bottom margin, one box per hidden object, with no text or numbers in them.
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "easy",
  "focus": "landmarks",
  "itinerary_day": "Arrival and camel yard",
  "scene": "the Dead Sea shore",
  "objects": [
    "camels",
    "Nubian ibex",
    "hoopoe birds",
    "labneh cheese with olive oil",
    "goats and sheep"
  ],
  "object_count": 5
}
```

</details>


### Page 3 — Amazing Animals of Kfar Hanokdim

| | |
| --- | --- |
| **Activity type** | `wildlife_facts` |
| **Educational goal** | Builds knowledge of local fauna and habitats, and encourages the child to look for real animals during the trip. |
| **Estimated age** | 6-8 |
| **Difficulty** | easy |
| **Prompt file** | [`prompts/03_wildlife_facts.md`](prompts/03_wildlife_facts.md) |

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
• Age-appropriate for a 7-9 year old: gentle and welcoming, nothing frightening, no weapons, no injuries
• Visually consistent with every other page of this book: a single coherent book about Kfar Hanokdim, same line weight, same simple horizon treatment and the same friendly character design on every page
• Recurring characters, drawn identically wherever they appear: two child explorers, about 7 and about 9 years old, with simple round friendly faces, practical outdoor clothes and small backpacks

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
  "focus": "activities",
  "itinerary_day": "Arrival and camel yard",
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


### Page 4 — Match the Shadows

| | |
| --- | --- |
| **Activity type** | `matching` |
| **Educational goal** | Trains shape recognition and one-to-one correspondence by matching each subject to its silhouette. |
| **Estimated age** | 6-8 |
| **Difficulty** | easy |
| **Prompt file** | [`prompts/04_matching.md`](prompts/04_matching.md) |

**Instructions for the child**

> Each animal on the left has a shadow on the right. Draw a line from every animal to its own shadow.

**Required illustration**

A matching puzzle of 4 subjects and their shadows.
Two vertical columns. The left column shows 4 outlined drawings from Kfar Hanokdim; the right column shows the same shapes as solid black silhouettes in a different order.
Must contain: goats and sheep, Nubian ibex, donkeys, hoopoe birds.
Render mode: `puzzle`.

**Image prompt**

```text
Create a black-and-white puzzle illustration for a children's travel activity book.

Scene:
Two vertical columns. The left column shows 4 outlined drawings from Kfar Hanokdim; the right column shows the same shapes as solid black silhouettes in a different order.

Include:
• goats and sheep
• Nubian ibex
• donkeys
• hoopoe birds

Layout:
Left column top-to-bottom: goats and sheep, Nubian ibex, donkeys, hoopoe birds. Right column top-to-bottom (silhouettes): hoopoe birds, donkeys, goats and sheep, Nubian ibex. Wide empty gutter between the columns for the child to draw lines.

Style:
• Crisp black line art with high contrast and clear separation between elements, so the puzzle stays readable when printed small — no shading or textures that could be mistaken for part of the puzzle
• Friendly modern children's picture-book line art: rounded shapes, even line weight, simple expressive faces
• Clean, uncluttered composition — every element clearly separated and easy to recognise
• Age-appropriate for a 7-9 year old: gentle and welcoming, nothing frightening, no weapons, no injuries
• Visually consistent with every other page of this book: a single coherent book about Kfar Hanokdim, same line weight, same simple horizon treatment and the same friendly character design on every page
• Recurring characters, drawn identically wherever they appear: two child explorers, about 7 and about 9 years old, with simple round friendly faces, practical outdoor clothes and small backpacks

Constraints:
• Portrait A4 (210 x 297 mm), vertical orientation, 300 DPI
• Pure white background, generous margins, nothing important within 12 mm of the page edge
• No text, letters, numbers, captions, speech bubbles, watermarks or logos anywhere in the image
• Prints cleanly in black and white on a home printer
• Each silhouette must be the exact outline of its partner, same pose and same size, filled solid black.
• No connecting lines, arrows, numbers or letters anywhere on the page.
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "easy",
  "focus": "plants",
  "itinerary_day": "Arrival and camel yard",
  "pair_count": 4,
  "left_column": [
    "goats and sheep",
    "Nubian ibex",
    "donkeys",
    "hoopoe birds"
  ],
  "right_column": [
    "hoopoe birds",
    "donkeys",
    "goats and sheep",
    "Nubian ibex"
  ],
  "answer_key": {
    "goats and sheep": 3,
    "Nubian ibex": 4,
    "donkeys": 2,
    "hoopoe birds": 1
  },
  "subject_kind": "animal"
}
```

</details>


### Page 5 — Color the Dead Sea shore

| | |
| --- | --- |
| **Activity type** | `coloring` |
| **Educational goal** | Develops fine motor control and color choice while introducing a real place the child will visit. |
| **Estimated age** | 7-9 |
| **Difficulty** | easy |
| **Prompt file** | [`prompts/05_coloring.md`](prompts/05_coloring.md) |

**Instructions for the child**

> Color this picture of the Dead Sea shore. Look closely for desert wildflowers after rain, date palms and camels — you may see them for real on your trip!

**Required illustration**

The Dead Sea shore.
the Dead Sea shore at Kfar Hanokdim, seen from a child's eye level, with plenty of large open areas to color.
Must contain: desert wildflowers after rain, date palms, camels, hoopoe birds.
Render mode: `coloring`.

**Image prompt**

```text
Create a black-and-white coloring page for a children's travel activity book.

Scene:
the Dead Sea shore at Kfar Hanokdim, seen from a child's eye level, with plenty of large open areas to color.

Include:
• desert wildflowers after rain
• date palms
• camels
• hoopoe birds

Layout:
Single full-page scene, very large shapes, few details, thick outlines.

Style:
• Bold, clean, uniform black outlines on white with large open areas to color — no shading, no hatching, no grey fills, no solid black areas
• Friendly modern children's picture-book line art: rounded shapes, even line weight, simple expressive faces
• Clean, uncluttered composition — every element clearly separated and easy to recognise
• Age-appropriate for a 7-9 year old: gentle and welcoming, nothing frightening, no weapons, no injuries
• Visually consistent with every other page of this book: a single coherent book about Kfar Hanokdim, same line weight, same simple horizon treatment and the same friendly character design on every page
• Recurring characters, drawn identically wherever they appear: two child explorers, about 7 and about 9 years old, with simple round friendly faces, practical outdoor clothes and small backpacks

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
  "focus": "local_food",
  "itinerary_day": "Arrival and camel yard",
  "subject": "the Dead Sea shore",
  "look_for": [
    "desert wildflowers after rain",
    "date palms",
    "camels"
  ],
  "knowledge_focus": "landmarks"
}
```

</details>


### Page 6 — The Path to the Nokdim valley lookout

| | |
| --- | --- |
| **Activity type** | `maze` |
| **Educational goal** | Practises visual planning, sequencing and pencil control, and links two real locations from the trip. |
| **Estimated age** | 7-9 |
| **Difficulty** | medium |
| **Prompt file** | [`prompts/06_maze.md`](prompts/06_maze.md) |

**Instructions for the child**

> Help Noa get from the Masada cliff fortress all the way to the Nokdim valley lookout. Draw one line through the maze without crossing any walls. Pick up dates from the palm trees and desert wildflowers after rain along the way.

**Required illustration**

A maze leading from the Masada cliff fortress to the Nokdim valley lookout.
A top-down maze puzzle. A small drawing of the Masada cliff fortress marks the entrance in the upper-left corner and a drawing of the Nokdim valley lookout marks the exit in the lower-right corner. The maze walls are decorated as Kfar Hanokdim scenery.
Must contain: dates from the palm trees, desert wildflowers after rain.
Render mode: `puzzle`.

**Image prompt**

```text
Create a black-and-white puzzle illustration for a children's travel activity book.

Scene:
A top-down maze puzzle. A small drawing of the Masada cliff fortress marks the entrance in the upper-left corner and a drawing of the Nokdim valley lookout marks the exit in the lower-right corner. The maze walls are decorated as Kfar Hanokdim scenery.

Include:
• dates from the palm trees
• desert wildflowers after rain

Layout:
A 9x9 maze filling the page, corridors wide enough for a chunky crayon, exactly one solvable path from entrance to exit.

Style:
• Crisp black line art with high contrast and clear separation between elements, so the puzzle stays readable when printed small — no shading or textures that could be mistaken for part of the puzzle
• Friendly modern children's picture-book line art: rounded shapes, even line weight, simple expressive faces
• Clean, uncluttered composition — every element clearly separated and easy to recognise
• Age-appropriate for a 7-9 year old: gentle and welcoming, nothing frightening, no weapons, no injuries
• Visually consistent with every other page of this book: a single coherent book about Kfar Hanokdim, same line weight, same simple horizon treatment and the same friendly character design on every page
• Recurring characters, drawn identically wherever they appear: two child explorers, about 7 and about 9 years old, with simple round friendly faces, practical outdoor clothes and small backpacks

Constraints:
• Portrait A4 (210 x 297 mm), vertical orientation, 300 DPI
• Pure white background, generous margins, nothing important within 12 mm of the page edge
• No text, letters, numbers, captions, speech bubbles, watermarks or logos anywhere in the image
• Prints cleanly in black and white on a home printer
• Maze walls must be solid, unbroken and clearly separated from the scenery.
• Exactly one correct route; no dead-end that touches the exit.
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "medium",
  "focus": "history",
  "itinerary_day": "Desert hike and Masada",
  "start": "the Masada cliff fortress",
  "goal": "the Nokdim valley lookout",
  "grid": {
    "rows": 9,
    "cols": 9
  },
  "collectibles": [
    "dates from the palm trees",
    "desert wildflowers after rain"
  ],
  "hero": "Noa"
}
```

</details>


### Page 7 — Kfar Hanokdim Word Search

| | |
| --- | --- |
| **Activity type** | `word_search` |
| **Educational goal** | Builds letter recognition, spelling and systematic visual scanning, using vocabulary from the place the child is visiting. |
| **Estimated age** | 7-9 |
| **Difficulty** | medium |
| **Prompt file** | [`prompts/07_word_search.md`](prompts/07_word_search.md) |

**Instructions for the child**

> 8 words from your trip are hiding in the grid — across, down and sometimes slanted. Find and circle each one: Acacia, Camels, Cardamom, Desert, Donkey, Goats, Grove and Lookout.

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
• Age-appropriate for a 7-9 year old: gentle and welcoming, nothing frightening, no weapons, no injuries
• Visually consistent with every other page of this book: a single coherent book about Kfar Hanokdim, same line weight, same simple horizon treatment and the same friendly character design on every page
• Recurring characters, drawn identically wherever they appear: two child explorers, about 7 and about 9 years old, with simple round friendly faces, practical outdoor clothes and small backpacks

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
  "focus": "interesting_facts",
  "itinerary_day": "Desert hike and Masada",
  "grid": [
    "LOOKOUTXGPQQ",
    "ZWYBROGROVEL",
    "ULZRBMRRZSVD",
    "MGJDOAXAXODE",
    "QNAZDZFTFUGS",
    "DIPCAMELSJOE",
    "OXTLHDMVNGAR",
    "SCARDAMOMBTT",
    "XOAFDONKEYSO",
    "IHLRXFFBQSBP",
    "DFMDPWNCEWEE",
    "GCACACIAAHZZ"
  ],
  "grid_size": 12,
  "words": [
    "ACACIA",
    "CAMELS",
    "CARDAMOM",
    "DESERT",
    "DONKEY",
    "GOATS",
    "GROVE",
    "LOOKOUT"
  ],
  "placements": [
    {
      "word": "ACACIA",
      "row": 11,
      "column": 2,
      "direction": [
        0,
        1
      ]
    },
    {
      "word": "CAMELS",
      "row": 5,
      "column": 3,
      "direction": [
        0,
        1
      ]
    },
    {
      "word": "CARDAMOM",
      "row": 7,
      "column": 1,
      "direction": [
        0,
        1
      ]
    },
    {
      "word": "DESERT",
      "row": 2,
      "column": 11,
      "direction": [
        1,
        0
      ]
    },
    {
      "word": "DONKEY",
      "row": 8,
      "column": 4,
      "direction": [
        0,
        1
      ]
    },
    {
      "word": "GOATS",
      "row": 4,
      "column": 10,
      "direction": [
        1,
        0
      ]
    },
    {
      "word": "GROVE",
      "row": 1,
      "column": 6,
      "direction": [
        0,
        1
      ]
    },
    {
      "word": "LOOKOUT",
      "row": 0,
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


### Page 8 — Spot the Differences

| | |
| --- | --- |
| **Activity type** | `spot_difference` |
| **Educational goal** | Sharpens visual discrimination and attention to detail through careful comparison of two scenes. |
| **Estimated age** | 7-9 |
| **Difficulty** | medium |
| **Prompt file** | [`prompts/08_spot_difference.md`](prompts/08_spot_difference.md) |

**Instructions for the child**

> These two pictures of rock hyraxes look the same — but 6 things are different. Circle every difference you find.

**Required illustration**

Two nearly identical scenes of rock hyraxes.
The same view of rock hyraxes at Kfar Hanokdim drawn twice: the top half is the original, the bottom half repeats it with small changes.
Must contain: dates from the palm trees, rock hyraxes, goats and sheep, sleeping in a Bedouin tent, hoopoe birds, hummus.
Render mode: `puzzle`.

**Image prompt**

```text
Create a black-and-white puzzle illustration for a children's travel activity book.

Scene:
The same view of rock hyraxes at Kfar Hanokdim drawn twice: the top half is the original, the bottom half repeats it with small changes.

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
• Age-appropriate for a 7-9 year old: gentle and welcoming, nothing frightening, no weapons, no injuries
• Visually consistent with every other page of this book: a single coherent book about Kfar Hanokdim, same line weight, same simple horizon treatment and the same friendly character design on every page
• Recurring characters, drawn identically wherever they appear: two child explorers, about 7 and about 9 years old, with simple round friendly faces, practical outdoor clothes and small backpacks

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
  "focus": "wildlife",
  "itinerary_day": "Desert hike and Masada",
  "subject": "rock hyraxes",
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


### Page 9 — The Kfar Hanokdim Crossword

| | |
| --- | --- |
| **Activity type** | `crossword` |
| **Educational goal** | Practises spelling, reading comprehension and inference — the child has to work out the answer from a clue and fit it to the letters already there. |
| **Estimated age** | 7-9 |
| **Difficulty** | medium |
| **Prompt file** | [`prompts/09_crossword.md`](prompts/09_crossword.md) |

**Instructions for the child**

> Read each clue and write the answer into the squares, one letter per square. There are 7 clues — the words cross each other, so a letter you already know can help with the next one.

**Required illustration**

A decorative border for a crossword page.
A thin decorative border of Kfar Hanokdim motifs framing an otherwise completely empty page.
Must contain: the big Bedouin hospitality tent, the Nokdim valley lookout.
Render mode: `frame`.

**Image prompt**

```text
Create a black-and-white activity page with a large empty drawing area for a children's travel activity book.

Scene:
A thin decorative border of Kfar Hanokdim motifs framing an otherwise completely empty page.

Include:
• the big Bedouin hospitality tent
• the Nokdim valley lookout

Layout:
Border only, no more than 15 mm wide. The centre of the page stays blank white — the crossword grid and clues are typeset there.

Style:
• Delicate black line art confined to the border, with the working area left completely blank white
• Friendly modern children's picture-book line art: rounded shapes, even line weight, simple expressive faces
• Clean, uncluttered composition — every element clearly separated and easy to recognise
• Age-appropriate for a 7-9 year old: gentle and welcoming, nothing frightening, no weapons, no injuries
• Visually consistent with every other page of this book: a single coherent book about Kfar Hanokdim, same line weight, same simple horizon treatment and the same friendly character design on every page
• Recurring characters, drawn identically wherever they appear: two child explorers, about 7 and about 9 years old, with simple round friendly faces, practical outdoor clothes and small backpacks

Constraints:
• Portrait A4 (210 x 297 mm), vertical orientation, 300 DPI
• Pure white background, generous margins, nothing important within 12 mm of the page edge
• No text, letters, numbers, captions, speech bubbles, watermarks or logos anywhere in the image
• Prints cleanly in black and white on a home printer
• Do not draw a grid, squares, numbers, letters or clues.
• This border is optional decoration; the page is complete without it.
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "medium",
  "focus": "landmarks",
  "itinerary_day": "Desert hike and Masada",
  "rows": 13,
  "columns": 8,
  "layout": [
    "####.###",
    "####.###",
    "####.#.#",
    "####.#.#",
    "#......#",
    "####.#.#",
    ".#.###.#",
    ".......#",
    ".#.###.#",
    ".#.#####",
    ".#.#####",
    ".#.#####",
    "#......."
  ],
  "solution": [
    "####A###",
    "####C###",
    "####A#S#",
    "####C#U#",
    "#NUBIAN#",
    "####A#R#",
    "S#G###I#",
    "HYRAXES#",
    "R#I###E#",
    "U#D#####",
    "B#D#####",
    "S#L#####",
    "#BEDOUIN"
  ],
  "numbers": [
    {
      "row": 0,
      "column": 4,
      "number": 1
    },
    {
      "row": 2,
      "column": 6,
      "number": 2
    },
    {
      "row": 4,
      "column": 1,
      "number": 3
    },
    {
      "row": 6,
      "column": 0,
      "number": 4
    },
    {
      "row": 6,
      "column": 2,
      "number": 5
    },
    {
      "row": 7,
      "column": 0,
      "number": 6
    },
    {
      "row": 12,
      "column": 1,
      "number": 7
    }
  ],
  "across": [
    {
      "number": 3,
      "clue": "___ ibex",
      "answer": "NUBIAN",
      "row": 4,
      "column": 1,
      "length": 6,
      "category": "wildlife"
    },
    {
      "number": 6,
      "clue": "Rock ___",
      "answer": "HYRAXES",
      "row": 7,
      "column": 0,
      "length": 7,
      "category": "wildlife"
    },
    {
      "number": 7,
      "clue": "The big ___ hospitality tent",
      "answer": "BEDOUIN",
      "row": 12,
      "column": 1,
      "length": 7,
      "category": "landmarks"
    }
  ],
  "down": [
    {
      "number": 1,
      "clue": "___ trees",
      "answer": "ACACIA",
      "row": 0,
      "column": 4,
      "length": 6,
      "category": "plants"
    },
    {
      "number": 2,
      "clue": "A desert hike at ___",
      "answer": "SUNRISE",
      "row": 2,
      "column": 6,
      "length": 7,
      "category": "activities"
    },
    {
      "number": 4,
      "clue": "White broom ___",
      "answer": "SHRUBS",
      "row": 6,
      "column": 0,
      "length": 6,
      "category": "plants"
    },
    {
      "number": 5,
      "clue": "Baking pita on a saj ___",
      "answer": "GRIDDLE",
      "row": 6,
      "column": 2,
      "length": 7,
      "category": "activities"
    }
  ],
  "clue_count": 7,
  "illustration": "decorative",
  "needs_illustration": false
}
```

</details>


### Page 10 — Pack Your Explorer Bag

| | |
| --- | --- |
| **Activity type** | `packing` |
| **Educational goal** | Introduces planning and cause-and-effect: what the weather and the activities mean for what you carry. |
| **Estimated age** | 7-9 |
| **Difficulty** | hard |
| **Prompt file** | [`prompts/10_packing.md`](prompts/10_packing.md) |

**Instructions for the child**

> You are going to Kfar Hanokdim! Tick the box next to everything you have packed, then draw one more thing you want to bring in the empty box.

**Required illustration**

An open explorer backpack surrounded by things to pack.
A friendly open backpack in the centre of the page with the items to pack for Kfar Hanokdim arranged around it in a neat grid.
Must contain: water bottle, comfortable shoes, small backpack, this activity book, pencils and crayons, snack, sun hat, sunscreen, sunglasses, warm coat, gloves, woolly hat.
Render mode: `coloring`.

**Image prompt**

```text
Create a black-and-white coloring page for a children's travel activity book.

Scene:
A friendly open backpack in the centre of the page with the items to pack for Kfar Hanokdim arranged around it in a neat grid.

Include:
• water bottle
• comfortable shoes
• small backpack
• this activity book
• pencils and crayons
• snack
• sun hat
• sunscreen
• sunglasses
• warm coat
• gloves
• woolly hat

Layout:
A grid of 13 equally sized cells. Each cell holds one clearly recognisable object drawing with an empty square checkbox beside it. The final cell is left completely empty for the child to draw in.

Style:
• Bold, clean, uniform black outlines on white with large open areas to color — no shading, no hatching, no grey fills, no solid black areas
• Friendly modern children's picture-book line art: rounded shapes, even line weight, simple expressive faces
• Clean, uncluttered composition — every element clearly separated and easy to recognise
• Age-appropriate for a 7-9 year old: gentle and welcoming, nothing frightening, no weapons, no injuries
• Visually consistent with every other page of this book: a single coherent book about Kfar Hanokdim, same line weight, same simple horizon treatment and the same friendly character design on every page
• Recurring characters, drawn identically wherever they appear: two child explorers, about 7 and about 9 years old, with simple round friendly faces, practical outdoor clothes and small backpacks

Constraints:
• Portrait A4 (210 x 297 mm), vertical orientation, 300 DPI
• Pure white background, generous margins, nothing important within 12 mm of the page edge
• No text, letters, numbers, captions, speech bubbles, watermarks or logos anywhere in the image
• Prints cleanly in black and white on a home printer
• Draw exactly these items, one per cell, in this order: water bottle, comfortable shoes, small backpack, this activity book, pencils and crayons, snack, sun hat, sunscreen, sunglasses, warm coat, gloves, woolly hat
• Checkboxes must be empty outlines — no ticks, no labels, no numbering.
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "hard",
  "focus": "activities",
  "itinerary_day": "Dead Sea day",
  "items": [
    "water bottle",
    "comfortable shoes",
    "small backpack",
    "this activity book",
    "pencils and crayons",
    "snack",
    "sun hat",
    "sunscreen",
    "sunglasses",
    "warm coat",
    "gloves",
    "woolly hat"
  ],
  "blank_slots": 1,
  "matched_conditions": [
    "hot_items",
    "cold_items",
    "rain_items",
    "hike_items",
    "water_items",
    "night_items",
    "wildlife_items"
  ]
}
```

</details>


### Page 11 — The Kfar Hanokdim Quiz

| | |
| --- | --- |
| **Activity type** | `quiz` |
| **Educational goal** | Consolidates what the child has learned about the destination and practises choosing between plausible options. |
| **Estimated age** | 8-10 |
| **Difficulty** | hard |
| **Prompt file** | [`prompts/11_quiz.md`](prompts/11_quiz.md) |

**Instructions for the child**

> Circle the answer you think is right. There are 5 questions — ask a grown-up if you get stuck.

**Required illustration**

A picture quiz sheet with 5 questions.
A quiz page about Kfar Hanokdim. Each row offers three small drawings to choose between, with an empty circle under each one.
Must contain: toucan, goats and sheep, polar bear, an ice castle, a pirate ship, the camel yard, cardamom coffee, rainbow soup, moon cheese, riding a dinosaur, riding a camel, swimming to the moon, camels.
Render mode: `puzzle`.

**Image prompt**

```text
Create a black-and-white puzzle illustration for a children's travel activity book.

Scene:
A quiz page about Kfar Hanokdim. Each row offers three small drawings to choose between, with an empty circle under each one.

Include:
• toucan
• goats and sheep
• polar bear
• an ice castle
• a pirate ship
• the camel yard
• cardamom coffee
• rainbow soup
• moon cheese
• riding a dinosaur
• riding a camel
• swimming to the moon
• camels

Layout:
5 rows stacked down the page. Each row has a blank strip at the top for the question, then three equally sized option drawings side by side, each with an empty circle beneath it.

Style:
• Crisp black line art with high contrast and clear separation between elements, so the puzzle stays readable when printed small — no shading or textures that could be mistaken for part of the puzzle
• Friendly modern children's picture-book line art: rounded shapes, even line weight, simple expressive faces
• Clean, uncluttered composition — every element clearly separated and easy to recognise
• Age-appropriate for a 7-9 year old: gentle and welcoming, nothing frightening, no weapons, no injuries
• Visually consistent with every other page of this book: a single coherent book about Kfar Hanokdim, same line weight, same simple horizon treatment and the same friendly character design on every page
• Recurring characters, drawn identically wherever they appear: two child explorers, about 7 and about 9 years old, with simple round friendly faces, practical outdoor clothes and small backpacks

Constraints:
• Portrait A4 (210 x 297 mm), vertical orientation, 300 DPI
• Pure white background, generous margins, nothing important within 12 mm of the page edge
• No text, letters, numbers, captions, speech bubbles, watermarks or logos anywhere in the image
• Prints cleanly in black and white on a home printer
• Question 1 options: toucan, goats and sheep, polar bear
• Question 2 options: an ice castle, a pirate ship, the camel yard
• Question 3 options: cardamom coffee, rainbow soup, moon cheese
• Question 4 options: riding a dinosaur, riding a camel, swimming to the moon
• Question 5 options: toucan, polar bear, camels
• Leave the question strips completely blank — the text is added later.
• Do not mark, tick or highlight the correct answer in any way.
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "hard",
  "focus": "plants",
  "itinerary_day": "Dead Sea day",
  "questions": [
    {
      "question": "Which animal can you meet at Kfar Hanokdim?",
      "options": [
        "toucan",
        "goats and sheep",
        "polar bear"
      ],
      "answer": "goats and sheep",
      "answer_index": 2,
      "category": "wildlife"
    },
    {
      "question": "Which of these can you visit at Kfar Hanokdim?",
      "options": [
        "an ice castle",
        "a pirate ship",
        "the camel yard"
      ],
      "answer": "the camel yard",
      "answer_index": 3,
      "category": "landmarks"
    },
    {
      "question": "Which of these is a local food at Kfar Hanokdim?",
      "options": [
        "cardamom coffee",
        "rainbow soup",
        "moon cheese"
      ],
      "answer": "cardamom coffee",
      "answer_index": 1,
      "category": "local_food"
    },
    {
      "question": "Which of these can you do at Kfar Hanokdim?",
      "options": [
        "riding a dinosaur",
        "riding a camel",
        "swimming to the moon"
      ],
      "answer": "riding a camel",
      "answer_index": 2,
      "category": "activities"
    },
    {
      "question": "Which animal can you meet at Kfar Hanokdim?",
      "options": [
        "toucan",
        "polar bear",
        "camels"
      ],
      "answer": "camels",
      "answer_index": 3,
      "category": "wildlife"
    }
  ],
  "question_count": 5
}
```

</details>


### Page 12 — Draw What You Saw

| | |
| --- | --- |
| **Activity type** | `drawing` |
| **Educational goal** | Encourages observation and recall, and gives the child a page that is entirely their own work. |
| **Estimated age** | 8-10 |
| **Difficulty** | hard |
| **Prompt file** | [`prompts/12_drawing.md`](prompts/12_drawing.md) |

**Instructions for the child**

> Draw what you remember about fresh pita from the saj inside the frame — the way *you* saw it. Add as many small details as you can.

**Required illustration**

An empty drawing frame decorated with local motifs.
A large empty rectangular frame with a decorative border of Kfar Hanokdim motifs woven around its edges.
Must contain: acacia trees, desert wildflowers after rain, desert lizards, Nubian ibex.
Render mode: `frame`.

**Image prompt**

```text
Create a black-and-white activity page with a large empty drawing area for a children's travel activity book.

Scene:
A large empty rectangular frame with a decorative border of Kfar Hanokdim motifs woven around its edges.

Include:
• acacia trees
• desert wildflowers after rain
• desert lizards
• Nubian ibex

Layout:
The frame occupies about 80% of the page and its interior is completely blank white. Only the border carries decoration.

Style:
• Delicate black line art confined to the border, with the working area left completely blank white
• Friendly modern children's picture-book line art: rounded shapes, even line weight, simple expressive faces
• Clean, uncluttered composition — every element clearly separated and easy to recognise
• Age-appropriate for a 7-9 year old: gentle and welcoming, nothing frightening, no weapons, no injuries
• Visually consistent with every other page of this book: a single coherent book about Kfar Hanokdim, same line weight, same simple horizon treatment and the same friendly character design on every page
• Recurring characters, drawn identically wherever they appear: two child explorers, about 7 and about 9 years old, with simple round friendly faces, practical outdoor clothes and small backpacks

Constraints:
• Portrait A4 (210 x 297 mm), vertical orientation, 300 DPI
• Pure white background, generous margins, nothing important within 12 mm of the page edge
• No text, letters, numbers, captions, speech bubbles, watermarks or logos anywhere in the image
• Prints cleanly in black and white on a home printer
• The inside of the frame must be pure white — no scenery, no guide lines, no faint shapes of any kind.
• Keep the border decoration thin so it never intrudes on the drawing area.
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "hard",
  "focus": "local_food",
  "itinerary_day": "Dead Sea day",
  "prompt_subject": "fresh pita from the saj",
  "border_motifs": [
    "acacia trees",
    "desert wildflowers after rain",
    "desert lizards",
    "Nubian ibex"
  ],
  "blank_page": true
}
```

</details>


### Page 13 — Color the Dead Sea shore

| | |
| --- | --- |
| **Activity type** | `coloring` |
| **Educational goal** | Develops fine motor control and color choice while introducing a real place the child will visit. |
| **Estimated age** | 8-10 |
| **Difficulty** | hard |
| **Prompt file** | [`prompts/13_coloring.md`](prompts/13_coloring.md) |

**Instructions for the child**

> Color this picture of the Dead Sea shore. Look closely for desert wildflowers after rain, white broom shrubs and rock hyraxes — you may see them for real on your trip!

**Required illustration**

The Dead Sea shore.
the Dead Sea shore at Kfar Hanokdim, seen from a child's eye level, with plenty of large open areas to color.
Must contain: desert wildflowers after rain, white broom shrubs, rock hyraxes, donkeys.
Render mode: `coloring`.

**Image prompt**

```text
Create a black-and-white coloring page for a children's travel activity book.

Scene:
the Dead Sea shore at Kfar Hanokdim, seen from a child's eye level, with plenty of large open areas to color.

Include:
• desert wildflowers after rain
• white broom shrubs
• rock hyraxes
• donkeys

Layout:
Single full-page scene, more detailed scene with layered background elements.

Style:
• Bold, clean, uniform black outlines on white with large open areas to color — no shading, no hatching, no grey fills, no solid black areas
• Friendly modern children's picture-book line art: rounded shapes, even line weight, simple expressive faces
• Clean, uncluttered composition — every element clearly separated and easy to recognise
• Age-appropriate for a 7-9 year old: gentle and welcoming, nothing frightening, no weapons, no injuries
• Visually consistent with every other page of this book: a single coherent book about Kfar Hanokdim, same line weight, same simple horizon treatment and the same friendly character design on every page
• Recurring characters, drawn identically wherever they appear: two child explorers, about 7 and about 9 years old, with simple round friendly faces, practical outdoor clothes and small backpacks

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
  "difficulty": "hard",
  "focus": "history",
  "itinerary_day": "Dead Sea day",
  "subject": "the Dead Sea shore",
  "look_for": [
    "desert wildflowers after rain",
    "white broom shrubs",
    "rock hyraxes"
  ],
  "knowledge_focus": "landmarks"
}
```

</details>


### Page 14 — My Kfar Hanokdim Memories

| | |
| --- | --- |
| **Activity type** | `reflection` |
| **Educational goal** | Consolidates memory of the trip and builds early metacognition — noticing what you enjoyed and what you learned. |
| **Estimated age** | 6-8 |
| **Difficulty** | easy |
| **Prompt file** | [`prompts/14_reflection.md`](prompts/14_reflection.md) |

**Instructions for the child**

> Your trip is nearly over! Draw or write your favorite moment, answer the questions, and color one star for every day you had fun.

**Required illustration**

A keepsake page with an empty memory frame and blank writing lines.
A calm, warm closing page for a trip to Kfar Hanokdim: a large empty frame for a drawing, blank ruled lines beneath it, and a row of outlined stars along the bottom.
Must contain: the Masada cliff fortress, goats and sheep.
Render mode: `frame`.

**Image prompt**

```text
Create a black-and-white activity page with a large empty drawing area for a children's travel activity book.

Scene:
A calm, warm closing page for a trip to Kfar Hanokdim: a large empty frame for a drawing, blank ruled lines beneath it, and a row of outlined stars along the bottom.

Include:
• the Masada cliff fortress
• goats and sheep

Layout:
Top half: one large empty frame. Middle: 4 groups of two blank ruled lines each. Bottom: a row of 3 evenly spaced star outlines. Small motifs only in the margins.

Style:
• Delicate black line art confined to the border, with the working area left completely blank white
• Friendly modern children's picture-book line art: rounded shapes, even line weight, simple expressive faces
• Clean, uncluttered composition — every element clearly separated and easy to recognise
• Age-appropriate for a 7-9 year old: gentle and welcoming, nothing frightening, no weapons, no injuries
• Visually consistent with every other page of this book: a single coherent book about Kfar Hanokdim, same line weight, same simple horizon treatment and the same friendly character design on every page
• Recurring characters, drawn identically wherever they appear: two child explorers, about 7 and about 9 years old, with simple round friendly faces, practical outdoor clothes and small backpacks

Constraints:
• Portrait A4 (210 x 297 mm), vertical orientation, 300 DPI
• Pure white background, generous margins, nothing important within 12 mm of the page edge
• No text, letters, numbers, captions, speech bubbles, watermarks or logos anywhere in the image
• Prints cleanly in black and white on a home printer
• Frame interior and all ruled lines must be completely empty.
• Stars must be plain outlines, unfilled and unnumbered.
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "easy",
  "focus": "interesting_facts",
  "prompts": [
    "The best thing I saw was...",
    "Something new I learned was...",
    "Next time I want to...",
    "The food I liked most was..."
  ],
  "writing_lines": 8,
  "stars": 3,
  "closing_page": true
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
