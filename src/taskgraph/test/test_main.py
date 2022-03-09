# Any copyright is dedicated to the public domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import pytest

import taskgraph
from taskgraph.graph import Graph
from taskgraph.main import (
    get_filtered_taskgraph,
    main as taskgraph_main,
)
from taskgraph.task import Task
from taskgraph.taskgraph import TaskGraph


@pytest.fixture
def run_main(maketgg, monkeypatch):
    def inner(args, **kwargs):
        kwargs.setdefault("target_tasks", ["_fake-t-0", "_fake-t-1"])
        tgg = maketgg(**kwargs)

        def fake_get_taskgraph_generator(*args):
            return tgg

        monkeypatch.setattr(
            taskgraph.main, "get_taskgraph_generator", fake_get_taskgraph_generator
        )
        taskgraph_main(args)
        return tgg

    return inner


@pytest.mark.parametrize(
    "attr,expected",
    (
        ("tasks", ["_fake-t-0", "_fake-t-1", "_fake-t-2"]),
        ("full", ["_fake-t-0", "_fake-t-1", "_fake-t-2"]),
        ("target", ["_fake-t-0", "_fake-t-1"]),
        ("target-graph", ["_fake-t-0", "_fake-t-1"]),
        ("optimized", ["_fake-t-0", "_fake-t-1"]),
        ("morphed", ["_fake-t-0", "_fake-t-1"]),
    ),
)
def test_show_taskgraph(run_main, capsys, attr, expected):
    run_main([attr])
    out, err = capsys.readouterr()
    assert out.strip() == "\n".join(expected)
    assert "Dumping result" in err


def test_tasks_regex(run_main, capsys):
    run_main(["full", "--tasks=_.*-t-1"])
    out, _ = capsys.readouterr()
    assert out.strip() == "_fake-t-1"


def test_output_file(run_main, tmpdir):
    output_file = tmpdir.join("out.txt")
    assert not output_file.check()

    run_main(["full", f"--output-file={output_file.strpath}"])
    assert output_file.check()
    assert output_file.read_text("utf-8").strip() == "\n".join(
        ["_fake-t-0", "_fake-t-1", "_fake-t-2"]
    )


@pytest.mark.parametrize(
    "regex,exclude,expected",
    (
        pytest.param(
            None,
            None,
            {
                "a": {
                    "attributes": {"kind": "task"},
                    "dependencies": {"dep": "b"},
                    "description": "",
                    "kind": "task",
                    "label": "a",
                    "optimization": None,
                    "soft_dependencies": [],
                    "if_dependencies": [],
                    "task": {
                        "foo": {"bar": 1},
                    },
                },
                "b": {
                    "attributes": {"kind": "task", "thing": True},
                    "dependencies": {},
                    "description": "",
                    "kind": "task",
                    "label": "b",
                    "optimization": None,
                    "soft_dependencies": [],
                    "if_dependencies": [],
                    "task": {
                        "foo": {"baz": 1},
                    },
                },
            },
            id="no-op",
        ),
        pytest.param(
            "^b",
            None,
            {
                "b": {
                    "attributes": {"kind": "task", "thing": True},
                    "dependencies": {},
                    "description": "",
                    "kind": "task",
                    "label": "b",
                    "optimization": None,
                    "soft_dependencies": [],
                    "if_dependencies": [],
                    "task": {
                        "foo": {"baz": 1},
                    },
                },
            },
            id="regex-b-only",
        ),
        pytest.param(
            None,
            [
                "attributes.thing",
                "task.foo.baz",
            ],
            {
                "a": {
                    "attributes": {"kind": "task"},
                    "dependencies": {"dep": "b"},
                    "description": "",
                    "kind": "task",
                    "label": "a",
                    "optimization": None,
                    "soft_dependencies": [],
                    "if_dependencies": [],
                    "task": {
                        "foo": {"bar": 1},
                    },
                },
                "b": {
                    "attributes": {"kind": "task"},
                    "dependencies": {},
                    "description": "",
                    "kind": "task",
                    "label": "b",
                    "optimization": None,
                    "soft_dependencies": [],
                    "if_dependencies": [],
                    "task": {
                        "foo": {},
                    },
                },
            },
            id="exclude-keys",
        ),
    ),
)
def test_get_filtered_taskgraph(regex, exclude, expected):
    tasks = {
        "a": Task(kind="task", label="a", attributes={}, task={"foo": {"bar": 1}}),
        "b": Task(
            kind="task", label="b", attributes={"thing": True}, task={"foo": {"baz": 1}}
        ),
    }

    graph = TaskGraph(tasks, Graph(set(tasks), {("a", "b", "dep")}))
    filtered = get_filtered_taskgraph(graph, regex, exclude)
    assert filtered.to_json() == expected
