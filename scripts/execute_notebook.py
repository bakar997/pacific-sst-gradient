"""Execute the notebook using this Python environment, preserving its outputs."""
from pathlib import Path
import sys
import tempfile
import json
import os
import argparse
import nbformat
from nbclient import NotebookClient
from traitlets.config import Config

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--ipc", action="store_true", help="Use local IPC sockets on Unix instead of TCP")
parser.add_argument("--in-process", action="store_true", help="Execute with IPython in this process; no kernel sockets")
args = parser.parse_args()
path = ROOT/"notebooks/pacific_sst_gradient.ipynb"
notebook = nbformat.read(path, as_version=4)
if args.in_process:
    # Real cell execution for restricted environments where kernel sockets are
    # unavailable. All notebook cells use standard Python; no outputs are mocked.
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.utils.capture import capture_output
    shell = InteractiveShell.instance()
    os.chdir(ROOT)
    count = 0
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        count += 1
        with capture_output(stdout=True, stderr=True, display=True) as captured:
            result = shell.run_cell(cell.source, store_history=True)
        if result.error_before_exec or result.error_in_exec:
            raise RuntimeError(f"Notebook cell {count} failed") from (result.error_before_exec or result.error_in_exec)
        cell.execution_count = count
        cell.outputs = []
        if captured.stdout:
            cell.outputs.append(nbformat.v4.new_output("stream", name="stdout", text=captured.stdout))
        if captured.stderr:
            cell.outputs.append(nbformat.v4.new_output("stream", name="stderr", text=captured.stderr))
        for item in captured.outputs:
            cell.outputs.append(nbformat.v4.new_output("display_data", data=item.data, metadata=item.metadata))
        cell.metadata.pop("execution", None)
    notebook.metadata["execution_method"] = "IPython in-process execution; kernel sockets unavailable in build environment"
    notebook.metadata["language_info"]["version"] = sys.version.split()[0]
    nbformat.validate(notebook)
    nbformat.write(notebook, path)
    print(f"Executed {count} notebook code cells successfully (IPython in-process).")
    sys.exit(0)
# A temporary kernelspec ensures this command uses the same environment in
# which its pinned requirements were installed; no global kernel changes.
with tempfile.TemporaryDirectory() as directory:
    kernel = Path(directory)/"kernels"/"sst-local"
    kernel.mkdir(parents=True)
    (kernel/"kernel.json").write_text(json.dumps({"argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "Pacific SST (local)", "language": "python"}))
    previous = os.environ.get("JUPYTER_PATH")
    os.environ["JUPYTER_PATH"] = directory+(os.pathsep+previous if previous else "")
    try:
        kernel_config = Config()
        if args.ipc:
            kernel_config.KernelManager.transport = "ipc"
            kernel_config.KernelManager.ip = str(Path(directory)/"sst")
        NotebookClient(notebook, timeout=300, kernel_name="sst-local", config=kernel_config,
                       resources={"metadata": {"path": str(ROOT)}}).execute()
    finally:
        if previous is None:
            os.environ.pop("JUPYTER_PATH", None)
        else:
            os.environ["JUPYTER_PATH"] = previous
notebook.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
notebook.metadata["execution_method"] = "Jupyter kernel execution (nbclient)"
notebook.metadata["language_info"]["version"] = sys.version.split()[0]
nbformat.write(notebook, path)
print("Executed notebooks/pacific_sst_gradient.ipynb successfully.")
