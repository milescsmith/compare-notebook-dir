from json import JSONDecodeError
from pathlib import Path
from typing import Annotated

import typer
from loguru import logger
from nbdime.args import prettyprint_config_from_args
from nbdime.diffing.notebooks import diff_notebooks
from nbdime.nbdiffapp import pretty_print_notebook_diff

# from nbdime.nbdiffapp import main as nbdiffapp_main
from nbdime.utils import read_notebook
from nbdime.webapp.nbdimeserver import main_server
from nbdime.webapp.webutil import browse
from nbformat.reader import NotJSONError
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text
from tornado.netutil import bind_sockets

from . import __version__
from .logging import init_logger

console = Console()


class ANSIConsole(Console):
    def write(self, text):
        reformatted = Text(overflow="fold").from_ansi(text)
        self.print(reformatted, end="")


diff_config = prettyprint_config_from_args(
    arguments={
        "attachments": True,
        "color_words": False,
        "details": True,
        "id": True,
        "language": None,
        "metadata": True,
        "outputs": True,
        "sources": True,
        "use_color": True,
        "use_diff": True,
        "use_git": True,
    },
    out=ANSIConsole(),
)

compare_notebooks = typer.Typer(
    name="diff_notebooks",
    add_completion=False,
    no_args_is_help=True,
    add_help_option=True,
)


def version_callback(
    version: Annotated[
        bool,
        typer.Option(
            "-v",
            "--version",
            help="Show compare-notebook-dir version",
        ),
    ] = False,
) -> None:  # FBT001
    """Prints the version of the package."""
    if version:
        console.print(f"[yellow]compare-notebook-dir[/] version: [bold blue]{__version__}[/]")
        raise typer.Exit()


# TODO: incorporate merging
@compare_notebooks.command(no_args_is_help=True)
def compare_notebook_dirs(
    path1: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            writable=False,
            readable=True,
            resolve_path=True,
            help="Directory to compare against.",
        ),
    ],
    path2: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            writable=False,
            readable=True,
            resolve_path=True,
            help="Directory to use for comparison",
        ),
    ],
    ext: Annotated[str, typer.Option("--ext", "-e", help="file extension to search for")] = "ipynb",
    recursive: Annotated[bool, typer.Option("--rec", "-r", help="search folders recursively?")] = True,
    view: Annotated[bool, typer.Option("--view", "-w", help="ask to view differences on the command line")] = False,
    web_view: Annotated[bool, typer.Option("--web_view", "-b", help="ask to view differences in web browser")] = False,
    ignore_checkpoints: Annotated[
        bool, typer.Option("--no-checkpoints", "-n", help="Ignore all of the '*-checkpoint.ipynb files'")
    ] = False,
    only_common: Annotated[bool, typer.Option("--common", "-c", help="Ignore missing notebooks.")] = False,
    report: Annotated[
        bool,
        typer.Option(
            "--report", "-p", help="Show a final report of what was the same, what differed, and what was missing"
        ),
    ] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Turn on logging")] = False,
    version: Annotated[
        bool, typer.Option("--version", help="Show version", callback=version_callback, is_eager=True)
    ] = False,
):
    if verbose:
        init_logger(3, save=True)
    else:
        init_logger(0)

    if recursive:
        path1_search = path1.glob(f"**/*.{ext}")
        path2_search = path2.glob(f"**/*.{ext}")
    else:
        path1_search = path1.glob(f"*.{ext}")
        path2_search = path2.glob(f"*.{ext}")

    if ignore_checkpoints:
        path1_found_notebooks = {x.name: x for x in path1_search if not x.name.endswith("-checkpoint.ipynb")}
        path2_found_notebooks = {y.name: y for y in path2_search if not y.name.endswith("-checkpoint.ipynb")}
    else:
        path1_found_notebooks = {x.name: x for x in path1_search}
        path2_found_notebooks = {y.name: y for y in path2_search}

    logger.info(f"found {len(path1_found_notebooks)} at {path1}")
    logger.info(f"found {len(path2_found_notebooks)} at {path2}")

    logger.debug(
        f"{[k for k in path1_found_notebooks.keys() if k not in path2_found_notebooks.keys()]} are exclusive to path1"
    )
    logger.debug(
        f"{[k for k in path2_found_notebooks.keys() if k not in path1_found_notebooks.keys()]} are exclusive to path2"
    )
    progress = Progress(
        "[yellow]Comparing...[/yellow]",
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        TextColumn("{task.description}"),
        console=console,
    )

    progress.start()
    task = progress.add_task("[yellow]Comparing...[/yellow]", total=len(path1_found_notebooks))
    mismatched = {}
    for name, notebook1 in path1_found_notebooks.items():
        progress.update(task, description=f"Reading {name!s}", advance=0)
        if not only_common and (name not in path2_found_notebooks.keys()):
            progress.console.print(f"No matching file was found for {name!s}")
        else:
            logger.debug(f"Comparing {notebook1!s} to {path2_found_notebooks[name]!s}")
            notebook2 = path2_found_notebooks[name]
            try:
                nb1 = read_notebook(str(notebook1), on_null="empty")
            except (JSONDecodeError, NotJSONError):
                msg = f"[red1]{notebook1!s}[/] does not appear to be a valid notebook file!"
                console.print(msg)
                continue
            try:
                nb2 = read_notebook(str(notebook2), on_null="empty")
            except (JSONDecodeError, NotJSONError):
                msg = f"[red1]{notebook2!s}[/] does not appear to be a valid notebook file!"
                console.print(msg)
                continue
            result = diff_notebooks(nb1, nb2)
            if len(result) > 0:
                progress.console.print(
                    f":warning-emoji:[bold red1] Differences were found[/bold red1] for [orange1]{name}[/orange1] :warning-emoji:"
                )
                mismatched[name] = {
                    "notebook1_path": notebook1,
                    "notebook2_path": notebook2,
                    "nb1": nb1,
                    "result": result,
                }
                logger.info(f"the two {name} are different")
            else:
                progress.console.print(f"[bold #00AA00]No differences[/bold #00AA00] found for [blue]{name}[/blue]")
                logger.debug(f"the two {name} match")
        progress.update(task, description=f"Processed {name!s}", advance=1)
    progress.stop()
    deleted_notebooks1 = []
    deleted_notebooks2 = []
    if len(mismatched) > 0 and (view or web_view):
        console.rule("[bold #55AAFF]Examine differences:")
        for name, data in mismatched.items():
            answer = Confirm.ask(
                f"There were differences for [orange1]{name}[/orange1]. Would you like to examine them?",
                console=console,
            )
            if answer:
                if web_view:
                    sockets = bind_sockets(port=0, address="localhost")
                    ip, port = sockets[0].getsockname()
                    console.print(
                        f"If browser does not open automatically, please visit http://{ip}:{port}/diff?base={data['notebook1_path']!s}&remote={data['notebook2_path']!s}"
                    )
                    main_server(
                        on_port=browse(
                            port=port,
                            rel_url="diff",
                            base=str(data["notebook1_path"]),
                            remote=str(data["notebook2_path"]),
                        ),
                        closable=True,
                    )
                if view:
                    # nbdiffapp_main([notebooks[0], notebooks[1]])
                    pretty_print_notebook_diff(
                        afn=data["notebook1_path"].name,
                        bfn=data["notebook2_path"].name,
                        a=data["nb1"],
                        di=data["result"],
                        config=diff_config,
                    )
                    delete_prompt = Prompt.ask(
                        prompt=f"Would you like to delete one of the notebooks? Click \n(1) for {data['notebook1_path']!s} and \n(2) for {data['notebook2_path']!s} or \n(n) for neither.",
                        choices=["1", "2", "n"],
                        default="n",
                        case_sensitive=False,
                        console=console,
                    )
                    match delete_prompt:
                        case "1":
                            data["notebook1_path"].unlink()
                            console.print(f"[red1]Deleted {data['notebook1_path']!s}[/red1]")
                            deleted_notebooks1.append(name)
                        case "2":
                            data["notebook2_path"].unlink()
                            console.print(f"[red1]Deleted {data['notebook2_path']!s}[/red1]")
                            deleted_notebooks2.append(name)
                        case "n":
                            console.print("[yellow]No notebooks deleted[/yellow]")

    if report:
        table = Table()
        table.add_column("Notebook", justify="right", style="cyan", no_wrap=True)
        table.add_column("Status", justify="center", style="cyan", no_wrap=True)
        table.add_column("Path1:", justify="center", style="cyan", no_wrap=True)
        table.add_column("Path2:", justify="center", style="cyan", no_wrap=True)

        unique_notebook_names = {*path1_found_notebooks.keys(), *path2_found_notebooks.keys()}
        for notebook in unique_notebook_names:
            col2 = col3 = col4 = ""
            if notebook in mismatched:
                col2 = "[yellow1]differ[/yellow1]"
            elif notebook not in path1_found_notebooks.keys():
                col3 = "[red1]missing[/red1]"
            elif notebook not in path2_found_notebooks.keys():
                col4 = "[red1]missing[/red1]"
            else:
                col2 = "[#00AA00]same[/#00AA00]"

            if notebook in deleted_notebooks1:
                col3 = "[orange_red1]deleted[/orange_red1]"
            elif notebook in deleted_notebooks2:
                col4 = "[orange_red1]deleted[/orange_red1]"

            table.add_row(notebook, col2, col3, col4)
        console.print(table)
