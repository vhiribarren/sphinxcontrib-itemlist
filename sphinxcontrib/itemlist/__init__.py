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

__project__ =  "sphinxcontrib-itemlist"
__author__  = "Vincent Hiribarren"
__license__ = "MIT"
__version__ = __import__("pkg_resources").require(__project__)[0].version


from docutils import nodes
from docutils.nodes import Node
from docutils.transforms import Transform
from docutils.parsers.rst import directives
from typing import Sequence, cast, List, Dict
from sphinx.util.docutils import SphinxDirective
from sphinx import addnodes


DEFAULT_FIELDS_SLOT = "itemlist_default_fields"


class ItemListDirective(SphinxDirective):
    has_content = True
    option_spec = {
        'numbered': directives.flag,
        'local': directives.flag,
    }

    def run(self):
        pending = nodes.pending(ItemListNodeTransform)
        pending["numbered"] = "numbered" in self.options
        pending["local"] = "local" in self.options
        pending["docname"] = self.env.docname
        document = self.state_machine.document
        document.note_pending(pending)
        return [pending]


class ItemTableDirective(SphinxDirective):
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
        pending = nodes.pending(ItemTableNodeTransform)
        pending["desc_name"] = desc_name
        pending["headers"] = headers
        pending["local"] = "local" in self.options
        pending["docname"] = self.env.docname
        document = self.state_machine.document
        document.note_pending(pending)
        return [pending]


class SphinxDirectiveEx(SphinxDirective):
    def set_default_itemlist_slot(self, reset=False):
        if not hasattr(self.env, DEFAULT_FIELDS_SLOT):
            setattr(self.env, DEFAULT_FIELDS_SLOT, {})
        if reset or not self.env.docname in getattr(self.env, DEFAULT_FIELDS_SLOT):
            getattr(self.env, DEFAULT_FIELDS_SLOT)[self.env.docname] = {
                "hidden": False,
                "attributes": {},
            }


class ItemDefaultFieldsDirective(SphinxDirectiveEx):
    has_content = True
    option_spec = {
        'hidden': directives.flag,
    }

    def run(self) -> Sequence[Node]:

        hidden = 'hidden' in self.options
        content_node = nodes.paragraph()
        self.state.nested_parse(self.content, self.content_offset, content_node)
        self.set_default_itemlist_slot(reset=True)
        for candidate_node in content_node:
            if isinstance(candidate_node, nodes.field_list):
                break
        else:
            return []
        attributes = {}
        for field in candidate_node:
            field_name = cast(nodes.field_name, field[0]).astext().strip()
            field_body = field[1]
            attributes[field_name] = field_body[0]
        getattr(self.env, DEFAULT_FIELDS_SLOT)[self.env.docname] = {
            "hidden": hidden,
            "attributes": attributes,
        }
        return []


class ItemDirective(SphinxDirectiveEx):
    has_content = True
    required_arguments = 1
    final_argument_whitespace = True

    def run(self) -> Sequence[Node]:

        title = self.arguments[0]

        target_id = f"item-{self.env.new_serialno('item')}"
        target_node = nodes.target('', '', ids=[target_id])

        item_desc = addnodes.desc()
        item_desc['classes'].append('describe')  # To have "describe" or signature directive-like style
        item_desc['objtype'] = "item"
        item_desc_signature = addnodes.desc_signature()
        item_desc_signature += addnodes.desc_name(text=title)
        item_desc_content = addnodes.desc_content()
        item_desc += item_desc_signature
        item_desc += item_desc_content
        self.state.nested_parse(self.content, self.content_offset, item_desc_content)

        self.set_default_itemlist_slot()
        items_defaults_options = getattr(self.env, DEFAULT_FIELDS_SLOT)[self.env.docname]
        attributes = items_defaults_options["attributes"].copy()
        if not items_defaults_options["hidden"]:
            self.add_default_fields(item_desc_content, attributes)
        attributes.update(self.extract_attributes(item_desc_content))
        item_desc['item_info'] = {
            "title": title,
            "docname": self.env.docname,
            "attributes": attributes,
            "target": target_node
        }

        return [target_node, item_desc]

    def add_default_fields(self, item_desc_content, attributes):
        for field_list_node in item_desc_content:
            if isinstance(field_list_node, nodes.field_list):
               break
        else:
            field_list_node = nodes.field_list()
            item_desc_content += field_list_node
        for attribute in attributes:
            for check_field in field_list_node:
                if check_field[0][0].rawsource == attribute:
                    break
            else:
                field = nodes.field()
                field_name = nodes.field_name(text=attribute)
                field_body = nodes.field_body()
                field_body += attributes[attribute]
                field_list_node += field
                field += field_name
                field += field_body

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


def gather_item_infos(root_node: Node, docname: None):
    item_infos = []
    for candidate_node in root_node.traverse(addnodes.desc):
        if candidate_node.get("objtype", None) == "item":
            if docname is None or candidate_node["item_info"]["docname"] == docname:
                item_infos.append(candidate_node["item_info"])
    return item_infos


class ItemListNodeTransform(Transform):
    default_priority = 999

    def apply(self) -> None:
       item_list_node = self.startnode
       item_list_docname = item_list_node["docname"]
       scope_node = item_list_node.parent if item_list_node["local"] else self.document
       item_infos = gather_item_infos(scope_node, item_list_docname)
       if len(item_infos) == 0:
           item_list_node.parent.remove(item_list_node)
           return
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


class ItemTableNodeTransform(Transform):
    default_priority = 999

    def apply(self) -> None:
        item_table_node = self.startnode
        item_table_docname = item_table_node["docname"]
        scope_node = item_table_node.parent if item_table_node["local"] else self.document
        item_infos = gather_item_infos(scope_node, item_table_docname)
        if len(item_infos) == 0:
            item_table_node.parent.remove(item_table_node)
            return
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
    app.add_directive('item_default_fields', ItemDefaultFieldsDirective)
    return {
        'version': __version__,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
