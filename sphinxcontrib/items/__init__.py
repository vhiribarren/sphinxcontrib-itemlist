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
        'local': directives.flag,
    }

    def run(self):
        item_list_node = item_list()
        item_list_node["numbered"] = "numbered" in self.options
        item_list_node["local"] = "local" in self.options
        return [item_list_node]


class ItemTableDirective(Directive):
    has_content = True
    option_spec = {
        'headers': directives.unchanged_required,
        'desc_name': directives.unchanged_required,
        'local': directives.flag,
    }

    def run(self):
        desc_name = self.options["desc_name"] if "desc_name" in self.options else "Title"
        headers = []
        if "headers" in self.options:
            headers = [h.strip() for h in self.options.get('headers').split(',')]
        if desc_name not in headers:
            headers.insert(0, desc_name)
        item_table_node = item_table()
        item_table_node["desc_name"] = desc_name
        item_table_node["headers"] = headers
        item_table_node["local"] = "local" in self.options
        return [item_table_node]


class ItemDirective(SphinxDirective):
    has_content = True
    required_arguments = 1
    final_argument_whitespace = True

    def run(self) -> Sequence[Node]:

        title = self.arguments[0]

        target_id = f"item-{self.env.new_serialno('item')}"
        target_node = nodes.target('', '', ids=[target_id])

        item_desc = addnodes.desc()
        item_desc['classes'].append('describe') # To have "describe" or signature directive-like style
        item_desc['objtype'] = "item"
        item_desc_signature = addnodes.desc_signature()
        item_desc_signature += addnodes.desc_name(text=title)
        item_desc_content = addnodes.desc_content()
        item_desc += item_desc_signature
        item_desc += item_desc_content
        self.state.nested_parse(self.content, self.content_offset, item_desc_content)

        item_desc['item_info'] = {
            "title": title,
            "attributes": self.extract_attributes(item_desc_content),
            "target": target_node
        }

        return [target_node, item_desc]

    def extract_attributes(self, desc_content: addnodes.desc_content) -> Dict[str, nodes.Node]:
        attributes: Dict[str, nodes.Node] = {}
        for node in desc_content:
            if not isinstance(node, nodes.field_list):
                continue
            fields = cast(List[nodes.field], node)
            for field in fields:
                field_name = cast(nodes.field_name, field[0]).astext().strip()
                field_body = field[1]
                attributes[field_name] = field_body[0]
        return attributes


def gather_item_infos(root_node: Node):
    item_infos = []
    for candidate_node in root_node.traverse(addnodes.desc):
        if candidate_node.get("objtype", None) == "item":
            item_infos.append(candidate_node["item_info"])
    return item_infos


def process_item_list_nodes(app, doctree, docname):
    for item_list_node in doctree.traverse(item_list):
        scope_node = item_list_node.parent if item_list_node["local"] else doctree
        item_infos = gather_item_infos(scope_node)
        if len(item_infos) == 0:
            item_list_node.replace_self(nodes.paragraph())
            continue
        result_list = nodes.enumerated_list() if item_list_node["numbered"] else nodes.bullet_list()
        for item_info in item_infos:
            refnode = nodes.reference()
            refnode["refid"] = item_info["target"]["refid"]
            list_item = nodes.list_item()
            para = nodes.paragraph()
            refnode += nodes.Text(item_info["title"], item_info["title"])
            para += refnode
            list_item += para
            result_list += list_item
        item_list_node.replace_self(result_list)


def process_item_table_nodes(app, doctree, docname):
    for item_table_node in doctree.traverse(item_table):
        scope_node = item_table_node.parent if item_table_node["local"] else doctree
        item_infos = gather_item_infos(scope_node)
        if len(item_infos) == 0:
            item_table_node.replace_self(nodes.paragraph())
            continue
        headers = item_table_node["headers"]
        desc_name = item_table_node["desc_name"]
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
        for item_info in item_infos:
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
                entry += item_info["attributes"].get(header, nodes.paragraph())
                row += entry
        item_table_node.replace_self(result_table)


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
