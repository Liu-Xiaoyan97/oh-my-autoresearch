import json
import shutil
import sqlite3
import subprocess

from conftest import REPO_ROOT


def copy_runtime(tmp_path):
    runtime = tmp_path / "runtime"
    project = tmp_path / "project" / "nn-architecture"
    shutil.copytree(REPO_ROOT / "runtime.template", runtime)
    project.mkdir(parents=True)
    (project / "train.py").write_text("print('train')\n", encoding="utf-8")
    shutil.copy(runtime / "states" / "objective.example.json", runtime / "states" / "objective.json")
    objective_path = runtime / "states" / "objective.json"
    objective = json.loads(objective_path.read_text(encoding="utf-8"))
    objective["project_root"] = "project/nn-architecture"
    objective["devices"] = ["cuda:0", "cuda:1"]
    objective_path.write_text(json.dumps(objective, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return runtime


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True)


def test_validate_runtime_and_generate_launch(tmp_path):
    runtime = copy_runtime(tmp_path)

    run("python3", str(runtime / "scripts" / "database" / "init_db.py"), str(runtime))
    result = run("python3", str(runtime / "scripts" / "validate" / "validate_runtime.py"), str(runtime))
    payload = json.loads(result.stdout)

    assert payload["pass"] is True

    launch = run(str(runtime / "scripts" / "training" / "generate_launch.sh"), str(runtime))
    launch_path = launch.stdout.strip()

    launch_file = runtime.parent / "project" / "nn-architecture" / "launchscripts" / "launch_exp_0.sh"
    assert launch_path == str(launch_file)
    assert launch_file.exists()
    launch_content = launch_file.read_text(encoding="utf-8")
    assert f"PROJECT_ROOT={runtime.parent / 'project' / 'nn-architecture'}" in launch_content
    assert "TRAINING_SCRIPT=train.py" in launch_content
    assert "TRAINING_ARGS=(--num_training_steps 10000 --eval_n_steps 1000)" in launch_content
    assert "TRAINING_DEVICES=(cuda:0 cuda:1)" in launch_content
    assert "export AUTORESEARCH_DEVICES=cuda:0,cuda:1" in launch_content
    assert "export CUDA_VISIBLE_DEVICES=0,1" in launch_content
    assert 'exec python "$SCRIPT_PATH" "${TRAINING_ARGS[@]}"' in launch_content


def test_training_log_parser_reports_primary_metric(tmp_path):
    runtime = copy_runtime(tmp_path)
    log_file = runtime / "logs" / "train-of-exp_0.log"
    log_file.write_text("step=100, loss=0.25, val_step=100, val_accuracy=0.81\n", encoding="utf-8")

    result = run("python3", str(runtime / "scripts" / "training" / "monitor_training.py"), str(runtime), "exp_0")
    payload = json.loads(result.stdout)

    assert payload["train_step"] == 100
    assert payload["val_step"] == 100
    assert payload["val_metric"] == 0.81
    assert payload["loss_exploded"] is False


def test_observer_dispatch_writes_log_and_dynamic_metric(tmp_path):
    runtime = copy_runtime(tmp_path)
    run("python3", str(runtime / "scripts" / "database" / "init_db.py"), str(runtime))

    dispatch = runtime / "observer" / "scripts" / "dispatch" / "dispatch_event.py"
    run(
        "python3",
        str(dispatch),
        str(runtime),
        json.dumps({"event_type": "experiments", "payload": {"action": "insert_experiment", "exp_name": "exp_0"}}),
    )
    run(
        "python3",
        str(dispatch),
        str(runtime),
        json.dumps({
            "event_type": "experiments",
            "payload": {
                "action": "update_metric",
                "exp_name": "exp_0",
                "data": {"train_step": 100, "train_loss": 0.25, "val_step": 100, "val_metric": 0.81},
            },
        }),
    )
    run(
        "python3",
        str(dispatch),
        str(runtime),
        json.dumps({
            "event_type": "log",
            "payload": {
                "exp_name": "exp_0",
                "timestamp": "2026-06-15T00:00:00+00:00",
                "level": "INFO",
                "source": "test",
                "message": "ok",
            },
        }),
    )

    with sqlite3.connect(runtime / "db" / "runtime.sqlite") as conn:
        row = conn.execute(
            "SELECT train_step, val_step, val_metric, step_100 FROM experiments WHERE exp_name='exp_0'"
        ).fetchone()

    assert row == (100, 100, 0.81, 0.81)
    assert (runtime / "observations" / "exp_0.log").read_text(encoding="utf-8") == "[2026-06-15 00:00:00]|[INFO]-ok\n"
