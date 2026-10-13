# forms — The complete banned-form inventory

Everything on this page counts as a violation under strict E-Prime: every
core form, every contraction, every archaic remnant. Soft E-Priming (`prime`
mode) tolerates the noun uses of `being` and treats low-risk auxiliaries as
judgment calls. This file lists what the linter detects, what it deliberately
ignores, and how to resolve the ambiguous cases.

## Core forms

```text
be   am   is   are   was   were   been   being
```

Case never matters (`Is`, `IS`, `Was` all count). Position never matters:
main verb, auxiliary, infinitive, participle, imperative, subjunctive — all
banned.

## Contractions

```text
'm        → I'm
's        → it's, he's, she's, that's, there's, here's, who's, what's,
            where's, when's, how's, why's
're       → you're, we're, they're, there're
negatives → isn't, aren't, wasn't, weren't, ain't, amn't, an't
```

Curly apostrophes behave identically (`it’s` counts, so the linter
normalizes them).

## Archaic & dialect

```text
'twas   'twere   'tis   thou art   thou wert   thou wast   beest
```

`war` appears on Bourland's archaic list (a dialect past of `were`), but the
noun overwhelms it in modern text, so the linter leaves `war` alone rather
than flood users with false positives. `art` counts only right after `thou`;
the noun `art` (as in fine art) stays safe.

## The three readings of `'s`

`'s` carries three readings; two of them violate:

1. **Contraction of `is`** — `It's raining`, `That's all` — violates.
2. **Contraction of `has`** — `He's gone`, `It's been ages` — no violation
   from the `'s` itself (`been` still counts, of course).
3. **Possessive** — `John's book`, `the skill's layout` — no violation.

Resolution rules:

- `let's` always reads as *let us* — never a violation.
- Pronoun stem (`he`, `she`, `it`, `that`, `there`, `here`, `who`, `what`,
  `where`, `when`, `how`, `why`) + `'s` + participle (`gone`, `done`,
  `been`, `started`…) → likely *has*.
- Pronoun stem + `'s` + anything else → `is`.
- Noun stem + `'s` + article or adjective → often `is`:
  `The cat's on the mat again`. Noun stem + `'s` + noun → likely
  possessive. Judge by context; when uncertainty survives the judgment,
  treat the token as a violation in strict mode.

## Edge constructions

| Pattern | Example | Repair |
|---------|---------|--------|
| infinitive | I want `to be` alone. | I want solitude. |
| subjunctive | If I `were` you… | If I stood in your shoes… |
| mandative | So `be` it. | Very well then. |
| concessive | `Be` that as it may. | Granted, and still. |
| imperative | `Be` careful. | Take care. |
| existential let | Let there `be` light. | Light appeared. |
| progressive passive | The bridge `is being` built. | Workers build the bridge. |
| perfect passive | The report `has been` finalized. | The team finalized the report. |
| future | It `will be` ready. | It finishes tonight. |
| scheduled | The meeting `is to` start at 3. | The meeting starts at 3. |
| destiny | She `was to` become famous. | Fame found her later. |
| past habit | He `used to be` shy. | Shy once; he grew out of it. |
| visit | I `have been to` Paris. | I visited Paris. |
| birth | I `was born` in 1990. | My mother bore me in 1990. / I arrived in 1990. |
| cleft | It `was` John who called. | John called. |
| day of week | Today `is` Tuesday. | Today falls on Tuesday. |
| math | Two plus two `is` four. | Two plus two equals four. |
| age | She `is` thirty. | She has lived thirty years. |
| comparison | X `is` taller than Y. | X stands taller than Y — by two inches, per the tape. |

## Noun & gerund `being`

| Phrase | Strict | Soft (`prime` mode) |
|--------|--------|---------------------|
| a human `being` | violates — write *a human*, *a person* | tolerated |
| `well-being` | violates — write *welfare*, *health* | tolerated |
| the supreme `being` | violates — write *the deity*, *God* | tolerated |
| for the time `being` | violates — write *for now* | tolerated |
| state of `being` | violates — write *condition*, *existence* | tolerated |

Bourland's own rule: the token `being` appears literally, so strict E-Prime
drops it everywhere. The linter flags every `being` and adds a noun-use
note when context suggests one; `prime` mode keeps the noun uses.

## False positives (leave these alone)

- **Substrings**: `island`, `isotope`, `this`, `his`, `maybe`, `because`,
  `begin`, `beside`, `between`, `beyond`, `timber`, `number`, `Amsterdam`,
  `werewolf` — none contains a standalone token. Token-level matching never
  trips on them.
- **`its`** (possessive, no apostrophe) — safe. Only `it's` counts.
- **`let's`** — *let us*.
- **Possessive `'s`** and **`'s` as *has*** — see the three readings above.
- **`art`, `war`** as nouns — see the archaic section.
- **Hyphen prefixes**: the linter skips any token directly followed by a
  hyphen, so `IS-Architecture` stays quiet; post-hyphen segments still flag
  (`well-being` exposes its `being`).

## How to scan your own output

1. Match tokens, never substrings: word boundaries, case-insensitive,
   contractions attached to their hosts.
2. Mask code, inline code, URLs, and frontmatter before scanning.
3. Preserve quoted spans verbatim; tag their hits instead of fixing them
   (offer a paraphrase alongside).
4. Promote every ambiguous `'s` to a judgment call; in strict mode, treat
   surviving uncertainty as a violation.
5. Check gerund and noun `being` cases against the strict/soft table above.

## A reassuring precedent

Russian, Hungarian, and Mandarin lack any exact `to be` equivalent, and
their speakers account for roughly a fifth of humanity. A language without
a copula not only functions — it communicates fluently. English can stand
the amputation; speakers of copula-free languages never miss the vein.