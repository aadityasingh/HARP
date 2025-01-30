import ctypes
import json
import multiprocessing as mp
import queue
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

import numpy as np
from google.cloud import storage

AMC_LETTER_CHOICES = ["A", "B", "C", "D", "E"]


def read_jsonl(path: Path | str):
    with open(path) as fh:
        return [json.loads(line) for line in fh.readlines() if line]


def write_jsonl(obj: Iterable[object], path: Path | str) -> None:
    with open(path, "w+") as fh:
        fh.write("\n".join([json.dumps(d) for d in obj]))


def get_uid(problem: dict[str, Any]) -> str:
    if "uid" in problem:
        return problem["uid"]
    
    # This is the UID convention we used for our dataset
    fields = ["year", "contest", "number"]
    if all(f in problem for f in fields):
        return "/".join([str(problem[f]) for f in fields])


def load_hendrycks_problem(filename: Path | str, data_dir: Path = Path("data/MATH")) -> dict[str, str]:
    """Load raw Hendryck's MATH problem given its unique ID.
    
    Uses the filename as a unique ids. Form is `<split>/<subject>/<num>.json`
    """
    with open(data_dir / filename) as f:
        prob = json.load(f)
        prob["uid"] = str(filename)
        return prob
    

def upload_blob(bucket_name: str, source_file_name: str, destination_blob_name: str) -> None:
    """Uploads a file to the Google Cloud bucket.
    
    Code copied from Google documentation

    Args:
        - bucket_name: ID of your GCS bucket
        - source_file_name: Path to local file to upload
        - destination_blob_name: ID of GCS object to upload to. Basically the GCS file path after the bucket name
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # Optional: set a generation-match precondition to avoid potential race conditions
    # and data corruptions. The request to upload is aborted if the object's
    # generation number does not match your precondition. For a destination
    # object that does not yet exist, set the if_generation_match precondition to 0.
    # If the destination object already exists in your bucket, set instead a
    # generation-match precondition using its generation number.
    generation_match_precondition = 0
    blob.upload_from_filename(source_file_name, if_generation_match=generation_match_precondition)

    print(
        f"File {source_file_name} uploaded to {destination_blob_name}."
    )


def download_blob(bucket_name: str, source_blob_name: str, dest_file_name: str) -> None:
    """Download a file from Google Cloud
    
    Code copied from Google documentation
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)

    blob.download_to_filename(dest_file_name)

    print(
        f"File {source_blob_name} downloaded to {dest_file_name}."
    )

T = TypeVar('T')

def run_with_timeout(func: Callable[..., T], timeout_seconds: float, default: Any,
                     *args: Any, **kwargs: Any) -> Optional[T]:
    """
    Run a function with a timeout using multiprocessing.
    
    Args:
        func: The function to run
        timeout_seconds: Maximum time to wait for completion
        default: Value to return if the function times out
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
    
    Returns:
        The function result or default value if timeout occurs
    """
    def worker(queue: mp.Queue) -> None:
        try:
            result = func(*args, **kwargs)
            queue.put(result)
        except Exception as e:
            print(f"Function failed with error: {str(e)}")
            queue.put(None)

    q = mp.Queue()
    process = mp.Process(target=worker, args=(q,))
    process.start()

    try:
        result = q.get(timeout=timeout_seconds)
        process.join()
        return result
    except (mp.TimeoutError, queue.Empty):
        print(f"Function timed out after {timeout_seconds} seconds")
        print(args, kwargs)
        process.terminate()
        process.join()  # Clean up the terminated process
        return default
    finally:
        # Ensure process is terminated and cleaned up
        if process.is_alive():
            process.terminate()
            process.join()

