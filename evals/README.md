# Runnable Evaluation Assets

`datasets/scenarios.json` records the three required behavior classes. The executable equivalents live in `tests/scenarios/test_core_scenarios.py` and use a scripted Agent backend, so they are deterministic and make no API calls.

Run them with:

```bash
.venv/bin/pytest tests/scenarios
```

Live model quality should be evaluated separately with representative private-safe notes before changing the default model, prompts, or reasoning effort.
