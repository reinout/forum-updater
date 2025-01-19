# forum-updater

Forum downloader/updater, mostly for restoring abload.de images on
stummiforum.de. So... some things are hardcoded for my personal purpose. It *might* be
useful for others, though :-)

Before shutting down, abload.de allowed you to download a big zipfile with all your
images. I did this, of course, and added them to my own website like
https://reinout.vanrees.org/abload/screenshot2020-03-30a04jqt.png .


## Installation

[Download and install](https://docs.astral.sh/uv/getting-started/installation/) `uv`,
that's a nice modern way of installing python projects:

    $ uv sync


## Usage

Create a directory somewhere, looking like this:

```
.
└── stummi
    ├── eifelburgenbahn
    │   └── thread.toml
    ├── eifeler-geschichten
    │   └── thread.toml
    ├── einfache-bu-mit-het-hat
    │   └── thread.toml
    └── site.toml
```

So a main dir (`stummi` in my case) with a `site.toml`:

    site_type = "stummi"
    base_url = "https://www.stummiforum.de"
    username = "reinout"

At the moment, only the "stummi" site type is supported/hardcoded. Apart from the
username, a password is also needed, of course. I don't want it in a config file on my
disk, so that one gets read from an environment variable named after the directory
name. In this case `STUMMI_PASSWORD`. If missing, you'll get a helpful error message.

The subdirs (like `eifelburgenbahn`) are for your forum threads. I don't know how to
look at all my own messages, so I'm just iterating over specific threads. Name the
directory however you want and add a `thread.toml`:

    first_page_url = "https://www.stummiforum.de/t134944f64-RE-Eifelburgenbahn-eingleisige-Nebenbahn-in.html"
    num_pages = 75

I'm too lazy to read the number of pages, so you'll have to enter it yourself. The URL
of the first page is used to extract the ID of the thread.

Now call the script:

    $ uv run src/forum_updater/script.py download ../forum-contents/stummi/eifelburgenbahn/

The "download" action downloads the pages (resulting in a list of IDs of posts you've
authored). It then downloads your posts and puts them in `.txt` files:

```
└── stummi
    ├── aus-dem-westen-etwas-neues
    │   ├── pages
    │   │   └── 001.json
    │   ├── posts
    │   │   ├── 0001.txt
    │   │   └── 0002.txt
    │   └── thread.toml
    ...
```

You can call it multiple times, pages or posts that already exist are skipped. If you
want to re-download, just remove the files first to trigger a re-download.

Then call the fix-abload action:

    $ uv run src/forum_updater/script.py fix-abload ../forum-contents/stummi/eifelburgenbahn/

That will go through the `.txt` files, find the abload image urls and replace them with
(in my case, hardcoded) urls like
https://reinout.vanrees.org/abload/screenshot2020-03-30a04jqt.png . Every `.txt` with an
abload url will get a `.txt-updated` next to it with the fixed text. **Check this for a
couple of files**.

Lastly, call the update action:

    $ uv run src/forum_updater/script.py update ../forum-contents/stummi/eifelburgenbahn/

This looks for those `.txt-updated` files and replaces the text on the forum with the
new one. After every update, it removes the original and the updated `.txt` file. The
idea is that you'll call "download" afterwards to grab fresh copies of the posts.

You'll probably get a timeout or so halfway through. When it happens, first do
"download" again as the script doesn't like missing files. Then "update" again.
