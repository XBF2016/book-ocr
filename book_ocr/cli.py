import typer
app = typer.Typer()

@app.command()
def version():
    """Print package version."""
    import importlib.metadata as importlib_metadata
    typer.echo(importlib_metadata.version("book-ocr"))

def test_function( a , b  ):
    # 故意引入格式问题和无类型标注
    c=a+b
    return   c

if __name__ == "__main__":
    app()  # pragma: no cover
