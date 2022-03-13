# sphinxcontrib-itemlist

Sphinx extension to create a list or table of different items marked with a
special `.. item::` directive.

This extension is quite similar to the `.. contents::` directive, since its
purpose is to create a list of shortcuts to different targets.

The main differences with `contents` are:

- possibility to create a summary table or a list, not only a list
- not restricted to list sections, so not necessary to artifically create sections

## Usage

Some examples are in the `demo/` folder.

Items you want to be referenced in a list or table must use the `.. item::` directive:

    .. item:: This is an Item title

        This is the long description of the Item.

        :Tag: Arbitrary tag
        :Category: My arbitrary category 

The field list can be used when generating a table to add extra columns with their contents.

All `item` of a page can then be collected.

For a list:

    .. item_list::

For a table:

    .. item_table::

### List options

- `:numbered:` uses numbers instead of bullet points
- `:local:` instead of collecting `item` from all the page, only collect the ones from the current section

Example with all options:

    .. item_list::
        :numbered:
        :local:

### Table options

- `:local:` instead of collecting `item` from all the page, only collect the ones from the current section
- `:headers:` which columns to add to the table ; the fields added in the `item` are used for that,
  separated with a comma
- `:desc_name:` set a title for the column containing the first line of the `item` directive ; once set, it can be
  used in the `:headers:` option to organize the column order

Example with all options:

    .. item_table::
        :local:
        :headers: Tag, Description, Category
        :desc_name: Description

### Default fields

When used with the table, it is possible to add implicit fields with `item`, when a success of `item` should
have some common fields. To introduce a new scope with default fields:

    .. item_default_fields::

        :Tag: Default tag

To stop adding a default field, just create a new scope with any fields:

    .. item_default_fields::

Caveat: when defining default fields, there must be a new line between the directive and the field list. Otherwise
there are considered options of the directive.

Possible options:

- `:hidden:` Does not add the default fields in the `item`` only in the table.

Example with option and default fields:

    .. item_default_fields::
        :hidden:

        :Tag: Default tag


## Installation

    $ pip install sphinxcontrib-itemlist

Then add in your Sphinx `conf.py` file:

    extensions = [ "sphinxcontrib.itemlist" ]

## Alternatives

Some alternatives I found:

- [sphinxcontrib-needs](https://sphinxcontrib-needs.readthedocs.io)
    - missed it at first look, not referenced in official ``contrib`` repository
    - too heavyweight for my needs

- [sphinxcontrib-requirements](https://github.com/sphinx-contrib/requirements)
    - goal and result is a bit different, too specific