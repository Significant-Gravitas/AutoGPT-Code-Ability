from .utils.QAFormat import Q_AND_A_FORMAT


MODULE_REFINEMENTS = """You are a system architect. Your goal is to refine modules into more detail based on the input and limitations provided

you will reply in the following format, making sure all fields are fully filled and fitted and all existing modules are covered
<modules>
    <module>
        <module_name>Module Name</module_name>
        <rough_requirements>requirements that have been sent that apply to this module</rough_requirements>
        <thoughts>your thoughts on how to refine the module</thoughts>
        <new_description>the new module description</new_description>
        <module_requirements_list>
            <requirement>
                <name>The name of the requirement</name>
                <description>the description of the requirement</description>
            </requirement>
            ... additional requirements for the module
        </module_requirements_list>
        <module_links>
        [names, of, existing, modules, this, one, will, need, to, work, with]
        </module_links>
        <endpoint_groups_list>list of groups of endpoints that will need to be defined</endpoint_groups_list>
        <endpoints>
            <endpoint_group>
                <endpoint>
                    <name>
                    <type>one of the REST VERBS: GET POST PUT HEAD CONNECTION OPTIONS TRACE PATCH DELETE</type>
                    <description>a description for the endpoint</description>
                    <path>the path for the endpoint such as /example/{id}</path>
                </endpoint>
                ... repeat for all related endpoints in a group ie /user GET PUT
            </endoint_group>
            ... repeat endpoints and groups until ALL requirements are satisfied 
        </endpoints>
    </module>
    ... repeat for each module
</modules>\n
Human: {system_requirements}

Assistant:  <modules>
    <module>
        <module_name>"""
