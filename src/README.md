# HARP source

You can use GitHub issues or contact [albert.s.yue@gmail.com](mailto:albert.s.yue@gmail.com) with questions.

## File structure

`data/` contains data files. Common subdirs include
- `raw/`: raw data files, such as
    - `MATH/`: the original Hendryck's MATH dataset files (in train/test split form)
    - `prm800k/`: PRM800K (for the MATH-500 split)
    - `aops_wiki/`: raw scrape files from `get.py`, one per problem saved in pickle files
- `processed/`: processed data files, such as a JSONL version of MATH and intermediate/final JSONL files for our dataset construction pipeline
- `processed_with_dup_info/`: some files related to duplicate analysis between MATH and our dataset

`inputs/` contains inputs passed into corresponding Batch APIs

`outputs/` contains the raw outputs from the various experiments we ran and described in the paper. You can download those files from [Google Drive](https://drive.google.com/drive/folders/1-OoVboyjiFbUVhn18MOZn5NMavsv3QGI?usp=sharing)

`eval/` contains our code for running evals and answer checking

`scraping/` contains code for scraping and constructing our dataset. More information can be found in the README in the folder

`test/` contains tests for our code. Right now, this contains answer checker tests

We also have the following scripts:
- A set of three scripts to run sequentially to determine the overlap between MATH and our dataset:
    1. `hendrycks_math_to_jsonl.py`
    2. `hendrycks_math_duplicate_find.py`
    3. `hendrycks_math_duplicate_sync.py`
- A script to run evals on MATH-500 `run_math500_eval.py`, along with some helper functions for subsequent answer checking
- A script to run the various evals we conducted on HARP `run_eval.py`. While tested, we only used this script at scale for o1 and Llama 3.1 evals, as we leveraged batch apis when available.


## Evals run

### Short answer

We ran short answer evals for 10 models. For 4 of these (o1 and Llama 3.1 families), there was no batch API available at the time, so we ran our own `run_eval.py` script in a tmux shell. The exact commands we ran are listed below. For the other 6, see `notebooks/runs/` for notebooks corresponding to each.
```bash
# o1-preview
python run_eval.py --model o1-preview-2024-09-12 --out outputs.jsonl --api openai --max-tokens 8192 --temperature 1

# o1-mini
python run_eval.py --model o1-mini-2024-09-12 --out outputs.jsonl --api openai --max-tokens 8192 --temperature 1

# Llama 3.1 405B
python run_eval.py --model meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo --api together --out hard.jsonl --temperature 0 --max-tokens 4096

# Llama 3.1 70B
python run_eval.py --model meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo --api together --out hard.jsonl --temperature 0 --max-tokens 2048
```
