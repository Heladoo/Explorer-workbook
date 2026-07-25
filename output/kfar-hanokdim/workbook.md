# Noa and Amit's Kfar Hanokdim Adventure Book

*An activity book for young explorers*

| Field | Value |
| --- | --- |
| Destination | Kfar Hanokdim |
| Language | en |
| Pages | 12 |
| Made for | Noa (5), Amit (7) |
| Trip | 3 day(s), itinerary: Arrival and camel yard; Desert hike and Masada; Dead Sea day |
| Special interests | animals |
| Knowledge source | file |
| Generated | 2026-07-25T20:05:55+00:00 |


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
| 2 | hidden_objects | easy | 4-6 | Builds sustained visual search and vocabulary for local plants, animals and objects. | [`02_hidden_objects.md`](prompts/02_hidden_objects.md) |
| 3 | wildlife_facts | easy | 4-6 | Builds knowledge of local fauna and habitats, and encourages the child to look for real animals during the trip. | [`03_wildlife_facts.md`](prompts/03_wildlife_facts.md) |
| 4 | matching | easy | 4-6 | Trains shape recognition and one-to-one correspondence by matching each subject to its silhouette. | [`04_matching.md`](prompts/04_matching.md) |
| 5 | coloring | medium | 5-7 | Develops fine motor control and color choice while introducing a real place the child will visit. | [`05_coloring.md`](prompts/05_coloring.md) |
| 6 | maze | medium | 5-7 | Practises visual planning, sequencing and pencil control, and links two real locations from the trip. | [`06_maze.md`](prompts/06_maze.md) |
| 7 | packing | medium | 5-7 | Introduces planning and cause-and-effect: what the weather and the activities mean for what you carry. | [`07_packing.md`](prompts/07_packing.md) |
| 8 | spot_difference | medium | 5-7 | Sharpens visual discrimination and attention to detail through careful comparison of two scenes. | [`08_spot_difference.md`](prompts/08_spot_difference.md) |
| 9 | quiz | medium | 6-8 | Consolidates what the child has learned about the destination and practises choosing between plausible options. | [`09_quiz.md`](prompts/09_quiz.md) |
| 10 | drawing | medium | 6-8 | Encourages observation and recall, and gives the child a page that is entirely their own work. | [`10_drawing.md`](prompts/10_drawing.md) |
| 11 | coloring | medium | 6-8 | Develops fine motor control and color choice while introducing a real place the child will visit. | [`11_coloring.md`](prompts/11_coloring.md) |
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

> This adventure book belongs to Noa and Amit. Write your name on the line, color the cover, and get ready to explore Kfar Hanokdim!

**Required illustration**

A welcoming cover scene of the Masada cliff fortress.
A cheerful establishing view of Kfar Hanokdim, with the Masada cliff fortress as the centrepiece and children setting off to explore.
Must contain: 2 happy children with small backpacks, the Masada cliff fortress, the date palm grove, camels, desert wildflowers after rain.
Render mode: `coloring`.

**Image prompt**

```text
Create a black-and-white coloring page for a children's travel activity book.

Scene:
A cheerful establishing view of Kfar Hanokdim, with the Masada cliff fortress as the centrepiece and children setting off to explore.

Include:
• 2 happy children with small backpacks
• the Masada cliff fortress
• the date palm grove
• camels
• desert wildflowers after rain

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
| **Estimated age** | 4-6 |
| **Difficulty** | easy |
| **Prompt file** | [`prompts/02_hidden_objects.md`](prompts/02_hidden_objects.md) |

**Instructions for the child**

> 5 things are hiding in this picture of the Masada cliff fortress: rock hyraxes, hoopoe birds, desert lizards, labneh cheese with olive oil and donkeys. Circle each one as you find it.

**Required illustration**

A busy search-and-find scene at the Masada cliff fortress.
A lively wide view of the Masada cliff fortress at Kfar Hanokdim, full of nooks, foliage and small structures where objects can hide.
Must contain: rock hyraxes, hoopoe birds, desert lizards, labneh cheese with olive oil, donkeys.
Render mode: `puzzle`.

**Image prompt**

```text
Create a black-and-white puzzle illustration for a children's travel activity book.

Scene:
A lively wide view of the Masada cliff fortress at Kfar Hanokdim, full of nooks, foliage and small structures where objects can hide.

Include:
• rock hyraxes
• hoopoe birds
• desert lizards
• labneh cheese with olive oil
• donkeys

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
• Hide exactly these 5 objects, one of each: rock hyraxes, hoopoe birds, desert lizards, labneh cheese with olive oil, donkeys
• Draw a small empty checkbox row along the bottom margin, one box per hidden object, with no text or numbers in them.
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "easy",
  "focus": "landmarks",
  "itinerary_day": "Arrival and camel yard",
  "scene": "the Masada cliff fortress",
  "objects": [
    "rock hyraxes",
    "hoopoe birds",
    "desert lizards",
    "labneh cheese with olive oil",
    "donkeys"
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
| **Estimated age** | 4-6 |
| **Difficulty** | easy |
| **Prompt file** | [`prompts/03_wildlife_facts.md`](prompts/03_wildlife_facts.md) |

**Instructions for the child**

> Meet 3 animals that live around Kfar Hanokdim. Color each one, then put a star next to the animal you would most like to see.

**Required illustration**

A fact card sheet of 3 animals from Kfar Hanokdim.
A page of equally sized cards, each holding one animal drawn accurately and clearly in its natural surroundings.
Must contain: rock hyraxes, goats and sheep, hoopoe birds.
Render mode: `illustration`.

**Image prompt**

```text
Create a black-and-white illustrated information page for a children's travel activity book.

Scene:
A page of equally sized cards, each holding one animal drawn accurately and clearly in its natural surroundings.

Include:
• rock hyraxes
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
• Draw the animals in this order, one per card: rock hyraxes, goats and sheep, hoopoe birds
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
    "rock hyraxes",
    "goats and sheep",
    "hoopoe birds"
  ],
  "cards": [
    {
      "animal": "rock hyraxes",
      "caption": "rock hyraxes — look for one near the Nokdim valley lookout."
    },
    {
      "animal": "goats and sheep",
      "caption": "goats and sheep — look for one near the Dead Sea shore."
    },
    {
      "animal": "hoopoe birds",
      "caption": "hoopoe birds — look for one near the Masada cliff fortress."
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
| **Estimated age** | 4-6 |
| **Difficulty** | easy |
| **Prompt file** | [`prompts/04_matching.md`](prompts/04_matching.md) |

**Instructions for the child**

> Each animal on the left has a shadow on the right. Draw a line from every animal to its own shadow.

**Required illustration**

A matching puzzle of 4 subjects and their shadows.
Two vertical columns. The left column shows 4 outlined drawings from Kfar Hanokdim; the right column shows the same shapes as solid black silhouettes in a different order.
Must contain: donkeys, Nubian ibex, goats and sheep, desert lizards.
Render mode: `puzzle`.

**Image prompt**

```text
Create a black-and-white puzzle illustration for a children's travel activity book.

Scene:
Two vertical columns. The left column shows 4 outlined drawings from Kfar Hanokdim; the right column shows the same shapes as solid black silhouettes in a different order.

Include:
• donkeys
• Nubian ibex
• goats and sheep
• desert lizards

Layout:
Left column top-to-bottom: donkeys, Nubian ibex, goats and sheep, desert lizards. Right column top-to-bottom (silhouettes): donkeys, Nubian ibex, goats and sheep, desert lizards. Wide empty gutter between the columns for the child to draw lines.

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
    "donkeys",
    "Nubian ibex",
    "goats and sheep",
    "desert lizards"
  ],
  "right_column": [
    "donkeys",
    "Nubian ibex",
    "goats and sheep",
    "desert lizards"
  ],
  "answer_key": {
    "donkeys": 1,
    "Nubian ibex": 2,
    "goats and sheep": 3,
    "desert lizards": 4
  },
  "subject_kind": "animal"
}
```

</details>


### Page 5 — Color the big Bedouin hospitality tent

| | |
| --- | --- |
| **Activity type** | `coloring` |
| **Educational goal** | Develops fine motor control and color choice while introducing a real place the child will visit. |
| **Estimated age** | 5-7 |
| **Difficulty** | medium |
| **Prompt file** | [`prompts/05_coloring.md`](prompts/05_coloring.md) |

**Instructions for the child**

> Color this picture of the big Bedouin hospitality tent. Look closely for tamarisk bushes, date palms and rock hyraxes — you may see them for real on your trip!

**Required illustration**

The big Bedouin hospitality tent.
the big Bedouin hospitality tent at Kfar Hanokdim, seen from a child's eye level, with plenty of large open areas to color.
Must contain: tamarisk bushes, date palms, rock hyraxes, desert lizards.
Render mode: `coloring`.

**Image prompt**

```text
Create a black-and-white coloring page for a children's travel activity book.

Scene:
the big Bedouin hospitality tent at Kfar Hanokdim, seen from a child's eye level, with plenty of large open areas to color.

Include:
• tamarisk bushes
• date palms
• rock hyraxes
• desert lizards

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
  "focus": "local_food",
  "itinerary_day": "Arrival and camel yard",
  "subject": "the big Bedouin hospitality tent",
  "look_for": [
    "tamarisk bushes",
    "date palms",
    "rock hyraxes"
  ],
  "knowledge_focus": "landmarks"
}
```

</details>


### Page 6 — The Path to the camel yard

| | |
| --- | --- |
| **Activity type** | `maze` |
| **Educational goal** | Practises visual planning, sequencing and pencil control, and links two real locations from the trip. |
| **Estimated age** | 5-7 |
| **Difficulty** | medium |
| **Prompt file** | [`prompts/06_maze.md`](prompts/06_maze.md) |

**Instructions for the child**

> Help Noa get from the big Bedouin hospitality tent all the way to the camel yard. Draw one line through the maze without crossing any walls. Pick up fresh pita from the saj and acacia trees along the way.

**Required illustration**

A maze leading from the big Bedouin hospitality tent to the camel yard.
A top-down maze puzzle. A small drawing of the big Bedouin hospitality tent marks the entrance in the upper-left corner and a drawing of the camel yard marks the exit in the lower-right corner. The maze walls are decorated as Kfar Hanokdim scenery.
Must contain: fresh pita from the saj, acacia trees.
Render mode: `puzzle`.

**Image prompt**

```text
Create a black-and-white puzzle illustration for a children's travel activity book.

Scene:
A top-down maze puzzle. A small drawing of the big Bedouin hospitality tent marks the entrance in the upper-left corner and a drawing of the camel yard marks the exit in the lower-right corner. The maze walls are decorated as Kfar Hanokdim scenery.

Include:
• fresh pita from the saj
• acacia trees

Layout:
A 9x9 maze filling the page, corridors wide enough for a chunky crayon, exactly one solvable path from entrance to exit.

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
  "start": "the big Bedouin hospitality tent",
  "goal": "the camel yard",
  "grid": {
    "rows": 9,
    "cols": 9
  },
  "collectibles": [
    "fresh pita from the saj",
    "acacia trees"
  ],
  "hero": "Noa"
}
```

</details>


### Page 7 — Pack Your Explorer Bag

| | |
| --- | --- |
| **Activity type** | `packing` |
| **Educational goal** | Introduces planning and cause-and-effect: what the weather and the activities mean for what you carry. |
| **Estimated age** | 5-7 |
| **Difficulty** | medium |
| **Prompt file** | [`prompts/07_packing.md`](prompts/07_packing.md) |

**Instructions for the child**

> You are going to Kfar Hanokdim! Tick the box next to everything you have packed, then draw one more thing you want to bring in the empty box.

**Required illustration**

An open explorer backpack surrounded by things to pack.
A friendly open backpack in the centre of the page with the items to pack for Kfar Hanokdim arranged around it in a neat grid.
Must contain: water bottle, comfortable shoes, small backpack, this activity book, pencils and crayons, snack, sun hat, sunscreen, sunglasses, warm coat.
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

Layout:
A grid of 11 equally sized cells. Each cell holds one clearly recognisable object drawing with an empty square checkbox beside it. The final cell is left completely empty for the child to draw in.

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
• Draw exactly these items, one per cell, in this order: water bottle, comfortable shoes, small backpack, this activity book, pencils and crayons, snack, sun hat, sunscreen, sunglasses, warm coat
• Checkboxes must be empty outlines — no ticks, no labels, no numbering.
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "medium",
  "focus": "interesting_facts",
  "itinerary_day": "Desert hike and Masada",
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
    "warm coat"
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


### Page 8 — Spot the Differences

| | |
| --- | --- |
| **Activity type** | `spot_difference` |
| **Educational goal** | Sharpens visual discrimination and attention to detail through careful comparison of two scenes. |
| **Estimated age** | 5-7 |
| **Difficulty** | medium |
| **Prompt file** | [`prompts/08_spot_difference.md`](prompts/08_spot_difference.md) |

**Instructions for the child**

> These two pictures of goats and sheep look the same — but 6 things are different. Circle every difference you find.

**Required illustration**

Two nearly identical scenes of goats and sheep.
The same view of goats and sheep at Kfar Hanokdim drawn twice: the top half is the original, the bottom half repeats it with small changes.
Must contain: labneh cheese with olive oil, goats and sheep, desert lizards, a desert hike at sunrise, rock hyraxes, sweet tea with na'ana mint.
Render mode: `puzzle`.

**Image prompt**

```text
Create a black-and-white puzzle illustration for a children's travel activity book.

Scene:
The same view of goats and sheep at Kfar Hanokdim drawn twice: the top half is the original, the bottom half repeats it with small changes.

Include:
• labneh cheese with olive oil
• goats and sheep
• desert lizards
• a desert hike at sunrise
• rock hyraxes
• sweet tea with na'ana mint

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
• Introduce exactly 6 differences between the two panels: missing — labneh cheese with olive oil; extra — goats and sheep; moved — desert lizards; resized — a desert hike at sunrise; missing — rock hyraxes; extra — sweet tea with na'ana mint
• Everything not listed as a difference must be pixel-for-pixel identical.
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "medium",
  "focus": "wildlife",
  "itinerary_day": "Desert hike and Masada",
  "subject": "goats and sheep",
  "difference_count": 6,
  "differences": [
    {
      "item": "labneh cheese with olive oil",
      "kind": "missing",
      "description": "labneh cheese with olive oil is missing from the second picture"
    },
    {
      "item": "goats and sheep",
      "kind": "extra",
      "description": "an extra goats and sheep appears in the second picture"
    },
    {
      "item": "desert lizards",
      "kind": "moved",
      "description": "desert lizards has moved to the other side"
    },
    {
      "item": "a desert hike at sunrise",
      "kind": "resized",
      "description": "a desert hike at sunrise is a different size"
    },
    {
      "item": "rock hyraxes",
      "kind": "missing",
      "description": "rock hyraxes is missing from the second picture"
    },
    {
      "item": "sweet tea with na'ana mint",
      "kind": "extra",
      "description": "an extra sweet tea with na'ana mint appears in the second picture"
    }
  ]
}
```

</details>


### Page 9 — The Kfar Hanokdim Quiz

| | |
| --- | --- |
| **Activity type** | `quiz` |
| **Educational goal** | Consolidates what the child has learned about the destination and practises choosing between plausible options. |
| **Estimated age** | 6-8 |
| **Difficulty** | medium |
| **Prompt file** | [`prompts/09_quiz.md`](prompts/09_quiz.md) |

**Instructions for the child**

> Circle the answer you think is right. There are 4 questions — ask a grown-up if you get stuck.

**Required illustration**

A picture quiz sheet with 4 questions.
A quiz page about Kfar Hanokdim. Each row offers three small drawings to choose between, with an empty circle under each one.
Must contain: toucan, donkeys, polar bear, an ice castle, a pirate ship, the big Bedouin hospitality tent, sweet tea with na'ana mint, rainbow soup, moon cheese, riding a dinosaur, sleeping in a Bedouin tent, swimming to the moon.
Render mode: `puzzle`.

**Image prompt**

```text
Create a black-and-white puzzle illustration for a children's travel activity book.

Scene:
A quiz page about Kfar Hanokdim. Each row offers three small drawings to choose between, with an empty circle under each one.

Include:
• toucan
• donkeys
• polar bear
• an ice castle
• a pirate ship
• the big Bedouin hospitality tent
• sweet tea with na'ana mint
• rainbow soup
• moon cheese
• riding a dinosaur
• sleeping in a Bedouin tent
• swimming to the moon

Layout:
4 rows stacked down the page. Each row has a blank strip at the top for the question, then three equally sized option drawings side by side, each with an empty circle beneath it.

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
• Question 1 options: toucan, donkeys, polar bear
• Question 2 options: an ice castle, a pirate ship, the big Bedouin hospitality tent
• Question 3 options: sweet tea with na'ana mint, rainbow soup, moon cheese
• Question 4 options: riding a dinosaur, sleeping in a Bedouin tent, swimming to the moon
• Leave the question strips completely blank — the text is added later.
• Do not mark, tick or highlight the correct answer in any way.
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "medium",
  "focus": "landmarks",
  "itinerary_day": "Dead Sea day",
  "questions": [
    {
      "question": "Which animal can you meet at Kfar Hanokdim?",
      "options": [
        "toucan",
        "donkeys",
        "polar bear"
      ],
      "answer": "donkeys",
      "answer_index": 2,
      "category": "wildlife"
    },
    {
      "question": "Which of these can you visit at Kfar Hanokdim?",
      "options": [
        "an ice castle",
        "a pirate ship",
        "the big Bedouin hospitality tent"
      ],
      "answer": "the big Bedouin hospitality tent",
      "answer_index": 3,
      "category": "landmarks"
    },
    {
      "question": "Which of these is a local food at Kfar Hanokdim?",
      "options": [
        "sweet tea with na'ana mint",
        "rainbow soup",
        "moon cheese"
      ],
      "answer": "sweet tea with na'ana mint",
      "answer_index": 1,
      "category": "local_food"
    },
    {
      "question": "Which of these can you do at Kfar Hanokdim?",
      "options": [
        "riding a dinosaur",
        "sleeping in a Bedouin tent",
        "swimming to the moon"
      ],
      "answer": "sleeping in a Bedouin tent",
      "answer_index": 2,
      "category": "activities"
    }
  ],
  "question_count": 4
}
```

</details>


### Page 10 — Draw What You Saw

| | |
| --- | --- |
| **Activity type** | `drawing` |
| **Educational goal** | Encourages observation and recall, and gives the child a page that is entirely their own work. |
| **Estimated age** | 6-8 |
| **Difficulty** | medium |
| **Prompt file** | [`prompts/10_drawing.md`](prompts/10_drawing.md) |

**Instructions for the child**

> Draw what you remember about baking pita on a saj griddle inside the frame — the way *you* saw it. Add as many small details as you can.

**Required illustration**

An empty drawing frame decorated with local motifs.
A large empty rectangular frame with a decorative border of Kfar Hanokdim motifs woven around its edges.
Must contain: date palms, tamarisk bushes, camels, hoopoe birds.
Render mode: `frame`.

**Image prompt**

```text
Create a black-and-white activity page with a large empty drawing area for a children's travel activity book.

Scene:
A large empty rectangular frame with a decorative border of Kfar Hanokdim motifs woven around its edges.

Include:
• date palms
• tamarisk bushes
• camels
• hoopoe birds

Layout:
The frame occupies about 80% of the page and its interior is completely blank white. Only the border carries decoration.

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
• The inside of the frame must be pure white — no scenery, no guide lines, no faint shapes of any kind.
• Keep the border decoration thin so it never intrudes on the drawing area.
```

<details>
<summary>Page data for the layout stage</summary>

```json
{
  "difficulty": "medium",
  "focus": "activities",
  "itinerary_day": "Dead Sea day",
  "prompt_subject": "baking pita on a saj griddle",
  "border_motifs": [
    "date palms",
    "tamarisk bushes",
    "camels",
    "hoopoe birds"
  ],
  "blank_page": true
}
```

</details>


### Page 11 — Color tamarisk bushes

| | |
| --- | --- |
| **Activity type** | `coloring` |
| **Educational goal** | Develops fine motor control and color choice while introducing a real place the child will visit. |
| **Estimated age** | 6-8 |
| **Difficulty** | medium |
| **Prompt file** | [`prompts/11_coloring.md`](prompts/11_coloring.md) |

**Instructions for the child**

> Color this picture of tamarisk bushes. Look closely for tamarisk bushes, date palms and rock hyraxes — you may see them for real on your trip!

**Required illustration**

Tamarisk bushes.
tamarisk bushes at Kfar Hanokdim, seen from a child's eye level, with plenty of large open areas to color.
Must contain: tamarisk bushes, date palms, rock hyraxes, desert lizards.
Render mode: `coloring`.

**Image prompt**

```text
Create a black-and-white coloring page for a children's travel activity book.

Scene:
tamarisk bushes at Kfar Hanokdim, seen from a child's eye level, with plenty of large open areas to color.

Include:
• tamarisk bushes
• date palms
• rock hyraxes
• desert lizards

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
  "itinerary_day": "Dead Sea day",
  "subject": "tamarisk bushes",
  "look_for": [
    "tamarisk bushes",
    "date palms",
    "rock hyraxes"
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
| **Prompt file** | [`prompts/12_reflection.md`](prompts/12_reflection.md) |

**Instructions for the child**

> Your trip is nearly over! Draw or write your favorite moment, answer the questions, and color one star for every day you had fun.

**Required illustration**

A keepsake page with an empty memory frame and blank writing lines.
A calm, warm closing page for a trip to Kfar Hanokdim: a large empty frame for a drawing, blank ruled lines beneath it, and a row of outlined stars along the bottom.
Must contain: the date palm grove, desert lizards.
Render mode: `frame`.

**Image prompt**

```text
Create a black-and-white activity page with a large empty drawing area for a children's travel activity book.

Scene:
A calm, warm closing page for a trip to Kfar Hanokdim: a large empty frame for a drawing, blank ruled lines beneath it, and a row of outlined stars along the bottom.

Include:
• the date palm grove
• desert lizards

Layout:
Top half: one large empty frame. Middle: 3 groups of two blank ruled lines each. Bottom: a row of 3 evenly spaced star outlines. Small motifs only in the margins.

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
• Frame interior and all ruled lines must be completely empty.
• Stars must be plain outlines, unfilled and unnumbered.
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
