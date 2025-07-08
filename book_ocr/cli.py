import typer
app = typer.Typer()

@app.command()
def version():
    """Print package version."""
    import importlib.metadata as importlib_metadata
    typer.echo(importlib_metadata.version("book-ocr"))

if __name__ == "__main__":
    app()  # pragma: no cover
