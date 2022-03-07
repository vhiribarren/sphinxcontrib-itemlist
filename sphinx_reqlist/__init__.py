from docutils import nodes
from docutils.nodes import Node
from docutils.parsers.rst import Directive
from typing import Sequence, cast, List, Dict
from sphinx.util.docutils import SphinxDirective
from sphinx import addnodes


class req_list(nodes.General, nodes.Element):
    pass


class ReqListDirective(Directive):
    def run(self):
        return [req_list('')]


class req_table(nodes.General, nodes.Element):
    pass


class ReqTableDirective(Directive):
    def run(self):
        return [req_table('')]


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
        result_list = nodes.bullet_list()
        for req_info in app.builder.env.req_all_reqs:
            item = nodes.list_item()
            item += nodes.paragraph(text=req_info["title"])
            result_list += item
        node.replace_self(result_list)


def process_req_table_nodes(app, doctree, fromdocname):
    if not hasattr(app.builder.env, 'req_all_reqs'):
        return
    for node in doctree.traverse(req_table):
        result_table = nodes.table()
        tgroup = nodes.tgroup()
        tbody = nodes.tbody()
        colspec = nodes.colspec(colwidth=100)
        tgroup += colspec
        tgroup += tbody
        result_table += tgroup
        for req_info in app.builder.env.req_all_reqs:
            row = nodes.row()
            entry = nodes.entry()
            entry += nodes.paragraph(text=req_info["title"])
            row += entry
            tbody += row
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
