# MIT License
#
# Copyright (c) 2022 Vincent Hiribarren
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from docutils import nodes
from docutils.nodes import Node
from docutils.parsers.rst import Directive, directives
from typing import Sequence, cast, List, Dict
from sphinx.util.docutils import SphinxDirective
from sphinx import addnodes


class item_list(nodes.General, nodes.Element):
    pass

class item_table(nodes.General, nodes.Element):
    pass

class ItemListDirective(Directive):
    has_content = True
    option_spec = {
        'numbered': directives.flag,
    }
    def run(self):
        item_list_node = item_list()
        item_list_node["numbered"] = "numbered" in self.options
        return [item_list_node]

class ItemTableDirective(Directive):
    has_content = True
    option_spec = {
        'headers': directives.unchanged_required,
        'desc_name': directives.unchanged_required,
    }
    def run(self):
        desc_name = self.options["desc_name"] if "desc_name" in self.options else "Title"
        headers = []
        if "headers" in self.options:
            headers = [ h.strip() for h in self.options.get('headers').split(',')]
        if desc_name not in headers:
            headers.insert(0, desc_name)
        options = {
            "headers": headers,
            "desc_name": desc_name
        }
        return [item_table(item_table_options=options)]


class ItemDirective(SphinxDirective):
    has_content = True
    required_arguments = 1
    final_argument_whitespace = True

    def run(self) -> Sequence[Node]:

        title = self.arguments[0]
        docname = self.env.docname

        target_id = f"item-{self.env.new_serialno('item')}"
        target_node = nodes.target('', '', ids=[target_id])

        item_desc_signature = addnodes.desc_signature()
        item_desc_signature += addnodes.desc_name(text=title)
        item_desc_content = addnodes.desc_content()
        self.state.nested_parse(self.content, self.content_offset, item_desc_content)
        item_desc = addnodes.desc()
        item_desc['classes'].append('describe')
        item_desc += item_desc_signature
        item_desc += item_desc_content

        if not hasattr(self.env, 'items_all_items'):
            self.env.items_all_items = {}
        if not docname in self.env.items_all_items:
            self.env.items_all_items[docname] = []
        self.env.items_all_items[docname].append({
            "title": title,
            "docname": self.env.docname,
            "attributes": self.extract_attributes(item_desc_content),
            "target": target_node
        })

        return [target_node, item_desc]

    def extract_attributes(self, desc_content: addnodes.desc_content) -> Dict[str, str]:
        attributes: Dict[str, str] = {}
        for node in desc_content:
            if not isinstance(node, nodes.field_list):
                continue
            fields = cast(List[nodes.field], node)
            for field in fields:
                field_name = cast(nodes.field_name, field[0]).astext().strip()
                field_body = cast(nodes.field_body, field[1]).astext().strip()
                attributes[field_name] = field_body
        return attributes


def process_item_list_nodes(app, doctree, from_docname):
    for node in doctree.traverse(item_list):
        if not from_docname in app.builder.env.items_all_items:
            node.replace_self(nodes.paragraph())
            continue
        result_list = nodes.enumerated_list() if node["numbered"] else nodes.bullet_list()
        for item_info in app.builder.env.items_all_items[from_docname]:
            refnode = nodes.reference()
            refnode["refid"] = item_info["target"]["refid"]
            list_item = nodes.list_item()
            para = nodes.paragraph()
            refnode += nodes.Text(item_info["title"], item_info["title"])
            para += refnode
            list_item += para
            result_list += list_item
        node.replace_self(result_list)


def process_item_table_nodes(app, doctree, from_docname):
    for node in doctree.traverse(item_table):
        if not from_docname in app.builder.env.items_all_items:
            node.replace_self(nodes.paragraph())
            continue
        docname_items = app.builder.env.items_all_items[from_docname]
        headers = node["item_table_options"]["headers"]
        desc_name = node["item_table_options"]["desc_name"]
        result_table = nodes.table()
        tgroup = nodes.tgroup()
        thead = nodes.thead()
        thead_row = nodes.row()
        thead += thead_row
        tbody = nodes.tbody()
        for header in headers:
            colspec = nodes.colspec(colwidth=1)
            tgroup += colspec
            entry = nodes.entry()
            entry += nodes.paragraph(text=header)
            thead_row += entry
        result_table += tgroup
        tgroup += thead
        tgroup += tbody
        for item_info in docname_items:
            row = nodes.row()
            tbody += row
            for header in headers:
                if header == desc_name:
                    entry = nodes.entry()
                    para = nodes.paragraph()
                    refnode = nodes.reference()
                    refnode["refid"] = item_info["target"]["refid"]
                    refnode += nodes.Text(item_info["title"], item_info["title"])
                    entry += para
                    para += refnode
                    row += entry
                    continue
                entry = nodes.entry()
                entry += nodes.paragraph(text=item_info["attributes"].get(header, ""))
                row += entry
        node.replace_self(result_table)


def setup(app):
    app.add_directive('item', ItemDirective)
    app.add_directive('item_list', ItemListDirective)
    app.add_directive('item_table', ItemTableDirective)
    app.add_node(item_list)
    app.add_node(item_table)
    app.connect('doctree-resolved', process_item_list_nodes)
    app.connect('doctree-resolved', process_item_table_nodes)
    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
