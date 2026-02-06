# Setup Guide

If you can copy/paste commands into a terminal, you can run this project.

---

## 0) Install prerequisites (one-time)

- Install Python 3.11+ (or whatever you already have)
- Install Git
- Optional: Install VS Code

---

## 1) Clone the repo (download the code)

Open a terminal and run:

```bash
git clone https://github.com/Tculhane8879/Speech-Aware-Meeting-Summarizer.git
cd Speech-Aware-Meeting-Summarizer
```

## 2) Create and activate virtual environment

Windows:

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

MacOS / Linux

```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

## 3) Install project dependencies

```
python -m pip install -r requirements.txt
```

## 4) Run the pipeline scaffold

The pipeline scaffold should always work if set up correctly, before any speech models are even added.

Windows:

```
$env:PYTHONPATH="src"
python src\cli.py --output outputs\smoke_test
```

MacOS / Linux

```
PYTHONPATH=src python src/cli.py --output outputs/smoke_test
```

Expected behavior:

- The terminal prints that the pipeline ran
- A folder outputs/smoke_test/ is created
- Inside it you should see: - stages.txt - summary.md
  Note: outputs/ is ignored by git and should never be committed.

## 5) Run automated tests

Verify correct set up, run:

```
python -m pytest -q
```

Expected output:

```
1 passed
```

## 6) Using VSCode

- Open the project folder in VSCode
- Select the correct Python interpreter
  - Choose Python: Select Interpreter
  - Select the interpreter inside .venv

If VS Code shows import warnings but the code runs correctly, that is safe to ignore.

## 7) GitHub workflow

- Do not commit directly to main
- Create your own branch for your work

```
git checkout -b feat/your-feature-name
```

- Push your branch and open a Pull Request

## 8) Errors

If you're getting errors with the set up, copy the commands you used and errors into ChatGPT and it will walk you through steps to fix them.
