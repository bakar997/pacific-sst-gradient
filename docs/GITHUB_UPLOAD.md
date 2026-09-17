# Put the project on GitHub

1. Extract `pacific-sst-gradient.zip` on your computer.
2. Read `README.md`, run the workflow and work through the notebook. Add a truthful personal verification entry in `docs/ASSISTANCE.md`.
3. Create a GitHub repository named `pacific-sst-gradient`. Suggested description: “Reproducible analysis of tropical Pacific SST contrasts using ERSSTv5 and COBE-SST2, with trend uncertainty and sensitivity checks.”
4. Upload the **contents** of the extracted `pacific-sst-gradient` folder, preserving its subfolders. `README.md` should appear at the repository root. Do not upload only the ZIP: GitHub should be able to display the code, notebook and figures.
5. Include `data/raw/` and `data/provenance.json`; the small frozen subsets make the analysis reproducible. Exclude `.venv`, `__pycache__` and notebook checkpoints, as the included `.gitignore` specifies.
6. Check that the README images load and the notebook displays its saved output. GitHub publication is your action; it has not been performed as part of preparing this package.

You can use GitHub Desktop to add and publish the extracted folder. That avoids command-line Git setup. If using Git instead, create the empty repository on GitHub first and follow GitHub's commands for pushing an existing local folder; use your own repository URL.

Keep the data citations and assistance note. Update numerical wording if you change data or methods. The repository is an observational learning project, not evidence that you performed climate-model attribution or already have expertise in all the proposed next steps.
