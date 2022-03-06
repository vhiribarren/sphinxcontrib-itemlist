from docutils import nodes
from docutils.nodes import Node
from typing import Sequence, cast, List
from sphinx.util.docutils import SphinxDirective
from sphinx import addnodes


class ReqDirective(SphinxDirective):

   has_content = True
   required_arguments = 1
   final_argument_whitespace = True

   def run(self) -> Sequence[Node]:
       req_desc_signature = addnodes.desc_signature()
       req_desc_signature += addnodes.desc_name(text=self.arguments[0])
       req_desc_content = addnodes.desc_content()
       self.state.nested_parse(self.content, self.content_offset, req_desc_content)
       self.show_fields(req_desc_content)
       req_desc = addnodes.desc()
       req_desc += req_desc_signature
       req_desc += req_desc_content
       return [req_desc]

   def show_fields(self, desc_content):
       for node in desc_content:
           if not isinstance(node, nodes.field_list):
               continue
           fields = cast(List[nodes.field], node)
           for field in fields:
               field_name = cast(nodes.field_name, field[0]).astext().strip()
               print(field_name)


def setup(app):
    app.add_directive('req', ReqDirective)
    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }