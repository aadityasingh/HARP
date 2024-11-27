# Pipeline

We create the HARP dataset and splits by running a series of python scripts. The full pipeline to create the full dataset and three splits is as follows:
```
python src/scraping/get.py && \
	python src/scraping/process.py > scraping/log.txt && \
	python src/scraping/dedupe.py && \
	python src/scraping/finalize.py && \
	python src/scraping/make_datasets.py
```

# File format

We use a jsonl format for the files -- this means each line is a separate json, with the same keys across lines. We generate multiple intermediate jsonl files: 

- aops_wiki_all_text.jsonl: This has all the raw text that gets scraped from the HTML -- note a small amount of processing is still applied to remove usernames, standardize boxed command, and remove links at the ends of solutions. It has a line for every possible problem in our dataset (6432 problems)
- aops_wiki.jsonl: This file that contains only problems for which we were able to extract "valid" solutions. For problems with answers (non-USAMO), a "valid" solution must have the correct boxed answer, and not refer to prior solutions. For USAMO/proof-problems, the latter condition doesn't apply.
- aops_wiki_deduped.jsonl: This file is the same as `aops_wiki.jsonl` but with duplicate problems removed. We deduplicate using a trie, as well as with some manual deduplication.
- aops_wiki_final.jsonl: This is the final dataset. This adds in the expert-made subject labels, manually removes a few bad solutions, and standardizes the last boxed value in each solution to the answer value.

Here are fields that you may find in these files:

- `year`: Year of the contest
- `contest`: Type of the contest. AJHSME, AMC8, AHSME, AMC10A/B, AMC12A/B are all multiple choice. AIME I/II are free response, but answer must be an integer between 0 and 999, inclusive. USA(J)MO are proofs.
- `number`: Question number within contest. Generally, later problems are more challenging.
- `url`: URL that the problem was scraped from. Can be useful for checking weird things. Note that the AoPS pages are dynamic (as the wiki is editable), so we can't guarantee that the HTML will be the same now as it was when we ran the scrape in September 2024.
- `full_text`: The "raw" HTML scrape. Does do a few things like preprocess out links, usernames, standardizes whitespace and normalizes boxed. Contains markdown headers for Problem/Solution
- `num_gpt4_tokens`: Number of tokens, if using the GPT4 tokenizer (`cl100k_base` from [tiktoken](https://github.com/openai/tiktoken))
- `choices`: If not null, a dictionary mapping the 5 letter choices A/B/C/D/E to their answers. Almost all answers are surrounded by '$' to indicate they are in LaTeX.
- `problem`: The reduced problem text, extracted from `full_text`. Does not contain header nor choices.
- `answer_choice`: If choices is not null, the correct letter choice
- `answer`: The answer to the problem (in math). Should be non-null for all but the USA(J)MO problems
- `solution_{i}`: text of solution #i, extracted from `full_text`. i starts at 1 and goes up to `num_solutions`. Header is stripped.
- `solution_{i}_metadata`: Sometimes, solution headers contain some information. For example "Solution 2 (Trigonometry)". In this case, "Trigonometry" will be stored in metadata. Most metadata's are null.
- `num_solutions`: Number of solutions for this problem. Will be >= 1.
- `other_appearances`: List of other contest problems that we determined to be duplicates of this problem.

We ran the scrape on Sept 19-20, 2024.

## Difficulty ratings

The exact mapping we use is in `difficulty.py`. The mapping is based on [AoPS difficulty ratings](https://artofproblemsolving.com/wiki/index.php/AoPS_Wiki:Competition_ratings)

# Processing notes

To record special things taken into account via manual inspection + iteration. Note, the output of `process.py` can be referred to for checking missing problems/warnings. Also, running `process.py` is not that expensive (<30 seconds), since we only have ~6k problems, which means if needed we can iterate on the processing!

## Extracting text + latex content

On AoPS, latex is rendered as images, with the raw latex appearing in alt_text. We have a method that replaces images with their alt text.

To get problem and solution text, we manually inspected HTML and wrote a regex (with the help of GPT4) that searches for the Problem and Solution blocks. To get this to work properly, we do some pre-pre-processing of the HTML:

- We remove some aesthetic HTML elements, like `<hr />` and `<p class="mw-empty-elt">`
- We found that sometimes `<center>` is used, so we turn those into `<p>` to keep the regex simple.
- Similarly, sometimes there are content or diagrams in the middle of solution with `<div class="center|floatright|floatleft|floatnone">` or `<div style="text-align:center">` tags, which we also turn into `<p>`.
- We process various HTML list elements into `<p>` with bullet points added.
- We merge adjacent `<p>` blocks. 
- Some pieces of text are also hyperlinked, so we have a preprocessing regex that removes links but retains the surface text. 
- We also remove `<br />` tags as sometimes these get included in the problems/solutions.

Note, this process isn't perfect. However, most of these should get caught in the future solutions step, which checks to see if the answer is present. For proof questions, they might be missed, but I'm not sure how to better address that!

Next, we do some post processing to:
	- remove Usernames (see more info below)
	- remove "Alternate solutions" artifacts 
	- trim new lines
	- convert all answer boxes to \boxed (instead of \fbox and \framebox, which are used in the earlier AHSMEs)
	- Remove emails (via regex)
	- Line level filter to remove lines containing usernames and/or lines containing hyperlinks (not useful) at the end of solutions. We do not apply this filter to earlier lines, as we do not want to break a solution by removing a line in the middle.
	- Manual line filters, to remove lines containing usernames or are otherwise irrelevant to the solution, and that don't cleanly fall into the regexes above. These are highly specific lines, so we can remove them from the middle of solutions (and we verified that we don't make undesirable deletions).

## Usernames

We want to try removing as many usernames as possible to avoid noise. One "ideal" way to do this would be if we had a list of all AoPS usernames, and we could delete those. This is problematic however due to common usernames like "Polynomial".

Instead, we note that most usernames are preceded by a \~ or \- character, so we use that to filter. More often than not, these are on a separate line, but sometimes they're at the end of a preceding line, so we check for both of these. We also manually account for a few other cases we identified in the line-level filter mentioned above.

We acknowledge that username removal isn't perfect, but have given it our best effort. There a number of examples under what we described above that aren't captured by the regex because of the high amount of variability there can be. Given that AoPS recommends not having a username that's personally identifiable, we believe there is minimal leakage of personal information (especially given that we have a separate step to remove emails).

## Processing choices

For multiple choice questions, we extract the choices as a dictionary. This involves some string preprocessing, with a few cases, as choices are often provided as `\text OR \textbf OR \mathrm`. Furthermore, for some few questions, the choices are not LaTeX, but rather, text, so we handle this with a niche check.

There's also this [pesky AMC](https://artofproblemsolving.com/wiki/index.php/2005_AMC_12A_Problems) where the choices are formatted as `(\mathrm {A})` instead of `\mathrm{(A)}`. We manually handle this.

We assume the choices are ABCDE, as this is the format all AMCs take throughout the years.

We remove `\left, \right` tags from choices to further standardize.

## Processing answers

We only get answers for non-proof questions. For these, there are two cases: multiple choice exams (everything but AIME), and free response exams (AIME) where the answer is between 0 and 999 inclusive. For the former case, we thus look for a letter choice in the `\boxed part` of a solution. Then, given the letter, we index into the choices to get the answer. We also store the letter in `answer_choice` for ease of reference.

For AIME, we extract the internals of the `\boxed`, and try to convert to an integer. If this is successful, we assume that's the answer. Note, this also takes care of the 0-padding often used to make AIME answers 3 digits (e.g. 010 instead of 10).

If a solution as multiple `\boxed` parts, we extract each of them. If we get muliple different answers, we drop the solution, which can happen if a solution uses `\boxed` for purposes other than to indicate the answer. We also drop solutions with nested `\boxed` commands. Further, we have a check to make sure all solutions with `\boxed` have the same answer. If not, we throw out the problem.

## Processing solutions

We only retain solutions that contain an answer in `\boxed`. This eliminates many incomplete or otherwise messed up solutions (such as those that are truncated due to casework with HTML `<ul>` tags). 

Some solutions refer to "as above" and refer to earlier solutions, since many webpages have multiple solutions. We remove all solutions containing this phrase and other direct references to a prior solution, to keep all solutions atomic.

In general, the `get_problem_solution_choices` is coded with a lot of forms of "early-termination" to catch these cases. For example, if no valid answer, then no point in having solutions. 
