

import click

import fluf
from fluf import db

from fluf.helpers import set_workfolder


@click.group()
@click.option('-w', '--workfolder', default='.')
@click.pass_context
def cli(ctx, **kwargs):
    ctx.ensure_object(dict)
    ctx.obj['WORKFOLDER'] = workfolder

    for k, v in kwargs.items():
        ctx.obj[k] = v



@cli.group("fluf")
@click.pass_context
def fcli(ctx):
    """Command fluf"""
    ctx.ensure_object(dict)


@fcli.command()
@click.pass_context
def functions(ctx):
    from rich import print as rprint
    from rich.console import Console
    from rich.table import Table
    # ensure callstack is up to date
    set_workfolder(ctx.obj['WORKFOLDER'])

    table = Table()
    table.add_column('Name', style="deep_sky_blue3")
    table.add_column('Check\nSum', style="dark_sea_green4")
    table.add_column('No\ncalls', style="white")
    table.add_column('No dirty\ncalls', style="red")
    table.add_column('Times\ncalled', style="blue")
    table.add_column('Times\ncalling', style="blue")


    for f in fluf.DBFUNCS:
        c = db.FunctionCall.select()\
            .where(db.FunctionCall.function == f)
        nocalls = c.count()
        c = c.where(db.FunctionCall.dirty)
        nodirty = c.count()
        nodirty = str(nodirty) if nodirty > 0 else ''

        FCF = db.FunctionCallFunction
        c = FCF.select().join(db.FunctionCall, on=FCF.called)\
            .where(db.FunctionCall.function == f)
        called = c.count()
        c = FCF.select().join(db.FunctionCall, on=FCF.caller)\
            .where(db.FunctionCall.function == f)
        caller = c.count()


        table.add_row(f.name, f.checksum, str(nocalls), nodirty, str(called),
                      str(caller))

    Console().print(table)
