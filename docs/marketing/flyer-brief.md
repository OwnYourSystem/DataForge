# DataForge flyer brief

Date: 15 November 2026
Purpose: a design brief for 1 flyer that attracts learners to the DataForge portal.
Rule: the flyer shows the portal as it is today. Each claim in this brief is true for the live code. Planned features go in 1 band that is labelled as planned.

---

## 1. The one message

**You do not learn data engineering by watching. You learn it by building, and DataForge checks what you built.**

If a reader remembers 1 thing, it must be this: DataForge checks the result of your work, not only that you clicked through a lesson.

---

## 2. Audience

- Data analysts and junior data engineers who know basic SQL.
- People who completed video courses on dbt or Databricks and cannot yet show that they can do the work.
- Engineers who want proof of skill, not a certificate of attendance.

They read the flyer on LinkedIn or a web page, mostly on a phone. They give it 3 seconds.

---

## 3. The gap that DataForge fills

Use this as the argument of the flyer. Do not name a competitor on the flyer.

| What online training usually gives | What DataForge gives |
|---|---|
| Videos and quizzes about a tool | A real task, in the real tool |
| A notebook where each cell is already written | An empty model that you must complete |
| The solution, 1 click away | The solution is never shown |
| "Completed", if you ran all the cells | "Passed", only if your table is correct |
| Training on the products of 1 vendor | Skills that are the same on each platform: SQL, dbt, data quality |
| A course about features | A task with a reason: why the data must be clean |

Short form for the flyer: **Courses show you. DataForge makes you do it, then checks it.**

---

## 4. Headline and sub-headline

Recommended:

- Headline: **Learn data engineering by building it.**
- Sub-headline: **Write a real dbt model in your browser. An independent grader checks your table.**

Alternatives for the headline:

- **Stop watching. Start building.**
- **Do the work. Get the proof.**

---

## 5. Layout, top to bottom

Format: portrait, 4:5 (for example 1080 x 1350 px). The current draft uses this shape.

1. **Logo and headline** (top 20%)
2. **Screen of the portal** (the main visual, 35%)
3. **How it works**: 4 steps in a row
4. **What you get**: 6 small tiles
5. **Proof band**: 1 strong line
6. **What is next**: 1 thin band, labelled as planned
7. **Call to action** and tagline

---

## 6. The screen: show the real portal

This is the most important part. The screen on the flyer must look like the real product. Use these exact contents.

**Top bar, left to right**
- `DataForge` (bold)
- `Build and Test a Retail Customer Staging Model` (grey)
- Badge `Completed` (green)
- `Best score: 100`
- An email address, for example `learner@example.com`
- Button `Sign out`

There is no menu. Do not draw "Labs", "Paths", or "Progress".

**Left panel: the task**

Title: `LAB-001: Build and Test a Retail Customer Staging Model`

Text: "The table `raw_customers` holds 5 customer records. The data is not clean: some values have spaces at the start or the end, and the letter case is not consistent."

A table with 2 columns, "Column" and "Rule":

| Column | Rule |
|---|---|
| `customer_key` | `customer_id` cast to `bigint` |
| `customer_name` | spaces removed from the start and the end |
| `email` | spaces removed, lowercase |
| `country` | spaces removed, uppercase |
| `processed_at` | the current timestamp |

**Middle panel: the editor**

File name: `models/staging/stg_customers.sql`, then the word `Saved`, then the blue button `Build and test`.

Code (use this text exactly; do not add a `config()` block, the portal does not permit it):

```sql
with source_data as (
    select
        customer_id,
        customer_name,
        email,
        country
    from {{ source('retail_raw', 'raw_customers') }}
),
cleaned as (
    select
        cast(customer_id as bigint) as customer_key,
        trim(customer_name) as customer_name,
        lower(trim(email)) as email,
        upper(trim(country)) as country,
        current_timestamp as processed_at
    from source_data
)
select *
from cleaned
```

**Bottom or right panel: the result**

Badge `Passed` (green), then `Score: 100 / 100`, then `6.5 s compute`.

The 5 checks, with these exact names and points:

| Check | Points |
|---|---:|
| The model reads the dbt source | 15 / 15 |
| Columns have the correct values and types | 30 / 30 |
| The dbt build is successful (critical) | 20 / 20 |
| Keys are unique and not null; dbt tests pass (critical) | 25 / 25 |
| Column names and order are correct | 10 / 10 |

**Optional second image: the honest fail**

A small inset that shows the first attempt: badge `Not passed`, `Score: 60 / 100`, with a red cross on "Columns have the correct values and types" and on "Column names and order are correct". Caption: **"It runs" is not the same as "it is correct".** This inset shows the difference from other training better than a perfect score.

---

## 7. How it works: 4 steps

| Step | Title | Text |
|---|---|---|
| 1 | Open the lab | Read the task and look at the rules for each column. |
| 2 | Write your dbt model | Complete the SQL in the online editor. Your work is saved. |
| 3 | Build and test | The platform runs dbt and the data tests for you. |
| 4 | See what passed | You get a score and a list of checks, each with pass or fail. |

Write "the lab", not "choose a lab". There is 1 lab today.

---

## 8. What you get: 6 tiles

| Tile | Text | Icon idea |
|---|---|---|
| 1 | No setup. A browser is all you need. | Laptop |
| 2 | Real tools: dbt and SQL. | Database |
| 3 | The grader checks your table, not only your code. | Checklist |
| 4 | A result in 10 to 20 seconds. | Lightning |
| 5 | Your work and your best score are saved. | Chart |
| 6 | Each run starts clean. A mistake breaks nothing. | Circular arrows |

Section title: **What you get**. Do not use "Why learners love it". There are no learner quotes yet.

---

## 9. Proof band

Main line: **Proof of skill. A pass means that you built the correct result yourself.**

Line below: **The solution is never shown.**

---

## 10. What is next: 1 band, labelled as planned

Title of the band: **Coming next**

- Explore the data with your own queries before you build.
- Labs on Databricks with Unity Catalog.
- A platform built in the open with Terraform, with a blueprint for each part.

Design this band smaller and quieter than the tiles. It must not look like a list of current features. Do not put the logos of Databricks or Terraform in the main visual.

---

## 11. Call to action

Button: **Start the lab**

Address below the button: `dataforge-ayum.onrender.com`

Tagline at the bottom: **Build. Test. Learn.**

---

## 12. Visual style

Keep the dark, technical look of the current draft. Use the colors of the real portal for the screen, so that the flyer and the product agree.

| Use | Light theme | Dark theme |
|---|---|---|
| Page background | `#f6f7f9` | `#12161c` |
| Panel background | `#ffffff` | `#1a2029` |
| Text | `#17202b` | `#e6eaf0` |
| Grey text | `#5d6b7a` | `#9aa7b6` |
| Lines | `#dfe4ea` | `#2c3542` |
| Button and accent | `#1f5fd1` | `#6ea0ff` |
| Pass | `#17794a` on `#e2f4ea` | `#63d39a` on `#163526` |
| Fail | `#b3261e` on `#fbe9e7` | `#ff8a80` on `#40201d` |

- Font in the portal: the system sans-serif font. For code: a monospace font.
- The portal button is blue, with a radius of 6 px. It is not a gradient.
- A dark flyer can show the dark theme of the portal. Both themes are real.

---

## 13. Facts that the designer can use

| Fact | Value |
|---|---|
| Labs available | 1 (LAB-001) |
| Level | Beginner |
| Time for the lab | 45 to 60 minutes |
| Rows in the lab data | 5 customer records |
| Checks in the grade | 5, of which 2 are critical |
| Score to pass | 80 of 100, with all critical checks passed |
| Time for 1 run | About 10 to 20 seconds |
| Sign-in | A code by email. No password |
| Cost for the learner | Free |

---

## 14. Do not show or say

- A menu with "Labs", "Paths", or "Progress".
- More than 1 lab, or "choose a lab".
- A `config()` block or other Jinja in the code, apart from `source()`.
- Databricks, Terraform, or Asset Bundles as current features.
- "Why learners love it", learner quotes, or learner numbers.
- A certificate. The portal gives a score and a pass, not a certificate.
- The name or logo of a different training provider.

---

## 15. Before the flyer is published

1. **Sign-in must work on the live portal.** On 15 November 2026 it does not: 3 settings in the Supabase project are open. A flyer that sends people to a portal they cannot enter does damage.
2. **The live portal is a free, single-container test deployment.** It is for a small number of people. Move to the split layout before the flyer goes to a large audience.
3. **Check the trademark rules** for the dbt name and logo before you use the logo. The name in plain text is the safer choice.
