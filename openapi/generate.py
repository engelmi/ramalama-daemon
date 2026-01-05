import json
import pathlib

from daemon.server import setup_server as daemon_setup
from worker.server import setup_server as worker_setup

def generate_daemon_spec(outdir: pathlib.Path):
    app, api = daemon_setup()

    with app.app_context():
        spec_dict = api.spec.to_dict()
        with open(outdir.joinpath("daemon/openapi.json"), "w") as f:
            json.dump(spec_dict, f, indent=2)

def generate_worker_spec(outdir: pathlib.Path):
    app, api = worker_setup("/not-relevant")

    with app.app_context():
        spec_dict = api.spec.to_dict()
        with open(outdir.joinpath("worker/openapi.json"), "w") as f:
            json.dump(spec_dict, f, indent=2)

if __name__ == "__main__":
    outdir = pathlib.Path(__file__).parent.resolve()
    generate_daemon_spec(outdir)
    generate_worker_spec(outdir)
