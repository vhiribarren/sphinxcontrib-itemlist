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


class req_list(nodes.General, nodes.Element):
    pass


class ReqListDirective(Directive):
    has_content = True
    option_spec = {
        'numbered': directives.flag,
    }
    def run(self):
        req_list_node = req_list()
        req_list_node["numbered"] = "numbered" in self.options
        return [req_list_node]


class req_table(nodes.General, nodes.Element):
    pass


class ReqTableDirective(Directive):
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
        return [req_table(req_table_options=options)]


class ReqDirective(SphinxDirective):
    has_content = True
    required_arguments = 1
    final_argument_whitespace = True

    def run(self) -> Sequence[Node]:

        title = self.arguments[0]

        target_id = f"req-{self.env.new_serialno('req')}"
        target_node = nodes.target('', '', ids=[target_id])

        req_desc_signature = addnodes.desc_signature()
        req_desc_signature += addnodes.desc_name(text=title)
        req_desc_content = addnodes.desc_content()
        self.state.nested_parse(self.content, self.content_offset, req_desc_content)
        req_desc = addnodes.desc()
        req_desc['classes'].append('describe')
        req_desc += req_desc_signature
        req_desc += req_desc_content

        if not hasattr(self.env, 'req_all_reqs'):
            self.env.req_all_reqs = []
        self.env.req_all_reqs.append({
            "title": title,
            "attributes": self.extract_attributes(req_desc_content),
            "target": target_node
        })

        return [target_node, req_desc]

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


def process_req_list_nodes(app, doctree, fromdocname):
    if not hasattr(app.builder.env, 'req_all_reqs'):
        return
    for node in doctree.traverse(req_list):
        result_list = nodes.enumerated_list() if node["numbered"] else nodes.bullet_list()
        for req_info in app.builder.env.req_all_reqs:
            refnode = nodes.reference()
            refnode["refid"] = req_info["target"]["refid"]
            item = nodes.list_item()
            para = nodes.paragraph()
            refnode += nodes.Text(req_info["title"], req_info["title"])
            para += refnode
            item += para
            result_list += item
        node.replace_self(result_list)


def process_req_table_nodes(app, doctree, fromdocname):
    if not hasattr(app.builder.env, 'req_all_reqs'):
        return

    for node in doctree.traverse(req_table):
        headers = node["req_table_options"]["headers"]
        desc_name = node["req_table_options"]["desc_name"]
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
        for req_info in app.builder.env.req_all_reqs:
            row = nodes.row()
            tbody += row
            for header in headers:
                if header == desc_name:
                    entry = nodes.entry()
                    para = nodes.paragraph()
                    refnode = nodes.reference()
                    refnode["refid"] = req_info["target"]["refid"]
                    refnode += nodes.Text(req_info["title"], req_info["title"])
                    entry += para
                    para += refnode
                    row += entry
                    continue
                entry = nodes.entry()
                entry += nodes.paragraph(text=req_info["attributes"][header])
                row += entry
        node.replace_self(result_table)


def setup(app):
    app.add_directive('req', ReqDirective)
    app.add_directive('req_list', ReqListDirective)
    app.add_directive('req_table', ReqTableDirective)
    app.add_node(req_list)
    app.add_node(req_table)
    app.connect('doctree-resolved', process_req_list_nodes)
    app.connect('doctree-resolved', process_req_table_nodes)
    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
