
from datetime import datetime
import logging

import click
import humanfriendly

from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.markdown import Markdown

lgr = logging.getLogger(__name__)
import fluf
from fluf.models import (Call, Function, CallCall, Invocation,
                         CallArg)


@click.group()
@click.pass_context
def cli(ctx, **kwargs):
    ctx.ensure_object(dict)


@cli.group("fluf")
@click.pass_context
def fcli(ctx):
    """Command fluf"""
    ctx.ensure_object(dict)


@fcli.command()
@click.argument("gml")
@click.pass_context
def export_graph(ctx, gml):
    import networkx as nx
    G = nx.DiGraph()

    for f in Function:
        fname = str(f.uid)
        G.add_node(fname, dtype='function', name=f.name,
                   created=str(f.created))

        for c in Call.select().where(Call.function == f):
            cname = c.uid
            G.add_node(cname, dtype='call')
            G.add_edge(fname, cname)

    for cc in CallCall:
        G.add_edge(cc.caller.uid, cc.called.uid)

    nx.write_graphml(G, gml)

@fcli.command()
@click.pass_context
def functions(ctx):
    """
    Show a list of known functions
    """

    table = Table()
    table.add_column('Name', style="deep_sky_blue3")
    table.add_column('Current Uid', style="deep_sky_blue3")
    table.add_column('Versions', style="deep_sky_blue3")
    table.add_column('Calls', style="deep_sky_blue3")

    all_func_names = Function.select(Function.name).distinct()
    all_func_names = set([x.name for x in all_func_names])

    for func in fluf.app.logger.functions:
        f = func.ffunc
        c = Call.select()\
                .where(Call.function == f)
        nocalls = c.count()
        novers = str(Function.select()
                     .where(Function.name == f.name)
                     .count())
        all_func_names.remove(f.name)
        table.add_row(f.name, f.uid, novers, str(nocalls))

    for func_name in sorted(all_func_names):
        novers = str(Function.select()
                     .where(Function.name == func_name)
                     .count())
        table.add_row(func_name, "[grey42]<historical>[/grey42]", novers, "")

    Console().print(table)


@fcli.command()
@click.argument('call')
@click.pass_context
def call(ctx, call):
    """
    Show information on a recent call
    """
    hash_length = fluf.app.config['hash_length']
    if len(call) == hash_length + 1 and call[0] == 'f':
        # looks like a function hash
        ffunc = Function.select().where(
            Function.uid == call).get()
 #       fcall = Call.select().where(
 #           Call.function == ffunc)\
 #           .order_by
#    if len(call)


@fcli.command()
@click.argument('func_name')
@click.pass_context
def function(ctx, func_name):
    """
    Show a list of known functions
    """

    table = Table()
    table.add_column('Name', style="deep_sky_blue3")
    table.add_column('Uid', style="deep_sky_blue3")
    table.add_column('Calls', style="deep_sky_blue3")

    hash_length = fluf.app.config['hash_length']
    ffunc = None
    if len(func_name) == hash_length + 1 and func_name[0] == 'f':
        ffunc = Function.select().where(
            Function.uid == func_name).get()

        lgr.debug(f"Using func: {ffunc}")

    if ffunc is None:
        ffunc = Function.select()\
                        .where(Function.name == func_name)\
                        .order_by(-Function.created)\
                        .get()
        lgr.debug(f"Using func: {ffunc}")

    if ffunc is None:
        lgr.warning(f"Function not found: {func_name}")
        exit(-1)

    console = Console()
    console.print(f"[red3]Function:[/red3] {ffunc.name} -- {ffunc}")

    console.print(Markdown("---"))
    syntax = Syntax(ffunc.code, 'python')
    console.print(syntax)
    console.print(Markdown("---"))

    console.print("[red3]Function Versions[/red3]")
    for i, v in enumerate(Function.select()
                          .where(Function.name == ffunc.name)
                          .order_by(-Function.created)
                          .limit(5)):
        current = "[yellow]*current*[/yellow]" if i == 0 else ""
        since_created = humanfriendly.format_timespan(
            datetime.now() - v.created, detailed=False, max_units=1)
        console.print(f" - {v.uid} -- {since_created} ago  {current}")

    console.print("[red3]Calls[/red3]")
    for i, call in enumerate(Call.select()
                          .where(Call.function == ffunc)
                          .order_by(-Call.created).limit(5)):
        since_created = humanfriendly.format_timespan(
            datetime.now() - v.created, detailed=False, max_units=1)
        console.print(f" - [red3]Call:[/red3] {call} "
                      f"created {since_created} ago")

        callargs = CallArg.select().where(CallArg.call == call)
        if callargs:
            console.print("   [dark_orange]Arguments:[/dark_orange]")

        for arg in callargs:
            console.print(f"     * {arg.name} = {arg.val}")

        calling = CallCall.select().join(Call, on=CallCall.caller)\
                                   .where(CallCall.caller == call)\
                                   .order_by(Call.created)\
                                   .limit(5)
        if calling:
            console.print("   [dark_orange]Calling:[/dark_orange]")
            for cc in calling:
                hist = " [grey42]historical[/grey42]" if cc.historical else ""

                console.print(f"     * {cc.called.uid} function: "
                              f"{cc.called.function.name} "
                              f"{cc.called.function.uid}{hist}")

        calledby = CallCall.select().where(
            CallCall.called == call)
        if calledby:
            console.print("   [dark_orange]Called by:[/dark_orange]")
            for c in calledby:
                console.print(f"     * {c.caller.uid} function: "
                              f"{c.caller.function.name} "
                              f"{c.caller.function.uid}")

    console.print(f"[red3]Invocations:[/red3] {ffunc.name} -- {ffunc}")
    Invoc = Invocation.select().join(Call).join(Function)\
        .where(Function.uid == ffunc.uid)\
        .order_by(-Invocation.start)\
        .limit(5)
    for inv in Invoc:
        since_started = humanfriendly.format_timespan(
            datetime.now() - inv.start, detailed=False, max_units=1)

        try:
            duration = humanfriendly.format_timespan(
                inv.end - inv.start, detailed=False, max_units=1)
        except:
            duration = 'Unknown duration??'

        console.print(f" - {inv.call.uid} started {inv.start} {since_started} ago,"
                      f" took {duration} {inv.success}")
