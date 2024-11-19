# HARD-Math source

To be updated with more details soon. Contact [albert.s.yue@gmail.com](mailto:albert.s.yue@gmail.com) with questions.

## File structure

`data/` contains data files. Common subdirs include
- `raw/`: raw data files, such as
    - `MATH/`: the original Hendryck's MATH dataset files (in train/test split form)
    - `prm800k/`: PRM800K (for the MATH-500 split)
    - `aops_wiki/`: raw scrape files from `get.py`, one per problem saved in pickle files
- `processed/`: processed data files, such as a JSONL version of MATH and intermediate/final JSONL files for our dataset construction pipeline
- `processed_with_dup_info/`: some files related to duplicate analysis between MATH and our dataset

`outputs/` contains the raw outputs from the various experiments we ran and described in the paper. You can download those files from [Google Drive](https://drive.google.com/drive/folders/1-OoVboyjiFbUVhn18MOZn5NMavsv3QGI?usp=sharing)

`eval/` contains our code for running evals and answer checking

`scraping/` contains code for scraping and constructing our dataset. More information can be found in the README in the folder

`test/` contains tests for our code. This only contains answer checker tests as of now

We also have the following scripts:
- A set of three scripts to run sequentially to determine the overlap between MATH and our dataset:
    1. `hendrycks_math_to_jsonl.py`
    2. `hendrycks_math_duplicate_find.py`
    3. `hendrycks_math_duplicate_sync.py`
- A script to run evals on MATH-500 `run_math500_eval.py`, along with some helper functions for subsequent answer checking
- A script to run the various evals we conducted on HARD-Math `run_eval.py`. Note that we did not really use this script except for Llama 3.1 evals, as we leveraged batch apis for the other model families we explored
