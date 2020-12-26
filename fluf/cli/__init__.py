
import click

import fluf

GLOPTIONS = []

def option(name, **kwargs):
    global GLOPTIONS
    GLOPTIONS[name, kwargs]


def cli():
    """ Run a fluffy CLI """

    from fluf.cli import core

    for oname, oargs in GLOPTIONS.items():
        click.option('--' + oname, **oargs)(core.cli)

    for func in fluf.FUNCTIONS:
        import inspect
        fsig = inspect.signature(func)
        useable = True
        for par in fsig.parameters.keys():
            ann = fsig.parameters[par].annotation
            if ann not in (int, str, float):
                useable = False
        if useable:
            #cmd = click.pass_context(func)
            cmd = core.cli.command(name=func.__name__)(func)

            for par in fsig.parameters.keys():
                ann = fsig.parameters[par].annotation
                default = fsig.parameters[par].default
                pardata = fsig.parameters[par]
                opargs = dict(type=ann)
                if default != inspect._empty:
                    opargs['default'] = default
                cmd = click.option('--' + par, **opargs)(cmd)

    q = core.cli()
