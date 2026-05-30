from pathlib import Path
from typing import Annotated

import typer
from loguru import logger
from nbdime.diffing.notebooks import diff_notebooks
from nbdime.utils import read_notebook
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)

from . import __version__
from .logging import init_logger

console = Console()

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

    path1_found_notebooks = {x.name: str(x) for x in path1_search}
    path2_found_notebooks = {y.name: str(y) for y in path2_search}

    logger.info(f"found {len(path1_found_notebooks)} at {path1}")
    logger.info(f"found {len(path2_found_notebooks)} at {path2}")

    logger.debug(
        f"{[k for k in path1_found_notebooks.keys() if k not in path2_found_notebooks.keys()]} are exclusive to path1"
    )
    logger.debug(
        f"{[k for k in path2_found_notebooks.keys() if k not in path1_found_notebooks.keys()]} are exclusive to path2"
    )

    # text_column = TextColumn("{task.description}", table_column=Column(ratio=1))
    # bar_column = BarColumn(bar_width=None, table_column=Column(ratio=2))
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
    try:
        for name, notebook1 in path1_found_notebooks.items():
            # progress.console.print(f"Comparing [blue]{key!s}[/blue]", markup=True)
            progress.update(task, description=str(name), advance=1)
            # with console.capture() as capture:
            if name not in path2_found_notebooks.keys():
                progress.console.print(f"No matching file was found for {name!s}")
            else:
                logger.debug(f"Comparing {notebook1} to {path2_found_notebooks[name]}")
                nb1 = read_notebook(notebook1, on_null="empty")
                nb2 = read_notebook(path2_found_notebooks[name], on_null="empty")
                result = diff_notebooks(nb1, nb2)
                if len(result) > 0:
                    progress.console.print(f"[bold red]Differences were found[/bold red] for {name}")
                    logger.info(f"the two {name} are different")
                else:
                    progress.console.print(f"[bold green]No differences[/bold green] found for [blue]{name}[/blue]")
                    logger.debug(f"the two {name} match")
            # output.append(capture.get())
    finally:
        progress.stop()
    # for x in output:
    #     console.print(x, markup=True)
