---
comments: true
---

# Advanced Developer Guide
**@Aidan, does the Export Section still apply?** Seems like it might already be covere in the [building and publishing guide](../guides/build.md)

-----
(PT removed this section from `index.md` and stuck it here for now)

To make a dictionary from your data, you need to do the following three
things:

1.  Install mothertongues, see [installation](install.md).
2.  Write a valid Mother Tongues Language configuration file. See
    [guides](../guides/index.md)
3.  Write valid Mother Tongues data resource configuration files. See
    [guides](../guides/index.md)

Then, build with the command line:

```bash
mothertongues build-and-run <path_to_language_configuration>
```

And open your browser at `localhost:3636` to see your dictionary.

Exporting a Dictionary
----------------------

Finally, you can export your dictionaries to JSON to be used with an MTD frontend using the command line:

```bash
mothertongues export <path_to_language_configuration> <output_dir>
```
