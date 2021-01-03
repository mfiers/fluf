

def cli():
    import click
    from fluf import prepare_run
    from fluf.cli import core
    prepare_run()
    core.cli()
