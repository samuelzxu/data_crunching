Info for using this:
- python 3.10.13
- do `pip install aiohttp tqdm requests`
- Either use the jupyter notebook or the functions in `import_utils.py`
- the `ver` variable is there because even after deleting, things are only "soft-deleted" so the primary keys are still there. Hence you increment that whenever doing a fresh import
- fill out `auth` with your bearer token (i.e. `auth = "Bearer hjgknlds-ahfidsaflkd0-saflas"` or whatever)
- deletion function is async because the deletion endpoint only takes one at a time afaik