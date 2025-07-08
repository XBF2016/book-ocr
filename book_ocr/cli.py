import typer

app = typer.Typer()

@app.command()  # type: ignore[misc]
def version() -> None:
    """Print package version."""
    import importlib.metadata as importlib_metadata
    typer.echo(importlib_metadata.version("book-ocr"))

def add_numbers(a: int, b: int) -> int:
    # 示例函数
    c = a + b
    return c

if __name__ == "__main__":
    app()  # pragma: no cover
