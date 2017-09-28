# Flapjack #

Flapjack is a tool that lets you hack on one or more of the components
inside a flatpak runtime.
You can make changes to the components and build a new "development
SDK" with your changed components.
You can then test your flatpak apps by running them against the
development SDK.

## Setting up your development environment ##

Install Flapjack with `pip3 install --user flapjack`.

Flapjack requires only Python 3.4 or later, Git, Flatpak, and
Flatpak-builder.
It does not require any other Python modules to run.
For installation, it requires pip or setuptools.

If you want, create a configuration file in `~/.config/flapjack.ini`.
Use the [`example.flapjack.ini`][1] as a template if you need to.
Out of the box, Flapjack is configured to work on the core platform
from the GNOME SDK.
The example file shows how to configure it for the Endless OS apps SDK.

Run `flapjack setup` to perform one-time setup.
This will install the base SDK that you are going to be modifying.
It will probably take a while.

## Using Flapjack ##

Flapjack is a command-line tool with several subcommands.
Run `flapjack --help` to get an overview of the subcommands.

The most basic thing you can do is to build your development runtime.
Run `flapjack build` to do that.
This builds a runtime without any modified components.
It's basically equivalent to the base SDK (although you can add
developer tools to it; see "Developer tools" below.)

Now, `flapjack run` will run a flatpak app against the development SDK
that you just built: for example, `flapjack run org.gnome.gedit`.
Since nothing has changed yet, this will not be very enlightening.

## Developing a component ##

As a tutorial, we will perform the [well-known trick of running GEdit
with all the labels upside-down][2].
We'll build a development SDK with a modified GTK that will do this,
and run GEdit against the development SDK.

For this, you have to indicate that you want to modify GTK.
Do this with `flapjack open gtk3`.
This will put a git clone of GTK in `~/flapjack/checkout/gtk3`.

For a list of other modules that are available to modify, do
`flapjack list`.
Note that `gtk3` is now shown with an asterisk, indicating that it is
open.

Let's now make the change in GTK.
Go into `~/flapjack/checkout/gtk3/gtk/gtklabel.c`, search for
`label_props[PROP_ANGLE]`, and change the last `0.0` in that paragraph
to `180.0` to set the default angle for labels to be upside-down.
Also add `priv->angle = 180.0;` to the end of the `gtk_label_init`
function.

Then, save the file and do `flapjack build` to build the development SDK
again with our modified copy of GTK.
You don't need to make a git commit, Flapjack will build whatever the
current state of the tree is.
When it's done, `flapjack run org.gnome.gedit` should run GEdit against
the development SDK, which now shows labels upside-down!

To test your modifications, you can also do `flapjack test gtk3` to run
`make check` while building GTK.
If a module's tests don't usually run in a sandbox, then they might not
work out of the box.
The `flapjack test` command has some extra options in case you need to
debug the tests or run distcheck instead.
Use `flapjack test --help` to see them.

When you are done modifying GTK, do `flapjack close gtk3` and open
a different module.
You can also have more than one module open at the same time, since it
often happens that changes in one module have effects on another one.

# Miscellaneous commands #

Doing `flapjack shell` will open a shell inside the sandbox of the
development SDK that you have built.
You can use this to poke around and see what's installed.

The `flapjack update` command will make sure you have the latest version
of the base SDK and do a `git fetch` in all of your checkouts.

# Developer tools #

You can also include extra developer tools in your development SDK.
As an example, here's how to include the [`jq`][3] utility.

Add this to your `~/.config/flapjackconfig.py` configuration file:
```python
import os.path
dev_tools_manifest = os.path.join(workdir, 'devtools.json')
```

Then, create a file in `~/flapjack/devtools.json` with the following
contents:
```json
[
    {
        "name": "jq",
        "sources": [
            {
                "type": "archive",
                "url": "https://github.com/stedolan/jq/releases/download/jq-1.5/jq-1.5.tar.gz",
                "sha256": "c4d2bfec6436341113419debf479d833692cc5cdab7eb0326b5a4d4fbe9f493c"
            }
        ]
    }
]
```

Run `flapjack build`.
Even though no modules are open for development, the development SDK
sandbox will still contain the `jq` tool.
You can verify this with `flapjack shell`.

[1]: https://github.com/endlessm/flapjack/blob/master/example.flapjack.ini
[2]: http://www.youtube.com/watch?v=70Kl9ft5DGA&t=40m4s
[3]: https://stedolan.github.io/jq/
