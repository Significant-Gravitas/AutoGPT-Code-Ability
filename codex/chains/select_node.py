import logging
from typing import List, Optional, Dict, Type, TypeVar

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.pydantic_v1 import BaseModel
from codex.chains.gen_branching_graph import NodeDef
from codex.model import Node
from tenacity import retry, stop_after_attempt, wait_none

logger = logging.getLogger(__name__)

model = ChatOpenAI(
    temperature=1,
    model_name="gpt-4-1106-preview",
    max_tokens=4095,
    model_kwargs={"top_p": 1, "frequency_penalty": 0, "presence_penalty": 0},
).bind(**{"response_format": {"type": "json_object"}})


class SelectNode(BaseModel):
    node_id: str
    input_map: Optional[Dict[str, str]]
    output_map: Optional[Dict[str, str]]

    def __str__(self) -> str:
        out = "Node ID: " + self.node_id + "\n"
        if self.input_map:
            out += "Input Map:\n"
            for k, v in self.input_map.items():
                out += f"\t{k} -> {v}\n"
        if self.output_map:
            out += "Output Map:\n"
            for k, v in self.output_map.items():
                out += f"\t{k} -> {v}\n"
        return out


T = TypeVar("T", bound=BaseModel)


class ValidatingPydanticOutputParser(PydanticOutputParser[T]):
    """Parse an output using a pydantic model."""

    pydantic_object: Type[T]
    possible_nodes: List[Node]
    requested_node: NodeDef

    class Config:
        arbitrary_types_allowed = True

    def validate_selected_node(
        cls,
        select_node: SelectNode,
    ) -> bool:
        selected_node = None
        if select_node.node_id == "new":
            return True
        else:
            selected_node = cls.possible_nodes[int(select_node.node_id)]

        input_types = set([p.param_type for p in cls.requested_node.input_params])
        output_types = set([p.param_type for p in cls.requested_node.output_params])
        
        selected_input_types = set([p.param_type for p in selected_node.input_params])
        selected_output_types = set([p.param_type for p in selected_node.output_params])
        
        if input_types != selected_input_types:
            logger.error(
                f"🚫 The Selected Node does not have all the required input types: {selected_node.name}"
            )
            return False

        if output_types != selected_output_types:
            logger.error(
                f"🚫 The Selected Node does not have all the required output types: {selected_node.name}"
            )
            return False
        
        # First check if the node_details and node_def have matching number of input and output params
        if len(selected_node.input_params) != len(cls.requested_node.input_params):
            logger.error(
                f"🚫 Node details and node def have different number of input params: {selected_node.name}"
            )
            return False

        if len(selected_node.output_params) < len(cls.requested_node.output_params):
            logger.error(
                f"🚫 The Selected Node has less output params than required: {selected_node.name}"
            )
            return False

        # Next check the validity of the input map:
        for key, value in select_node.input_map.items():
            if key not in [n.name for n in selected_node.input_params]:
                logger.error(f"🚫 Input map contains invalid key: {key}")
                return False
            if value not in [n.name for n in cls.requested_node.input_params]:
                logger.error(f"🚫 Input map contains invalid value: {value}")
                return False

        # Next check if the output map is valid:
        for key, value in select_node.output_map.items():
            if key not in [n.name for n in selected_node.output_params]:
                logger.error(f"🚫 Output map contains invalid key: {key}")
                return False
            if value not in [n.name for n in cls.requested_node.output_params]:
                logger.error(f"🚫 Output map contains invalid value: {value}")
                return False

        return True

    def parse(self, text: str) -> T:
        obj = super().parse(text)
        if not self.validate_selected_node(obj):
            raise ValueError("Invalid node selected")
        return obj


@retry(wait=wait_none(), stop=stop_after_attempt(3))
def chain_select_from_possible_nodes(
    nodes_str: str,
    requested_node: NodeDef,
    avaliable_inpurt_params: str,
    possible_nodes: List[Node],
):
    parser_select_node = PydanticOutputParser(
        pydantic_object=SelectNode,
        possible_nodes=possible_nodes,
        requested_node=requested_node,
    )
    prompt_select_node = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Your are an expect at node selection. You are to decide if one of the nodes presented to you fits the requirement.\nReply in json format: {format_instructions}\n Note: if no node matches the requirement reply with `new` as the node_id.",
            ),
            (
                "human",
                """
    Thinking carefully step by step. Select a node if it meets the requirement and provide a mapping between the selected nodes input and outputs and node specified in the requirements.

    If there are no possible nodes that have all the Avaliable Input Params then reply with `new` as the node_id.

    # Possible Nodes
    {nodes}

    # Requirement
    {requirement}

    # Avaliable Input Params
    {avaliable_params}

    # Required Output Params
    {required_output_params}

    ## IMPORTANT!
    The selected node all node inputs must be mapped to avaliable input params. If there are missing input params then the node is not a match.
    The node must have all required output params. If there are missing output params then the node is not a match.
    """,
            ),
        ]
    ).partial(format_instructions=parser_select_node.get_format_instructions())
    chain = prompt_select_node | model | parser_select_node

    return chain.invoke(
        {
            "nodes": nodes_str,
            "requirement": requested_node,
            "avaliable_params": avaliable_inpurt_params,
            "required_output_params": requested_node.output_params,
        }
    )
